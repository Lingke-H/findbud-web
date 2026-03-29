"""
匹配会话与 AI 问答路由

GET  /api/v1/sessions/{session_id}/questions  — 获取 AI 问题列表
POST /api/v1/sessions/{session_id}/submit     — 提交所有答案，触发匹配，返回 Top3
"""

import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserProfile
from app.models.session import MatchSession
from app.services import ai_service
from app.services.match_service import UserProfile as MatchProfile, find_top_matches
from app.schemas.session import (
    QuestionsResponse,
    SessionQuestion,
    SessionQuestionOption,
    SubmitRequest,
    SubmitResponse,
    CandidateResult,
    RadarDim,
)

router = APIRouter(prefix="/sessions", tags=["问答与匹配"])


# ── 维度定义（key=UserProfile 字段名，name/description 用于 AI Prompt）────
_DIMS: list[dict] = [
    {"key": "skill_modeling",     "label": "建模", "name": "skill_modeling",     "description": "数学建模与方案设计能力，包括数学思维、建模经验"},
    {"key": "skill_coding",       "label": "编程", "name": "skill_coding",       "description": "编程实现与数据处理能力，包括 Python/MATLAB/代码调试"},
    {"key": "skill_writing",      "label": "写作", "name": "skill_writing",      "description": "论文写作与排版能力，包括文字表达、摘要写作"},
    {"key": "personality_leader", "label": "协作", "name": "personality_leader", "description": "团队协作与领导力，包括主动推进、协调分工"},
    {"key": "strength_ambition",  "label": "动力", "name": "strength_ambition",  "description": "参赛动力与获奖欲望，对比赛结果的重视程度"},
]

# AI Prompt 用的维度子集（只含 name + description）
_AI_DIMS: list[dict] = [{"name": d["name"], "description": d["description"]} for d in _DIMS]

# MVP 固定选择题（与前端 mock 保持一致，可替换为 AI 动态生成）
_MVP_QUESTIONS: list[SessionQuestion] = [
    SessionQuestion(
        id="q_skill_model",
        dimension="skill_modeling",
        text="在数学建模中，面对一道从未见过的赛题，你通常第一步会怎么做？",
        options=[
            SessionQuestionOption(option_id="A", text="快速查阅相关文献，寻找已有模型框架"),
            SessionQuestionOption(option_id="B", text="先画出问题结构图，再讨论建模思路"),
            SessionQuestionOption(option_id="C", text="直接动手写代码，边跑数据边理解题意"),
            SessionQuestionOption(option_id="D", text="等队友讨论出方向再开始分工配合"),
        ],
    ),
    SessionQuestion(
        id="q_skill_code",
        dimension="skill_coding",
        text="当队伍需要对大规模数据做可视化分析时，你最有把握的工具是？",
        options=[
            SessionQuestionOption(option_id="A", text="Python（Pandas + Matplotlib / Seaborn）"),
            SessionQuestionOption(option_id="B", text="MATLAB / R"),
            SessionQuestionOption(option_id="C", text="Excel / WPS 图表功能"),
            SessionQuestionOption(option_id="D", text="我更擅长分析和写作，数据处理由队友负责"),
        ],
    ),
    SessionQuestion(
        id="q_skill_paper",
        dimension="skill_writing",
        text="撰写论文时，你最擅长哪个部分？",
        options=[
            SessionQuestionOption(option_id="A", text="模型建立与公式推导"),
            SessionQuestionOption(option_id="B", text="摘要与整体行文逻辑"),
            SessionQuestionOption(option_id="C", text="图表制作与结果分析"),
            SessionQuestionOption(option_id="D", text="参考文献整理与格式排版"),
        ],
    ),
    SessionQuestion(
        id="q_personality",
        dimension="personality_leader",
        text="团队在方向选择上出现分歧，你通常会？",
        options=[
            SessionQuestionOption(option_id="A", text="主动发表意见，推动大家达成决策"),
            SessionQuestionOption(option_id="B", text="先倾听各方观点，再提出折中方案"),
            SessionQuestionOption(option_id="C", text="跟随多数人意见，专注于执行"),
            SessionQuestionOption(option_id="D", text="根据数据和逻辑分析提出建议"),
        ],
    ),
    SessionQuestion(
        id="q_strength_ambition",
        dimension="strength_ambition",
        text="你参加这次数学建模比赛最主要的目标是？",
        options=[
            SessionQuestionOption(option_id="A", text="冲击国家级奖项，简历加分"),
            SessionQuestionOption(option_id="B", text="提升建模能力，重在学习"),
            SessionQuestionOption(option_id="C", text="认识志同道合的朋友"),
            SessionQuestionOption(option_id="D", text="体验比赛流程，没有特别期待"),
        ],
    ),
]

# 选项 ID → 维度分数（0–10）
_OPTION_SCORES: dict[str, float] = {"A": 9.0, "B": 7.0, "C": 5.0, "D": 3.0}

# Hackathon 保命 Mock 候选人（DB 用户不足 3 人时自动补充）
_MOCK_CANDIDATES: list[dict] = [
    {
        "user_id": "mock-001",
        "name": "张明远",
        "grade": "大三",
        "major": "数学与应用数学",
        "contact_info": "WeChat: zhangy2024",
        "skill_modeling": 9.0, "skill_coding": 5.0, "skill_writing": 7.0,
        "personality_leader": 7.0, "personality_executor": 6.0, "personality_supporter": 4.0,
        "strength_competition_count": 3, "strength_award_count": 1, "strength_ambition": 9.0,
    },
    {
        "user_id": "mock-002",
        "name": "李子晴",
        "grade": "大二",
        "major": "计算机科学与技术",
        "contact_info": "WeChat: lzq_coding",
        "skill_modeling": 6.0, "skill_coding": 10.0, "skill_writing": 4.0,
        "personality_leader": 4.0, "personality_executor": 9.0, "personality_supporter": 5.0,
        "strength_competition_count": 2, "strength_award_count": 0, "strength_ambition": 7.0,
    },
    {
        "user_id": "mock-003",
        "name": "王思远",
        "grade": "大四",
        "major": "统计学",
        "contact_info": "email: wsy@example.com",
        "skill_modeling": 7.0, "skill_coding": 6.0, "skill_writing": 9.0,
        "personality_leader": 5.0, "personality_executor": 5.0, "personality_supporter": 9.0,
        "strength_competition_count": 5, "strength_award_count": 2, "strength_ambition": 7.0,
    },
]

# question_id → dimension 快速查找
_Q_DIM_MAP: dict[str, str] = {q.id: q.dimension for q in _MVP_QUESTIONS}


# ── 路由 ─────────────────────────────────────────────────────

@router.get(
    "/{session_id}/questions",
    response_model=QuestionsResponse,
    summary="获取 AI 问题列表",
    description="调用 AI 动态生成选择题；AI 不可用时降级为 MVP 固定题目。",
)
async def get_questions(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """优先调用 AI 生成差异化题目，失败时回退到 MVP 本地题目。"""
    try:
        raw_questions = await asyncio.wait_for(
            ai_service.generate_batch_questions(
                competition_type="数学建模",
                dimensions=_AI_DIMS[:3],  # 只生成 3 题，减少 token 消耗加快响应
            ),
            timeout=40.0,  # DeepSeek 可能较慢，给同 40s
        )
        questions = [
            SessionQuestion(
                id=q.get("id", f"q_{i+1}"),
                dimension=q.get("dimension", _DIMS[i % len(_DIMS)]["key"]),
                text=q.get("text", ""),
                options=[
                    SessionQuestionOption(
                        option_id=opt.get("option_id", "A"),
                        text=opt.get("text", ""),
                    )
                    for opt in q.get("options", [])
                ],
            )
            for i, q in enumerate(raw_questions)
        ]
        if questions:
            return QuestionsResponse(session_id=str(session_id), questions=questions)
    except asyncio.TimeoutError:
        print("[AI] generate_batch_questions timed out (20s), using MVP fallback")
    except Exception as e:
        print(f"[AI] generate_batch_questions failed, using MVP fallback: {e}")

    return QuestionsResponse(
        session_id=str(session_id),
        questions=_MVP_QUESTIONS,
    )


@router.post(
    "/{session_id}/submit",
    response_model=SubmitResponse,
    summary="提交所有答案，触发匹配，返回 Top3",
)
def submit_answers(
    session_id: uuid.UUID,
    body: SubmitRequest,
    db: Session = Depends(get_db),
):
    """
    业务逻辑：
    1. 将每道题的 option_id 映射为维度分数
    2. 更新 user_profiles（若 user_id 有效）
    3. 从 DB 查询其他用户画像，不足 3 人时补充 Mock 候选人
    4. 运行匹配算法，生成雷达图数据
    5. 返回 Top3 + session_id
    """

    # ── 1. 构建当前用户维度分数 ──
    user_dim_scores: dict[str, float] = {d["key"]: 5.0 for d in _DIMS}
    for ans in body.answers:
        dim = _Q_DIM_MAP.get(ans.question_id)
        if dim and ans.option_id in _OPTION_SCORES:
            user_dim_scores[dim] = _OPTION_SCORES[ans.option_id]

    # ── 2. 写入 UserProfile ──
    user_uuid: uuid.UUID | None = None
    try:
        user_uuid = uuid.UUID(body.user_id)
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
        if profile:
            for field_name, score in user_dim_scores.items():
                if hasattr(profile, field_name):
                    setattr(profile, field_name, score)
            db.commit()
    except Exception:
        pass  # Mock user_id（非 UUID）时跳过 DB 写入

    # ── 3. 更新 session 状态 ──
    session = db.query(MatchSession).filter(MatchSession.id == session_id).first()
    if session:
        session.status = "matching"
        try:
            db.commit()
        except Exception:
            db.rollback()

    # ── 4. 查询其他用户画像 ──
    db_candidate_profiles: list[MatchProfile] = []
    db_candidate_info: dict[str, dict] = {}

    try:
        query = (
            db.query(User, UserProfile)
            .join(UserProfile, User.id == UserProfile.user_id)
        )
        if user_uuid:
            query = query.filter(User.id != user_uuid)

        for user, profile in query.all():
            uid = str(user.id)
            db_candidate_profiles.append(MatchProfile(
                user_id=uid,
                skill_modeling=float(profile.skill_modeling or 5.0),
                skill_coding=float(profile.skill_coding or 5.0),
                skill_writing=float(profile.skill_writing or 5.0),
                personality_leader=float(profile.personality_leader or 5.0),
                personality_executor=float(profile.personality_executor or 5.0),
                personality_supporter=float(profile.personality_supporter or 5.0),
                strength_competition_count=int(profile.strength_competition_count or 0),
                strength_award_count=int(profile.strength_award_count or 0),
                strength_ambition=float(profile.strength_ambition or 5.0),
            ))
            db_candidate_info[uid] = {
                "name": user.name, "grade": user.grade,
                "major": user.major,
                "contact_info": user.contact_info or "请通过平台联系",
            }
    except Exception:
        pass

    # ── 5. 补充 Mock 候选人（不足 3 个时） ──
    all_profiles = list(db_candidate_profiles)
    all_info = dict(db_candidate_info)

    for mock in _MOCK_CANDIDATES:
        if len(all_profiles) >= 3:
            break
        all_profiles.append(MatchProfile(
            user_id=mock["user_id"],
            skill_modeling=mock["skill_modeling"],
            skill_coding=mock["skill_coding"],
            skill_writing=mock["skill_writing"],
            personality_leader=mock["personality_leader"],
            personality_executor=mock["personality_executor"],
            personality_supporter=mock["personality_supporter"],
            strength_competition_count=mock["strength_competition_count"],
            strength_award_count=mock["strength_award_count"],
            strength_ambition=mock["strength_ambition"],
        ))
        all_info[mock["user_id"]] = {
            "name": mock["name"], "grade": mock["grade"],
            "major": mock["major"], "contact_info": mock["contact_info"],
        }

    # ── 6. 运行匹配算法 ──
    current_profile = MatchProfile(
        user_id=body.user_id,
        skill_modeling=user_dim_scores.get("skill_modeling", 5.0),
        skill_coding=user_dim_scores.get("skill_coding", 5.0),
        skill_writing=user_dim_scores.get("skill_writing", 5.0),
        personality_leader=user_dim_scores.get("personality_leader", 5.0),
        personality_executor=5.0,
        personality_supporter=5.0,
        strength_competition_count=0,
        strength_award_count=0,
        strength_ambition=user_dim_scores.get("strength_ambition", 5.0),
    )
    match_output = find_top_matches(user_a=current_profile, candidates=all_profiles)

    # ── 7. 组装响应（含雷达图） ──
    dim_labels = {d["key"]: d["label"] for d in _DIMS}
    result_candidates: list[CandidateResult] = []

    for match in match_output.results:
        info = all_info.get(match.recommended_user_id, {})
        # 从候选人 MatchProfile 取维度分数用于雷达图
        cand_prof = next((p for p in all_profiles if p.user_id == match.recommended_user_id), None)
        cand_dim = {
            "skill_modeling":     cand_prof.skill_modeling     if cand_prof else 5.0,
            "skill_coding":       cand_prof.skill_coding       if cand_prof else 5.0,
            "skill_writing":      cand_prof.skill_writing      if cand_prof else 5.0,
            "personality_leader": cand_prof.personality_leader if cand_prof else 5.0,
            "strength_ambition":  cand_prof.strength_ambition  if cand_prof else 5.0,
        }
        radar = [
            RadarDim(
                dimension=dim_labels.get(dim_key, dim_key),
                user=int(round(user_dim_scores.get(dim_key, 5.0))),
                candidate=int(round(cand_dim.get(dim_key, 5.0))),
            )
            for dim_key in user_dim_scores
        ]
        summary = match.match_reasons.get("summary", "综合匹配度较高")

        result_candidates.append(CandidateResult(
            user_id=match.recommended_user_id,
            name=info.get("name", "候选人"),
            grade=info.get("grade", "-"),
            major=info.get("major", "-"),
            match_score=int(round(match.match_score * 100)),
            contact_info=info.get("contact_info", "请通过平台联系"),
            summary=summary,
            radar=radar,
        ))

    # ── 8. 标记 session 完成 ──
    if session:
        session.status = "completed"
        try:
            db.commit()
        except Exception:
            db.rollback()

    return SubmitResponse(session_id=str(session_id), top3=result_candidates)
