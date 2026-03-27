"""
匹配算法服务模块

业务理解（编码前必读）：
    本模块是 FindBud App 的第二个核心亮点。
    在用户完成 AI 动态提问后，系统已为该用户构建出一个多维度画像向量
    （存储在 match_sessions.user_vector 和 user_profiles 表中）。
    本模块负责将该向量与数据库中其他候选用户的向量进行相似度/互补度计算，
    最终严格返回 Top 3 的潜在队友推荐列表，不多不少。
    推荐数量由常量 MAX_RECOMMEND_COUNT = 3 控制，禁止在业务逻辑中硬编码数字 3。
"""

import math
from dataclasses import dataclass, field
from typing import Any

# ========== 常量 ==========

# 固定推荐队友数量，全项目统一以此常量为准
MAX_RECOMMEND_COUNT: int = 3

# 各评判维度在匹配算法中的默认权重（与 evaluation_dimensions 表的 weight 字段对应）
# 实际运行时应从数据库动态读取，此处为回退默认值
DEFAULT_DIMENSION_WEIGHTS: dict[str, float] = {
    "技术能力":   1.50,
    "沟通协作":   1.20,
    "时间投入度": 1.30,
    "创新思维":   1.20,
    "抗压能力":   1.00,
    "领导力":     0.80,
}


# ========== 数据结构定义 ==========

@dataclass
class UserVector:
    """
    用户画像向量，由基础信息 + AI 问答评分结果构建。
    对应数据库中 user_profiles 表的一行 + match_sessions.user_vector 字段。
    """
    # 用户唯一标识
    user_id: str
    # 各评判维度得分，键为维度名称，值为 0.0~10.0 的归一化评分
    dimension_scores: dict[str, float]
    # 用户偏好的比赛类型列表（来自 user_competition_preferences 表）
    preferred_competition_types: list[str] = field(default_factory=list)
    # 用户倾向角色，如 "技术开发"、"项目管理"、"设计"
    preferred_role: str = ""


@dataclass
class MatchCandidate:
    """
    单个候选队友的匹配结果，对应数据库 match_results 表的一行。
    """
    # 候选队友的用户 ID
    candidate_user_id: str
    # 综合匹配度得分（0.0~1.0，越高越匹配）
    match_score: float
    # 各维度的匹配分析明细，最终存入 match_results.match_reasons（JSONB）
    dimension_breakdown: list[dict[str, Any]]
    # 推荐摘要文字，由算法基于维度分析生成
    summary: str


# ========== 向量计算工具函数 ==========

def normalize_scores(dimension_scores: dict[str, float]) -> dict[str, float]:
    """
    将各维度原始得分（0~10）归一化到 0~1 区间。

    参数:
        dimension_scores (dict[str, float]): 原始维度得分字典

    返回:
        dict[str, float]: 归一化后的得分字典
    """
    return {dim: score / 10.0 for dim, score in dimension_scores.items()}


def compute_weighted_cosine_similarity(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
    weights: dict[str, float],
) -> float:
    """
    计算两个用户维度向量之间的加权余弦相似度。

    适用场景：寻找"相似"队友（如技术风格一致的搭档）。

    参数:
        vec_a (dict[str, float]): 用户 A 的归一化维度得分
        vec_b (dict[str, float]): 用户 B 的归一化维度得分
        weights (dict[str, float]): 各维度权重

    返回:
        float: 加权余弦相似度（0.0~1.0）
    """
    # 取两个向量共同拥有的维度
    common_dims = set(vec_a.keys()) & set(vec_b.keys())
    if not common_dims:
        return 0.0

    dot_product: float = 0.0
    norm_a: float = 0.0
    norm_b: float = 0.0

    for dim in common_dims:
        w = weights.get(dim, 1.0)
        a = vec_a[dim] * w
        b = vec_b[dim] * w
        dot_product += a * b
        norm_a += a ** 2
        norm_b += b ** 2

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))


def compute_complementarity_score(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
    weights: dict[str, float],
) -> float:
    """
    计算两个用户之间的加权互补度得分。

    适用场景：寻找"互补"队友（如一人技术强、另一人管理强）。
    互补度定义：某维度上两人得分差距越大，该维度互补性越高。

    参数:
        vec_a (dict[str, float]): 用户 A 的归一化维度得分
        vec_b (dict[str, float]): 用户 B 的归一化维度得分
        weights (dict[str, float]): 各维度权重

    返回:
        float: 加权互补度得分（0.0~1.0）
    """
    common_dims = set(vec_a.keys()) & set(vec_b.keys())
    if not common_dims:
        return 0.0

    total_weight: float = sum(weights.get(dim, 1.0) for dim in common_dims)
    if total_weight == 0.0:
        return 0.0

    # 加权差值绝对值之和，差距越大说明互补性越强
    weighted_diff_sum: float = sum(
        weights.get(dim, 1.0) * abs(vec_a[dim] - vec_b[dim])
        for dim in common_dims
    )

    return weighted_diff_sum / total_weight


def compute_combined_match_score(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
    weights: dict[str, float],
    similarity_weight: float = 0.5,
    complementarity_weight: float = 0.5,
) -> float:
    """
    综合相似度和互补度，计算最终匹配得分。

    参数:
        vec_a (dict[str, float]): 用户 A 的归一化维度得分
        vec_b (dict[str, float]): 用户 B 的归一化维度得分
        weights (dict[str, float]): 各维度权重
        similarity_weight (float): 相似度在最终得分中的占比（默认 0.5）
        complementarity_weight (float): 互补度在最终得分中的占比（默认 0.5）

    返回:
        float: 综合匹配得分（0.0~1.0）
    """
    similarity = compute_weighted_cosine_similarity(vec_a, vec_b, weights)
    complementarity = compute_complementarity_score(vec_a, vec_b, weights)

    return similarity * similarity_weight + complementarity * complementarity_weight


# ========== 维度分析工具函数 ==========

def build_dimension_breakdown(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
    weights: dict[str, float],
) -> list[dict[str, Any]]:
    """
    生成两个用户各维度的匹配分析明细，用于填充 match_results.match_reasons 字段。

    参数:
        vec_a (dict[str, float]): 当前用户的归一化维度得分
        vec_b (dict[str, float]): 候选队友的归一化维度得分
        weights (dict[str, float]): 各维度权重

    返回:
        list[dict]: 各维度分析列表，每项含 dimension、score、comment
    """
    breakdown = []
    common_dims = set(vec_a.keys()) & set(vec_b.keys())

    for dim in sorted(common_dims, key=lambda d: weights.get(d, 1.0), reverse=True):
        score_a = vec_a[dim]
        score_b = vec_b[dim]
        diff = abs(score_a - score_b)

        # 相似度分量（差距越小，相似度越高）
        similarity_component = 1.0 - diff

        # 根据差距生成文字描述
        if diff < 0.15:
            comment = f"{dim}高度一致"
        elif diff < 0.35:
            comment = f"{dim}较为接近，有共同语言"
        else:
            comment = f"{dim}形成互补，优势互补效果佳"

        breakdown.append({
            "dimension": dim,
            "score": round(similarity_component, 4),
            "comment": comment,
        })

    return breakdown


def generate_match_summary(breakdown: list[dict[str, Any]]) -> str:
    """
    根据维度分析明细，生成简短的推荐摘要文字。

    参数:
        breakdown (list[dict]): build_dimension_breakdown 的返回结果

    返回:
        str: 推荐摘要字符串
    """
    # 取得分最高的前 3 个维度作为摘要亮点
    top_dims = sorted(breakdown, key=lambda x: x["score"], reverse=True)[:3]
    highlights = "、".join([item["comment"] for item in top_dims])
    return highlights if highlights else "综合匹配度较高"


# ========== 核心匹配接口 ==========

def find_top_matches(
    current_user: UserVector,
    all_candidates: list[UserVector],
    dimension_weights: dict[str, float] | None = None,
) -> list[MatchCandidate]:
    """
    核心匹配函数：计算当前用户与所有候选人的匹配度，严格返回 Top 3 推荐列表。

    业务逻辑：
        1. 剔除当前用户自身
        2. 对每位候选人：归一化向量 → 计算综合匹配得分 → 生成维度分析
        3. 按匹配得分降序排列，取前 MAX_RECOMMEND_COUNT（= 3）名
        4. 返回包含匹配得分和分析明细的 MatchCandidate 列表

    参数:
        current_user (UserVector): 发起匹配的当前用户画像向量
        all_candidates (list[UserVector]): 数据库中所有候选用户的画像向量列表
            （应预先按比赛类型筛选，只传入参加同一比赛的候选人）
        dimension_weights (dict[str, float] | None): 各维度权重，
            None 时使用 DEFAULT_DIMENSION_WEIGHTS

    返回:
        list[MatchCandidate]: 严格长度为 MAX_RECOMMEND_COUNT（3）的推荐列表，
            按 match_score 降序排列。若候选人不足 3 人，返回所有候选人。
    """
    # 使用传入的权重，或回退到默认权重
    weights = dimension_weights if dimension_weights is not None else DEFAULT_DIMENSION_WEIGHTS

    # 归一化当前用户的维度得分
    normalized_current = normalize_scores(current_user.dimension_scores)

    scored_candidates: list[MatchCandidate] = []

    for candidate in all_candidates:
        # 排除当前用户自身（不能把自己推荐给自己）
        if candidate.user_id == current_user.user_id:
            continue

        # 归一化候选人的维度得分
        normalized_candidate = normalize_scores(candidate.dimension_scores)

        # 计算综合匹配得分（相似度 + 互补度加权融合）
        match_score: float = compute_combined_match_score(
            vec_a=normalized_current,
            vec_b=normalized_candidate,
            weights=weights,
            similarity_weight=0.5,
            complementarity_weight=0.5,
        )

        # 生成各维度分析明细，用于前端展示匹配原因
        dimension_breakdown = build_dimension_breakdown(
            normalized_current,
            normalized_candidate,
            weights,
        )

        # 生成推荐摘要文字
        summary: str = generate_match_summary(dimension_breakdown)

        scored_candidates.append(MatchCandidate(
            candidate_user_id=candidate.user_id,
            match_score=round(match_score, 4),
            dimension_breakdown=dimension_breakdown,
            summary=summary,
        ))

    # 按综合匹配得分降序排列
    scored_candidates.sort(key=lambda c: c.match_score, reverse=True)

    # 严格截取 Top MAX_RECOMMEND_COUNT 名，固定返回 3 个推荐结果
    return scored_candidates[:MAX_RECOMMEND_COUNT]


def build_user_vector_from_profile(
    user_id: str,
    profile_scores: dict[str, float],
    preferred_competition_types: list[str],
    preferred_role: str,
) -> UserVector:
    """
    从数据库 user_profiles 表的查询结果构建 UserVector 对象。

    参数:
        user_id (str): 用户 UUID
        profile_scores (dict[str, float]): 各维度得分，键为维度名称
            例：{"技术能力": 8.5, "沟通协作": 7.0, ...}
        preferred_competition_types (list[str]): 偏好比赛类型名称列表
        preferred_role (str): 倾向角色

    返回:
        UserVector: 可直接传入 find_top_matches 的用户画像向量对象
    """
    return UserVector(
        user_id=user_id,
        dimension_scores=profile_scores,
        preferred_competition_types=preferred_competition_types,
        preferred_role=preferred_role,
    )
