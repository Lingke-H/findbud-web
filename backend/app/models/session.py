"""
匹配会话相关 ORM 模型

match_sessions  — 匹配会话（用户每次发起匹配的生命周期）
question_answers — 选择题记录（前置问题 + AI 向量收集题）
match_results   — 推荐结果（固定 3 条）
"""

import uuid
from sqlalchemy import Boolean, CheckConstraint, Numeric, SmallInteger, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class MatchSession(Base):
    """
    匹配会话表

    用户每次发起一次匹配流程就创建一条记录。
    状态流转：questioning（选择题填写中）→ matching（算法运行中）→ completed（已完成）
    """

    __tablename__ = "match_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )   # FK → users.id

    # 状态流转
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="questioning"
    )   # questioning / matching / completed

    question_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
    )   # 已完成的题目数

    # 最终向量（完成所有题目后写入，供匹配算法使用）
    user_vector: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )   # 匹配完成时间

    __table_args__ = (
        CheckConstraint(
            "status IN ('questioning', 'matching', 'completed')",
            name="ck_match_sessions_status",
        ),
    )


class QuestionAnswer(Base):
    """
    选择题记录表

    存储每次会话中所有选择题（前置问题 + AI 向量收集题）及用户的选择答案。
    phase = 'pre'：机动前置问题（1-2 题，根据组队目标分流）
    phase = 'ai' ：AI 生成的向量量化选择题
    """

    __tablename__ = "question_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )   # FK → match_sessions.id

    # 题目阶段
    phase: Mapped[str] = mapped_column(String(10), nullable=False)  # pre / ai

    round_number: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )   # 题目序号（从 1 开始）

    question_text: Mapped[str] = mapped_column(Text, nullable=False)  # 题目正文

    # 选项列表，格式：[{"label": "A", "text": "建模手"}, ...]
    options: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # 用户答案
    selected_option: Mapped[str | None] = mapped_column(
        String(5), nullable=True
    )   # 用户选择的选项标签，如 "A"

    # AI 阶段专用：对应的向量维度名称
    dimension: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )   # 如 "skill_modeling" / "personality_leader" / "strength_ambition"

    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    answered_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )   # 用户完成作答的时间

    __table_args__ = (
        CheckConstraint("phase IN ('pre', 'ai')", name="ck_question_answers_phase"),
    )


class MatchResult(Base):
    """
    匹配推荐结果表

    算法运行后写入，固定 3 条（rank 1/2/3）。
    由后端常量 MAX_RECOMMEND_COUNT = 3 控制，禁止硬编码数字 3。
    """

    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )   # FK → match_sessions.id

    recommended_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )   # FK → users.id（被推荐的候选人）

    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 推荐排名：1 / 2 / 3

    match_score: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False
    )   # 效用函数计算的综合匹配度（0.0000~1.0000）

    # 匹配维度说明，格式示例：
    # {"summary": "技能互补，性格一致", "dimension_breakdown": [...]}
    match_reasons: Mapped[dict] = mapped_column(JSONB, nullable=False)

    is_viewed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )   # 用户是否已查看该推荐

    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("rank IN (1, 2, 3)", name="ck_match_results_rank"),
        CheckConstraint("match_score BETWEEN 0 AND 1", name="ck_match_results_score"),
    )
