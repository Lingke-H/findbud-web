"""
匹配算法服务模块（数学建模大赛版）

业务理解（编码前必读）：
    本模块是 FindBud App 的核心匹配引擎（Phase II）。
    用户完成 AI 动态提问后，系统已为该用户构建出分类标签画像（UserProfile）。
    本模块接收用户 A 的画像及已通过固定标签筛选的候选用户集合，
    通过效用函数最大化，严格返回 Top 3 推荐列表，不多不少。

    算法流程（对应 matching_module_prompt.md 的步骤编号）：
        步骤3   ─ 互补指数计算（互斥标签组 → 余弦正交性）
        步骤4   ─ 独立标签预处理与相似度计算（差异越小越好）
        步骤5   ─ 按列 Min-Max 归一化
        步骤6   ─ 权重计算（熵权法客观权重 × α + 主观权重 × (1-α)，α=0.5）
        步骤7   ─ 效用函数（加权和）
        步骤8~9 ─ 初步配对（按效用值排序取 Top MAX_RECOMMEND_COUNT）
        步骤10  ─ 特长多样性检查 + 候选池耗尽容错机制

    推荐数量由 MAX_RECOMMEND_COUNT 控制，禁止在业务逻辑中硬编码数字 3。
    主客观权重融合比例由 OBJECTIVE_WEIGHT_RATIO 控制，主观权重由 SUBJECTIVE_WEIGHTS 指定。
"""

from dataclasses import dataclass

from app.services.match_engine import (
    MAX_RECOMMEND_COUNT,
    OBJECTIVE_WEIGHT_RATIO,
    MatchResult,
    MatchOutput,
    compute_complementarity_index,
    logistic_map,
    normalize_column,
    compute_entropy_weights,
    blend_weights,
)

# 主观权重字典（键名须与指标名完全一致，值无需归一化，程序会自动处理）
# ⚙️ 开发者：如需调整各维度主观权重，只需修改此字典，无需改动计算逻辑
SUBJECTIVE_WEIGHTS: dict[str, float] = {
    "技能互补指数":       0.45,
    "性格互补指数":       0.15,
    "参与比赛场次相似度": 0.10,
    "是否获奖相似度":     0.15,
    "获奖欲望相似度":     0.15,
}


# ========== 数据结构定义 ==========

@dataclass
class UserProfile:
    """
    用户分类标签画像（匹配模块的核心输入单元）。
    包含两组互斥标签（技能向量、性格动能因子）和一组独立标签（绝对实力）。
    所有字段均由 AI 动态提问阶段评分后写入，对应 user_profiles 表。
    """
    # 用户唯一标识（对应数据库 UUID）
    user_id: str

    # ── 互斥标签组1：技能向量（得分范围 0~10，对应 user_profiles 列，组内各项此消彼长）──
    skill_modeling: float    # 建模手
    skill_coding: float      # 编程手
    skill_writing: float     # 论文手

    # ── 互斥标签组2：性格动能因子（得分范围 0~10，对应 user_profiles 列，组内各项此消彼长）──
    personality_leader: float    # 军官（领导者）
    personality_executor: float  # 勇士（执行者）
    personality_supporter: float # 军师（支持者）

    # ── 独立标签：绝对实力（与其他标签无此消彼长关系，字段名与 user_profiles 表列名一致）──
    strength_competition_count: int   # 参与过的比赛场次（非负整数）
    strength_award_count: int         # 获奖次数（非负整数，>0 视为已获奖）
    strength_ambition: float          # 获奖欲望（0~10）

    # ── 附加字段（来自 user_profiles 表，当前算法未使用，预留扩展）──
    strength_major_relevant: float = 0.0  # 专业对口程度（0~10）
    preferred_role: str = ""               # 前置问题结果：建模手/论文手/编程手/无倾向


def _compute_independent_similarities(
    user_a: UserProfile,
    user_b: UserProfile,
) -> dict[str, float]:
    """
    计算所有独立标签在用户 A 与用户 B 之间的相似度（差异越小，得分越高）。

    各标签计算规则：
        参与比赛场次 ─ logistic 映射后取 1 - |A_mapped - B_mapped|
        是否获奖     ─ 布尔值转 0/1，取 1 - |A - B|
        获奖欲望     ─ 0~10 分值，取 1 - |A - B| / 10

    未指明特殊映射的独立标签默认使用恒等映射 y = x。
    """
    # 参与比赛场次（对应 strength_competition_count）：先 logistic 映射，再计算相似度
    mapped_a = logistic_map(float(user_a.strength_competition_count))
    mapped_b = logistic_map(float(user_b.strength_competition_count))
    experience_sim = 1.0 - abs(mapped_a - mapped_b)

    # 是否获奖（对应 strength_award_count）：获奖次数 > 0 视为已获奖，转为 0/1 后计算差异
    award_a = 1.0 if user_a.strength_award_count > 0 else 0.0
    award_b = 1.0 if user_b.strength_award_count > 0 else 0.0
    award_sim = 1.0 - abs(award_a - award_b)

    # 获奖欲望（对应 strength_ambition）：0~10 范围，除以 10 归一化分母
    ambition_sim = 1.0 - abs(user_a.strength_ambition - user_b.strength_ambition) / 10.0

    return {
        "参与比赛场次相似度": experience_sim,
        "是否获奖相似度":     award_sim,
        "获奖欲望相似度":     ambition_sim,
    }


# ========== 特长标签收集（步骤8 辅助函数） ==========

def _get_special_tags(profile: UserProfile) -> dict[str, str]:
    """
    获取用户每一组互斥标签中的「特长标签」（该组内得分最高的子标签名）。

    返回: {互斥标签组名: 特长子标签名}
    例：{"技能向量": "建模手", "性格动能因子": "军师"}
    """
    skill_scores: dict[str, float] = {
        "建模手": profile.skill_modeling,
        "编程手": profile.skill_coding,
        "论文手": profile.skill_writing,
    }
    personality_scores: dict[str, float] = {
        "军官": profile.personality_leader,
        "勇士": profile.personality_executor,
        "军师": profile.personality_supporter,
    }
    return {
        "技能向量":     max(skill_scores,       key=lambda k: skill_scores[k]),
        "性格动能因子": max(personality_scores,  key=lambda k: personality_scores[k]),
    }


# ========== match_reasons 构建辅助（供写入 match_results 表使用） ==========

# 各细粒度指标归属的大维度（对应 match_reasons.dimension_breakdown 中的 dimension 字段）
_INDICATOR_TO_GROUP: dict[str, str] = {
    "技能互补指数":       "技能向量",
    "性格互补指数":       "性格动能因子",
    "参与比赛场次相似度": "绝对实力",
    "是否获奖相似度":     "绝对实力",
    "获奖欲望相似度":     "绝对实力",
}


def _generate_dimension_comment(group: str, score: float) -> str:
    """
    根据大维度名称和得分生成一句人类可读的匹配评语，
    写入 match_reasons.dimension_breakdown[].comment 字段。
    """
    if group == "技能向量":
        if score >= 0.75:
            return "技能正交互补，建模/编程/排版三角分工完整"
        elif score >= 0.5:
            return "技能有一定互补，分工较为明确"
        else:
            return "技能方向相近，分工需进一步协调"
    elif group == "性格动能因子":
        if score >= 0.75:
            return "性格角色互补，协作摩擦小"
        elif score >= 0.5:
            return "性格角色较为均衡，协作较顺畅"
        else:
            return "性格方向相近，需注意角色分配"
    else:
        if score >= 0.75:
            return "比赛经验与目标高度匹配，整体实力均衡"
        elif score >= 0.5:
            return "实力较为接近，有共同参赛基础"
        else:
            return "实力有差异，可互相补充经验"


def _build_match_reasons(
    indicator_names: list[str],
    normalized_scores: list[float],
) -> dict:
    """
    将5个细粒度指标汇总为 match_results.match_reasons 所需的 JSONB 格式。

    输出结构（与 schema.md 中 match_reasons 示例完全对齐）：
        {
            "summary": "...",
            "dimension_breakdown": [
                {"dimension": "技能向量",     "score": 0.90, "comment": "..."},
                {"dimension": "性格动能因子", "score": 0.85, "comment": "..."},
                {"dimension": "绝对实力",     "score": 0.80, "comment": "..."},
            ]
        }
    """
    # 按大维度聚合得分（对应 _INDICATOR_TO_GROUP 的映射关系）
    group_score_lists: dict[str, list[float]] = {}
    for name, score in zip(indicator_names, normalized_scores):
        group = _INDICATOR_TO_GROUP.get(name, name)
        group_score_lists.setdefault(group, []).append(score)

    # 按固定顺序输出大维度（与 schema.md 示例保持一致）
    ordered_groups = ["技能向量", "性格动能因子", "绝对实力"]
    breakdown = []
    for group in ordered_groups:
        scores = group_score_lists.get(group, [])
        if not scores:
            continue
        avg_score = round(sum(scores) / len(scores), 4)
        breakdown.append({
            "dimension": group,
            "score":     avg_score,
            "comment":   _generate_dimension_comment(group, avg_score),
        })

    # summary 由各维度评语拼接而成
    summary = "；".join(item["comment"] for item in breakdown) or "综合匹配度较高"
    return {"summary": summary, "dimension_breakdown": breakdown}


# ========== 子模块6：初步配对 + 子模块7：最终确定 ==========

def find_top_matches(
    user_a: UserProfile,
    candidates: list[UserProfile],
) -> MatchOutput:
    """
    核心匹配函数：输入用户 A 及已通过固定标签筛选的候选集，返回最优 Top 3 推荐。

    完整执行步骤3~10，包括：
        - 互补指数计算（余弦正交性）
        - 独立标签相似度计算（差异越小越好）
        - 按列归一化
        - 熵权法 + 主观权重 1:1 融合
        - 效用函数加权和
        - 特长标签多样性检查（步骤10）
        - 候选池耗尽容错机制

    参数:
        user_a     ─ 发起匹配的用户画像（已完成 AI 动态提问）
        candidates ─ 已通过固定标签筛选的候选用户列表（不应包含 user_a 自身）

    返回:
        MatchOutput：含 Top-MAX_RECOMMEND_COUNT 推荐结果及 diversity_guaranteed 标记
    """
    # 候选池为空时直接返回空结果
    if not candidates:
        return MatchOutput(results=[], diversity_guaranteed=True)

    # 有效指标名列表（顺序与 SUBJECTIVE_WEIGHTS 键顺序一致，后续矩阵列对应此顺序）
    indicator_names: list[str] = list(SUBJECTIVE_WEIGHTS.keys())
    n_indicators: int = len(indicator_names)
    n_candidates: int = len(candidates)

    # ── 步骤3~4：计算每对 (A, B) 的原始指标值 ──
    raw_matrix: list[list[float]] = []
    for b in candidates:
        # 互斥标签组1：技能向量的余弦正交性（互补指数）
        skill_a = [user_a.skill_modeling, user_a.skill_coding, user_a.skill_writing]
        skill_b = [b.skill_modeling,      b.skill_coding,      b.skill_writing]
        comp_skill = compute_complementarity_index(skill_a, skill_b)

        # 互斥标签组2：性格动能因子的余弦正交性（互补指数）
        pers_a = [user_a.personality_leader, user_a.personality_executor, user_a.personality_supporter]
        pers_b = [b.personality_leader,      b.personality_executor,      b.personality_supporter]
        comp_personality = compute_complementarity_index(pers_a, pers_b)

        # 独立标签：差异越小越好
        indep = _compute_independent_similarities(user_a, b)

        raw_matrix.append([
            comp_skill,
            comp_personality,
            indep["参与比赛场次相似度"],
            indep["是否获奖相似度"],
            indep["获奖欲望相似度"],
        ])

    # ── 步骤5：按列（每个指标跨所有候选用户）进行 Min-Max 归一化 ──
    normalized_matrix: list[list[float]] = [
        [0.0] * n_indicators for _ in range(n_candidates)
    ]
    for col in range(n_indicators):
        col_values = [raw_matrix[row][col] for row in range(n_candidates)]
        normalized_col = normalize_column(col_values)
        for row in range(n_candidates):
            normalized_matrix[row][col] = normalized_col[row]

    # ── 步骤6：计算融合权重 ──
    # 客观权重：熵权法
    objective_weights: list[float] = compute_entropy_weights(normalized_matrix)

    # 主观权重：从 SUBJECTIVE_WEIGHTS 按指标顺序提取并归一化
    raw_subj = [SUBJECTIVE_WEIGHTS.get(name, 0.0) for name in indicator_names]
    total_subj = sum(raw_subj)
    subjective_weights: list[float] = (
        [w / total_subj for w in raw_subj]
        if total_subj > 0.0
        else [1.0 / n_indicators] * n_indicators
    )

    # 融合权重（OBJECTIVE_WEIGHT_RATIO 控制主客观比例）
    final_weights: list[float] = blend_weights(
        objective_weights, subjective_weights, OBJECTIVE_WEIGHT_RATIO
    )

    # ── 步骤7：计算效用函数值（加权和）──
    utility_scores: list[float] = [
        sum(final_weights[col] * normalized_matrix[row][col] for col in range(n_indicators))
        for row in range(n_candidates)
    ]

    # 同步收集每位候选用户的特长标签（供步骤10使用）
    special_tags: list[dict[str, str]] = [_get_special_tags(b) for b in candidates]

    # ── 步骤8~9：初步配对，按效用值降序排列，取 Top MAX_RECOMMEND_COUNT ──
    sorted_indices: list[int] = sorted(
        range(n_candidates), key=lambda i: utility_scores[i], reverse=True
    )
    top_indices: list[int] = list(sorted_indices[:MAX_RECOMMEND_COUNT])
    next_ptr: int = MAX_RECOMMEND_COUNT  # 指向排名下一位的游标

    # ── 步骤10：特长标签多样性检查 ──
    # 每个互斥标签组内，若初步配对的三人特长标签全部相同，则触发替换
    diversity_guaranteed: bool = True
    group_names: list[str] = ["技能向量", "性格动能因子"]

    need_recheck: bool = len(top_indices) >= MAX_RECOMMEND_COUNT
    while need_recheck:
        need_recheck = False
        for group in group_names:
            tags = [special_tags[i][group] for i in top_indices]
            # 三人该组特长全部相同，触发替换
            if len(set(tags)) == 1:
                if next_ptr >= n_candidates:
                    # 候选池已耗尽，启动容错机制，不再强制替换
                    diversity_guaranteed = False
                    need_recheck = False
                    break
                # 剔除当前 top 中效用值最低的成员
                worst_idx = min(top_indices, key=lambda i: utility_scores[i])
                top_indices.remove(worst_idx)
                top_indices.append(sorted_indices[next_ptr])
                next_ptr += 1
                need_recheck = True  # 替换后重新检查所有组
                break

    # ── 构建最终返回结果 ──
    results: list[MatchResult] = []
    for idx in top_indices:
        # 取出该候选用户各指标的归一化得分，用于生成 match_reasons JSONB
        indicator_scores: list[float] = [
            normalized_matrix[idx][col] for col in range(n_indicators)
        ]
        results.append(MatchResult(
            recommended_user_id=candidates[idx].user_id,   # 对应 match_results.recommended_user_id
            rank=0,                                          # 暂时填 0，排序后赋正式排名
            match_score=round(utility_scores[idx], 4),      # 对应 match_results.match_score
            match_reasons=_build_match_reasons(             # 对应 match_results.match_reasons（JSONB）
                indicator_names, indicator_scores
            ),
        ))

    # 按效用得分降序排列，赋予最终排名（1 = 最佳）
    results.sort(key=lambda r: r.match_score, reverse=True)
    for rank_num, result in enumerate(results, start=1):
        result.rank = rank_num

    return MatchOutput(results=results, diversity_guaranteed=diversity_guaranteed)
