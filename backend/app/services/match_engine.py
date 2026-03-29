"""
匹配引擎核心工具层（与业务场景无关）

本模块只包含：
    1. 全局共享常量（MAX_RECOMMEND_COUNT、OBJECTIVE_WEIGHT_RATIO）
    2. 通用输出数据结构（MatchResult、MatchOutput）
    3. 纯数学/算法函数（余弦相似度、归一化、熵权法、权重融合等）

所有场景专属逻辑（UserProfile 定义、SUBJECTIVE_WEIGHTS、独立标签相似度计算、
find_top_matches 入口函数）均在各自的服务模块中实现：
    - match_service.py        → 数学建模大赛
    - ielts_match_service.py  → 雅思学习搭子
"""

import math
from dataclasses import dataclass

# ========== 全局共享常量 ==========

# 固定推荐队友数量，全项目统一以此常量为准
MAX_RECOMMEND_COUNT: int = 3

# 主客观权重融合系数（0.0 = 纯主观，1.0 = 纯客观，默认 1:1）
# ⚙️ 开发者：如需调整主客观比例，只需修改此常量，无需改动计算逻辑
OBJECTIVE_WEIGHT_RATIO: float = 0.5


# ========== 通用输出数据结构 ==========

@dataclass
class MatchResult:
    """
    单个候选用户的匹配结果，对应数据库 match_results 表的一行。
    字段名与表列名严格对齐，可直接用于 ORM 写入。
    """
    recommended_user_id: str  # 被推荐候选人 UUID（对应 match_results.recommended_user_id）
    rank: int                 # 推荐排名（1~MAX_RECOMMEND_COUNT，对应 match_results.rank）
    match_score: float        # 综合效用函数值（0~1，对应 match_results.match_score）
    match_reasons: dict       # 三大维度分析，JSONB 格式（对应 match_results.match_reasons）


@dataclass
class MatchOutput:
    """
    find_top_matches 系列函数的最终返回值，包含推荐列表及多样性保证标记。
    """
    results: list[MatchResult]
    # 是否保证了特长标签多样性；候选池不足时为 False，供上层调用者感知
    diversity_guaranteed: bool = True


# ========== 纯数学函数 ==========

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    计算两个向量的标准余弦相似度。
    若任一向量为零向量，返回 0.0（无法比较，视为不相似）。
    """
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a ** 2 for a in vec_a))
    norm_b = math.sqrt(sum(b ** 2 for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_complementarity_index(
    vec_a: list[float],
    vec_b: list[float],
) -> float:
    """
    计算一组互斥标签的互补指数：互补指数 = 1 - cosine_similarity(A, B)。
    两向量越正交（余弦相似度越低），互补性越强，互补指数越高（趋近 1）。
    """
    return 1.0 - cosine_similarity(vec_a, vec_b)


def logistic_map(x: float, k: float = 1.5, x0: float = 2.5) -> float:
    """
    Logistic 函数，将非负整数（如场次、小时数）非线性压缩到 (0, 1) 区间。
    k 控制曲线增长速度，x0 控制中点位置（x=x0 时映射值为 0.5）。
    开发者可根据实际数据分布调整 k 和 x0。
    """
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def normalize_column(values: list[float]) -> list[float]:
    """
    对一列指标值进行 Min-Max 归一化，映射到 [0, 1]。
    若所有值相等（max == min），视为无差异，全部返回 1.0。
    """
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return [1.0] * len(values)
    return [(v - min_v) / (max_v - min_v) for v in values]


def compute_entropy_weights(matrix: list[list[float]]) -> list[float]:
    """
    熵权法计算各指标的客观权重。

    原理：某指标在各候选用户间差异越大（信息熵越低），
    对区分候选人的贡献越大，赋予越高客观权重。

    参数:
        matrix ─ 归一化后的指标矩阵，行=候选用户，列=指标

    返回:
        各指标客观权重列表，总和为 1.0
    """
    n_samples = len(matrix)
    n_indicators = len(matrix[0]) if matrix else 0

    if n_samples <= 1 or n_indicators == 0:
        count = n_indicators if n_indicators > 0 else 1
        return [1.0 / count] * count

    utility_values: list[float] = []
    for col_idx in range(n_indicators):
        col = [matrix[row][col_idx] for row in range(n_samples)]
        col_sum = sum(col)

        if col_sum == 0.0:
            utility_values.append(0.0)
            continue

        p_list = [(v + 1e-9) / (col_sum + 1e-9 * n_samples) for v in col]
        entropy = -sum(p * math.log(p) for p in p_list) / math.log(n_samples)
        utility_values.append(max(0.0, 1.0 - entropy))

    total_utility = sum(utility_values)
    if total_utility == 0.0:
        return [1.0 / n_indicators] * n_indicators

    return [u / total_utility for u in utility_values]


def blend_weights(
    objective_weights: list[float],
    subjective_weights: list[float],
    alpha: float,
) -> list[float]:
    """
    融合客观权重与主观权重：final = alpha × objective + (1 - alpha) × subjective。
    融合后再次归一化，确保总和严格为 1.0。
    """
    blended = [
        alpha * obj + (1.0 - alpha) * subj
        for obj, subj in zip(objective_weights, subjective_weights)
    ]
    total = sum(blended)
    if total == 0.0:
        n = len(blended)
        return [1.0 / n] * n
    return [w / total for w in blended]
