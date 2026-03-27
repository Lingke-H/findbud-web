"""
AI 动态提问服务模块

业务理解（编码前必读）：
    本模块是 FindBud App 的核心亮点之一。
    系统不使用固定问题库，而是将"比赛类型 + 系统预设评判维度"注入给大模型，
    由 AI 扮演面试官，为每位用户生成差异化的个性化问题（3~5 轮）。
    用户的每条回答经 AI 评分后，写入 question_answers 表，
    最终汇总为 user_profiles 中的各维度得分，供匹配算法使用。
"""

import os
import json
import uuid
from typing import Any

# ========== 数据结构定义 ==========

class QuestionItem:
    """
    单条 AI 生成问题的数据结构，对应数据库 question_answers 表的一行。
    """
    def __init__(
        self,
        question_id: str,
        session_id: str,
        dimension_name: str,
        round_number: int,
        question_text: str,
    ):
        # 问题唯一标识（UUID）
        self.question_id: str = question_id
        # 所属匹配会话 ID
        self.session_id: str = session_id
        # 对应的评判维度名称（如 "技术能力"）
        self.dimension_name: str = dimension_name
        # 本题在当前会话中的轮次（从 1 开始）
        self.round_number: int = round_number
        # AI 生成的问题正文
        self.question_text: str = question_text


class AnswerScoreResult:
    """
    AI 对用户某条回答的评分结果。
    """
    def __init__(
        self,
        question_id: str,
        ai_score: float,
        ai_score_reasoning: str,
    ):
        # 被评分的问题 ID
        self.question_id: str = question_id
        # AI 评分（0.0 ~ 10.0）
        self.ai_score: float = ai_score
        # AI 给出评分的理由（供调试和透明度）
        self.ai_score_reasoning: str = ai_score_reasoning


# ========== 常量 ==========

# 每次会话 AI 提问的轮次范围
MIN_QUESTION_ROUNDS: int = 3
MAX_QUESTION_ROUNDS: int = 5


# ========== Prompt 模板构建 ==========

def build_question_system_prompt(
    competition_type: str,
    dimensions: list[dict[str, Any]],
) -> str:
    """
    构建发送给大模型的系统提示词（System Prompt）。

    参数:
        competition_type (str): 比赛类型名称，如 "数学建模"、"黑客马拉松"
        dimensions (list[dict]): 评判维度列表，每项包含 {"name": str, "description": str}

    返回:
        str: 完整的系统提示词字符串

    注意:
        - 维度列表来自数据库 evaluation_dimensions 表，不对用户暴露
        - 提示词要求 AI 生成有针对性的、差异化的问题，禁止返回通用问题
    """
    # 将维度列表格式化为易读的文本块，注入给模型作为上下文
    dimensions_text = "\n".join(
        [f"  - {d['name']}：{d['description']}" for d in dimensions]
    )

    system_prompt = f"""你是一位经验丰富的竞赛组队顾问，正在对一位想参加【{competition_type}】的同学进行能力摸底访谈。

你需要根据以下评判维度，向该同学提出 {MIN_QUESTION_ROUNDS}~{MAX_QUESTION_ROUNDS} 个问题：
{dimensions_text}

提问要求：
1. 每次只提出 1 个问题，等待用户回答后再提下一个。
2. 问题必须与【{competition_type}】这个比赛的具体情境结合，不能是泛泛而谈的通用问题。
3. 问题应能自然地引导用户展示其在对应维度上的真实能力与风格。
4. 根据用户的前一条回答，适当调整下一个问题的方向（追问或切换维度）。
5. 禁止直接问出维度名称（如不能问"你的技术能力如何"），要通过具体场景侧面了解。

每次返回严格遵循以下 JSON 格式，不要有额外说明文字：
{{
  "dimension": "<本题对应的评判维度名称>",
  "question": "<问题正文>"
}}"""

    return system_prompt


def build_score_prompt(
    dimension_name: str,
    question_text: str,
    answer_text: str,
) -> str:
    """
    构建对用户某条回答进行评分的 Prompt。

    参数:
        dimension_name (str): 该问题所对应的评判维度名称
        question_text (str): AI 提出的问题原文
        answer_text (str): 用户的回答原文

    返回:
        str: 评分请求的 Prompt 字符串
    """
    score_prompt = f"""请对以下问答进行评分，评估用户在【{dimension_name}】维度上的表现。

问题：{question_text}
用户回答：{answer_text}

评分标准：0~10 分，10 分为最高。
请严格按以下 JSON 格式返回，不要有额外说明：
{{
  "score": <0到10之间的浮点数>,
  "reasoning": "<50字以内的评分理由>"
}}"""

    return score_prompt


# ========== 核心接口 ==========

async def generate_next_question(
    session_id: str,
    competition_type: str,
    dimensions: list[dict[str, Any]],
    conversation_history: list[dict[str, str]],
    current_round: int,
) -> QuestionItem:
    """
    调用 AI API，为当前用户生成下一轮个性化问题。

    业务逻辑：
        1. 根据比赛类型和评判维度构建系统提示词
        2. 将本次会话的历史问答作为上下文传入，实现动态追问
        3. 解析 AI 返回的 JSON，构造 QuestionItem 返回

    参数:
        session_id (str): 当前匹配会话的 UUID
        competition_type (str): 目标比赛类型名称
        dimensions (list[dict]): 系统预设的评判维度列表（含 name 和 description）
        conversation_history (list[dict]): 本会话已有的问答历史，格式为
            [{"role": "assistant", "content": "问题..."}, {"role": "user", "content": "回答..."}]
        current_round (int): 当前轮次（从 1 开始）

    返回:
        QuestionItem: 包含问题正文、维度信息、轮次的数据对象

    异常:
        ValueError: AI 返回格式不符合预期时抛出
        RuntimeError: AI API 调用失败时抛出
    """
    # 从环境变量读取 AI API 配置，禁止硬编码
    api_key: str = os.getenv("AI_API_KEY", "")
    api_base_url: str = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
    model_name: str = os.getenv("AI_MODEL_NAME", "gpt-4o")

    if not api_key:
        raise RuntimeError("AI_API_KEY 未配置，请检查 .env 文件")

    # 构建系统提示词
    system_prompt: str = build_question_system_prompt(competition_type, dimensions)

    # 组装发送给 AI 的完整消息列表（系统提示 + 历史对话）
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        *conversation_history,
    ]

    # TODO: 替换为实际 AI SDK 调用（如 openai.AsyncOpenAI 或 httpx 请求）
    # 示例占位：
    # client = openai.AsyncOpenAI(api_key=api_key, base_url=api_base_url)
    # response = await client.chat.completions.create(
    #     model=model_name,
    #     messages=messages,
    #     response_format={"type": "json_object"},
    #     temperature=0.7,  # 适当随机性，确保不同用户获得不同问题
    # )
    # raw_content: str = response.choices[0].message.content

    # --- 开发阶段占位返回，联调时删除此块 ---
    raw_content: str = json.dumps({
        "dimension": dimensions[current_round % len(dimensions)]["name"],
        "question": f"【占位问题 第{current_round}轮】请描述你在{competition_type}中的相关经历。"
    })
    # ---

    # 解析 AI 返回的 JSON
    try:
        parsed: dict = json.loads(raw_content)
        dimension_name: str = parsed["dimension"]
        question_text: str = parsed["question"]
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"AI 返回格式解析失败：{e}，原始内容：{raw_content}")

    return QuestionItem(
        question_id=str(uuid.uuid4()),
        session_id=session_id,
        dimension_name=dimension_name,
        round_number=current_round,
        question_text=question_text,
    )


async def score_user_answer(
    question_id: str,
    dimension_name: str,
    question_text: str,
    answer_text: str,
) -> AnswerScoreResult:
    """
    调用 AI API，对用户在某一问题上的回答进行维度评分（0~10 分）。

    业务逻辑：
        1. 构建评分 Prompt，包含问题原文、用户回答和评判维度
        2. AI 返回评分数值和评分理由
        3. 结果写入 question_answers 表的 ai_score 和 ai_score_reasoning 字段

    参数:
        question_id (str): 被评分的问题 UUID
        dimension_name (str): 该问题对应的评判维度名称
        question_text (str): AI 提出的问题原文
        answer_text (str): 用户的回答原文

    返回:
        AnswerScoreResult: 包含评分数值和评分理由
    """
    # 从环境变量读取 AI API 配置
    api_key: str = os.getenv("AI_API_KEY", "")
    model_name: str = os.getenv("AI_MODEL_NAME", "gpt-4o")

    if not api_key:
        raise RuntimeError("AI_API_KEY 未配置，请检查 .env 文件")

    # 构建评分提示词
    score_prompt: str = build_score_prompt(dimension_name, question_text, answer_text)

    # TODO: 替换为实际 AI SDK 调用
    # response = await client.chat.completions.create(
    #     model=model_name,
    #     messages=[{"role": "user", "content": score_prompt}],
    #     response_format={"type": "json_object"},
    #     temperature=0.2,  # 评分任务使用低随机性，保持一致性
    # )
    # raw_content: str = response.choices[0].message.content

    # --- 开发阶段占位返回 ---
    raw_content: str = json.dumps({"score": 7.5, "reasoning": "占位评分理由"})
    # ---

    try:
        parsed: dict = json.loads(raw_content)
        ai_score: float = float(parsed["score"])
        reasoning: str = parsed["reasoning"]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"AI 评分结果解析失败：{e}")

    # 确保分数在合法范围内
    ai_score = max(0.0, min(10.0, ai_score))

    return AnswerScoreResult(
        question_id=question_id,
        ai_score=ai_score,
        ai_score_reasoning=reasoning,
    )
