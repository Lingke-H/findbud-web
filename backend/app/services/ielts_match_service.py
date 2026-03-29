"""
匹配算法服务模块（雅思学习搭子版）

业务理解（编码前必读）：
    本模块是 FindBud App 雅思学习搭子匹配路径的专属服务层。
    结构完全平行于 match_service.py（数学建模版），共享 match_engine.py 的纯数学函数。
    用户完成 AI 动态提问后，系统已将答案写入 ielts_user_profiles 表。
    本模块接收用户 A 的画像及候选集，通过效用函数最大化返回 Top 3 推荐列表。

    算法流程（与 matching_module_prompt.md 步骤编号对应）：
        步骤3   ─ 互补指数计算（互斥标签组 → 余弦正交性）
        步骤4   ─ 独立标签预处理与相似度计算（差异越小越好）
        步骤5   ─ 按列 Min-Max 归一化
        步骤6   ─ 权重计算（熵权法客观权重 × α + 主观权重 × (1-α)，α=0.5）
        步骤7   ─ 效用函数（加权和）
        步骤8~9 ─ 初步配对（按效用值排序取 Top MAX_RECOMMEND_COUNT）
        步骤10  ─ 特长多样性检查 + 候选池耗尽容错机制

    字段名与 ielts_user_profiles 表列名严格对齐，禁止随意更改。
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
    "擅长题型互补指数":   0.35,
    "性格互补指数":       0.20,
    "口语流畅度相似度":   0.10,
    "雅思考试经历相似度": 0.10,
    "愿意培训班相似度":   0.10,
    "每周学习时长相似度": 0.10,
    "目标成绩相似度":     0.05,
}


# ========== 数据结构定义 ==========

@dataclass
class IELTSUserProfile:
    """
    雅思学习搭子分类标签画像（匹配模块的核心输入单元）。
    包含两组互斥标签（擅长题型、性格动能因子）和一组独立标签（学习目标与投入）。
    所有字段均由 AI 动态提问阶段评分后写入，对应 ielts_user_profiles 表。
    字段名与表列名严格一致，可直接从 ORM 对象映射。
    """
    # 用户唯一标识（对应数据库 UUID）
    user_id: str

    # ── 互斥标签组1：擅长题型（得分范围 0~10，组内各项此消彼长）──
    skill_listening: float   # 听力
    skill_reading:   float   # 阅读
    skill_writing:   float   # 写作
    skill_speaking:  float   # 口语

    # ── 互斥标签组2：性格动能因子（得分范围 0~10，组内各项此消彼长）──
    personality_planner:     float   # 计划制定及推动者
    personality_resourcer:   float   # 资源获取者
    personality_coordinator: float   # 协调者

    # ── 独立标签：学习目标与投入（与其他标签无此消彼长关系）──
    strength_fluency:          float   # 日常英语口语顺畅程度（0~10）
    strength_has_ielts_exp:    bool    # 是否有雅思考试经历
    strength_willing_training: bool    # 是否愿意一起参加培训班
    strength_weekly_hours:     int     # 每周可投入共同学习时长（小时，≥0）
    strength_target_score:     float   # 目标成绩期望（0~10，0=随意，10=最高分）

    # ── 附加字段（来自 ielts_user_profiles 表，当前算法未使用，预留扩展）──
    preferred_role: str = ""   # 前置问题结果：听力/阅读/写作/口语/无倾向


# ========== 独立标签相似度计算（步骤4） ==========

def _compute_independent_similarities(
    user_a: IELTSUserProfile,
    user_b: IELTSUserProfile,
) -> dict[str, float]:
    """
    计算所有独立标签在用户 A 与用户 B 之间的相似度（差异越小，得分越高）。

    各标签计算规则：
        口语流畅度       ─ 0~10 分值，取 1 - |A - B| / 10
        雅思考试经历     ─ 布尔值转 0/1，取 1 - |A - B|
        愿意参加培训班   ─ 布尔值转 0/1，取 1 - |A - B|
        每周学习时长     ─ logistic 映射（k=0.3, x0=10）后取 1 - |A_mapped - B_mapped|
        目标成绩期望     ─ 0~10 分值，取 1 - |A - B| / 10
    """
    # 口语流畅度（strength_fluency）：0~10 范围，除以 10 归一化分母
    fluency_sim = 1.0 - abs(user_a.strength_fluency - user_b.strength_fluency) / 10.0

    # 是否有雅思考试经历（strength_has_ielts_exp）：布尔转 0/1 差异
    exp_sim = 1.0 - abs(int(user_a.strength_has_ielts_exp) - int(user_b.strength_has_ielts_exp))

    # 是否愿意一起参加培训班（strength_willing_training）：布尔转 0/1 差异
    training_sim = 1.0 - abs(
        int(user_a.strength_willing_training) - int(user_b.strength_willing_training)
    )

    # 每周可投入学习时长（strength_weekly_hours）：非负整数，logistic 映射压缩（中点≈10小时/周）
    mapped_a = logistic_map(float(user_a.strength_weekly_hours), k=0.3, x0=10.0)
    mapped_b = logistic_map(float(user_b.strength_weekly_hours), k=0.3, x0=10.0)
    hours_sim = 1.0 - abs(mapped_a - mapped_b)

    # 目标成绩期望（strength_target_score）：0~10 范围，除以 10 归一化分母
    score_sim = 1.0 - abs(user_a.strength_target_score - user_b.strength_target_score) / 10.0

    return {
        "口语流畅度相似度":   fluency_sim,
        "雅思考试经历相似度": exp_sim,
        "愿意培训班相似度":   training_sim,
        "每周学习时长相似度": hours_sim,
        "目标成绩相似度":     score_sim,
    }


# ========== 特长标签收集（步骤8 辅助函数） ==========

def _get_special_tags(profile: IELTSUserProfile) -> dict[str, str]:
    """
    获取用户每一组互斥标签中的「特长标签」（该组内得分最高的子标签名）。

    返回: {互斥标签组名: 特长子标签名}
    例：{"擅长题型": "听力", "性格动能因子": "计划者"}
    """
    skill_scores: dict[str, float] = {
        "听力": profile.skill_listening,
        "阅读": profile.skill_reading,
        "写作": profile.skill_writing,
        "口语": profile.skill_speaking,
    }
    personality_scores: dict[str, float] = {
        "计划者": profile.personality_planner,
        "资源者": profile.personality_resourcer,
        "协调者": profile.personality_coordinator,
    }
    return {
        "擅长题型":   max(skill_scores,       key=lambda k: skill_scores[k]),
        "性格动能因子": max(personality_scores, key=lambda k: personality_scores[k]),
    }


# ========== match_reasons 构建辅助（供写入 match_results 表使用） ==========

_INDICATOR_TO_GROUP: dict[str, str] = {
    "擅长题型互补指数":   "擅长题型",
    "性格互补指数":       "性格动能因子",
    "口语流畅度相似度":   "学习目标与投入",
    "雅思考试经历相似度": "学习目标与投入",
    "愿意培训班相似度":   "学习目标与投入",
    "每周学习时长相似度": "学习目标与投入",
    "目标成绩相似度":     "学习目标与投入",
}


def _generate_dimension_comment(group: str, score: float) -> str:
    """
    根据大维度名称和得分生成人类可读的匹配评语，
    写入 match_reasons.dimension_breakdown[].comment 字段。
    """
    if group == "擅长题型":
        if score >= 0.75:
            return "听说读写四项互补，分工天然清晰"
        elif score >= 0.5:
            return "题型能力有一定互补，练习侧重较为均衡"
        else:
            return "擅长方向相近，需主动规划差异化分工"
    elif group == "性格动能因子":
        if score >= 0.75:
            return "角色互补：计划、资源、协调三位一体"
        elif score >= 0.5:
            return "性格角色较为均衡，协作摩擦较小"
        else:
            return "性格方向相近，建议明确各自职责边界"
    else:
        if score >= 0.75:
            return "学习投入与目标高度一致，长期搭档潜力强"
        elif score >= 0.5:
            return "学习节奏与目标较为吻合，合作较顺畅"
        else:
            return "目标期望有差异，建议提前沟通学习计划"


def _build_match_reasons(
    indicator_names: list[str],
    normalized_scores: list[float],
) -> dict:
    """
    将7个细粒度指标汇总为 match_results.match_reasons 所需的 JSONB 格式。

    输出结构（与 schema.md 中 match_reasons 示例完全对齐）：
        {
            "summary": "...",
            "dimension_breakdown": [
                {"dimension": "擅长题型",     "score": 0.85, "comment": "..."},
                {"dimension": "性格动能因子", "score": 0.80, "comment": "..."},
                {"dimension": "学习目标与投入", "score": 0.75, "comment": "..."},
            ]
        }
    """
    group_score_lists: dict[str, list[float]] = {}
    for name, score in zip(indicator_names, normalized_scores):
        group = _INDICATOR_TO_GROUP.get(name, name)
        group_score_lists.setdefault(group, []).append(score)

    ordered_groups = ["擅长题型", "性格动能因子", "学习目标与投入"]
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

    summary = "；".join(item["comment"] for item in breakdown) or "综合匹配度较高"
    return {"summary": summary, "dimension_breakdown": breakdown}


# ========== 核心匹配入口（步骤3~10） ==========

def find_top_matches_ielts(
    user_a: IELTSUserProfile,
    candidates: list[IELTSUserProfile],
) -> MatchOutput:
    """
    雅思学习搭子核心匹配函数：输入用户 A 及候选集，返回最优 Top 3 推荐。

    完整执行步骤3~10，包括：
        - 互补指数计算（余弦正交性）
        - 独立标签相似度计算（差异越小越好）
        - 按列归一化
        - 熵权法 + 主观权重 1:1 融合
        - 效用函数加权和
        - 特长标签多样性检查（步骤10）
        - 候选池耗尽容错机制

    参数:
        user_a     ─ 发起匹配的雅思用户画像
        candidates ─ 已通过固定标签筛选的候选用户列表（不含 user_a 自身）

    返回:
        MatchOutput：含 Top-MAX_RECOMMEND_COUNT 推荐结果及 diversity_guaranteed 标记
    """
    if not candidates:
        return MatchOutput(results=[], diversity_guaranteed=True)

    indicator_names: list[str] = list(SUBJECTIVE_WEIGHTS.keys())
    n_indicators: int = len(indicator_names)
    n_candidates: int = len(candidates)

    # ── 步骤3~4：计算每对 (A, B) 的原始指标值 ──
    raw_matrix: list[list[float]] = []
    for b in candidates:
        # 互斥标签组1：擅长题型余弦正交性（互补指数）
        skill_a = [user_a.skill_listening, user_a.skill_reading, user_a.skill_writing, user_a.skill_speaking]
        skill_b = [b.skill_listening,      b.skill_reading,      b.skill_writing,      b.skill_speaking]
        comp_skill = compute_complementarity_index(skill_a, skill_b)

        # 互斥标签组2：性格动能因子余弦正交性（互补指数）
        pers_a = [user_a.personality_planner, user_a.personality_resourcer, user_a.personality_coordinator]
        pers_b = [b.personality_planner,      b.personality_resourcer,      b.personality_coordinator]
        comp_personality = compute_complementarity_index(pers_a, pers_b)

        # 独立标签：差异越小越好
        indep = _compute_independent_similarities(user_a, b)

        raw_matrix.append([
            comp_skill,
            comp_personality,
            indep["口语流畅度相似度"],
            indep["雅思考试经历相似度"],
            indep["愿意培训班相似度"],
            indep["每周学习时长相似度"],
            indep["目标成绩相似度"],
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
    objective_weights: list[float] = compute_entropy_weights(normalized_matrix)

    raw_subj = [SUBJECTIVE_WEIGHTS.get(name, 0.0) for name in indicator_names]
    total_subj = sum(raw_subj)
    subjective_weights: list[float] = (
        [w / total_subj for w in raw_subj]
        if total_subj > 0.0
        else [1.0 / n_indicators] * n_indicators
    )

    final_weights: list[float] = blend_weights(
        objective_weights, subjective_weights, OBJECTIVE_WEIGHT_RATIO
    )

    # ── 步骤7：计算效用函数值（加权和）──
    utility_scores: list[float] = [
        sum(final_weights[col] * normalized_matrix[row][col] for col in range(n_indicators))
        for row in range(n_candidates)
    ]

    special_tags: list[dict[str, str]] = [_get_special_tags(b) for b in candidates]

    # ── 步骤8~9：初步配对，按效用值降序排列，取 Top MAX_RECOMMEND_COUNT ──
    sorted_indices: list[int] = sorted(
        range(n_candidates), key=lambda i: utility_scores[i], reverse=True
    )
    top_indices: list[int] = list(sorted_indices[:MAX_RECOMMEND_COUNT])
    next_ptr: int = MAX_RECOMMEND_COUNT

    # ── 步骤10：特长标签多样性检查 ──
    diversity_guaranteed: bool = True
    group_names: list[str] = ["擅长题型", "性格动能因子"]

    need_recheck: bool = len(top_indices) >= MAX_RECOMMEND_COUNT
    while need_recheck:
        need_recheck = False
        for group in group_names:
            tags = [special_tags[i][group] for i in top_indices]
            if len(set(tags)) == 1:
                if next_ptr >= n_candidates:
                    diversity_guaranteed = False
                    need_recheck = False
                    break
                worst_idx = min(top_indices, key=lambda i: utility_scores[i])
                top_indices.remove(worst_idx)
                top_indices.append(sorted_indices[next_ptr])
                next_ptr += 1
                need_recheck = True
                break

    # ── 构建最终返回结果 ──
    results: list[MatchResult] = []
    for idx in top_indices:
        indicator_scores: list[float] = [
            normalized_matrix[idx][col] for col in range(n_indicators)
        ]
        results.append(MatchResult(
            recommended_user_id=candidates[idx].user_id,
            rank=0,
            match_score=round(utility_scores[idx], 4),
            match_reasons=_build_match_reasons(indicator_names, indicator_scores),
        ))

    results.sort(key=lambda r: r.match_score, reverse=True)
    for rank_num, result in enumerate(results, start=1):
        result.rank = rank_num

    return MatchOutput(results=results, diversity_guaranteed=diversity_guaranteed)
