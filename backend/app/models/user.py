"""
用户相关 ORM 模型

users         — 用户基础信息（6 项）
user_profiles — 用户三大向量画像（1:1 与 users）
"""

import uuid
from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """用户基础信息表，存储用户填写的 6 项基础信息"""

    __tablename__ = "users"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 6 项基础信息
    name: Mapped[str] = mapped_column(String(50), nullable=False)               # 姓名
    gender: Mapped[str] = mapped_column(String(10), nullable=False)              # 性别
    grade: Mapped[str] = mapped_column(String(20), nullable=False)               # 年级，如 "大二"
    major: Mapped[str] = mapped_column(String(100), nullable=False)              # 专业
    team_goal: Mapped[str] = mapped_column(String(100), nullable=False)          # 组队目标，如 "数学建模比赛"
    want_long_term: Mapped[bool] = mapped_column(Boolean, nullable=False)        # 是否想要长期组队

    # 固定标签（筛选条件）
    gender_preference: Mapped[str | None] = mapped_column(String(10), nullable=True)   # 对搭子的性别要求，如 "男"/"女"/"任意"
    grade_preference: Mapped[str | None] = mapped_column(String(20), nullable=True)    # 对搭子的年级要求，如 "大二"/"任意"

    # 可选字段
    contact_info: Mapped[str | None] = mapped_column(String(100), nullable=True) # 联系方式，匹配后展示

    # 状态与时间
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )


class UserProfile(Base):
    """
    用户向量画像表（1:1 与 users）

    存储 AI 选择题量化后的三大维度向量，由匹配算法直接读取。
    完成所有 AI 选择题后写入/更新此表。
    """

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True
    )

    # 技能向量（相对实力，0~10）
    skill_modeling: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 数学建模实力
    skill_coding: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 编程实现
    skill_writing: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 论文排版

    # 性格动能因子（0~10）
    personality_leader: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 领导者倾向
    personality_supporter: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 支持者倾向
    personality_executor: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 执行者倾向

    # 绝对实力（独立标签，相同维度上评分相似的用户更可能匹配）
    strength_competition_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )   # 参赛次数
    strength_award_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )   # 获奖次数
    strength_ambition: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 获奖欲望（0~10）
    strength_major_relevant: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )   # 专业对口程度（0~10）

    # 前置问题结果
    preferred_role: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )   # 如 "建模手" / "论文手" / "编程手" / "无倾向"

    # 原始答案备份
    raw_answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # 原始选择题答案

    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("skill_modeling    BETWEEN 0 AND 10", name="ck_skill_modeling"),
        CheckConstraint("skill_coding      BETWEEN 0 AND 10", name="ck_skill_coding"),
        CheckConstraint("skill_writing     BETWEEN 0 AND 10", name="ck_skill_writing"),
        CheckConstraint("personality_leader    BETWEEN 0 AND 10", name="ck_personality_leader"),
        CheckConstraint("personality_supporter BETWEEN 0 AND 10", name="ck_personality_supporter"),
        CheckConstraint("personality_executor  BETWEEN 0 AND 10", name="ck_personality_executor"),
        CheckConstraint("strength_competition_count >= 0", name="ck_strength_competition_count"),
        CheckConstraint("strength_award_count >= 0",       name="ck_strength_award_count"),
        CheckConstraint("strength_ambition BETWEEN 0 AND 10", name="ck_strength_ambition"),
        CheckConstraint("strength_major_relevant  BETWEEN 0 AND 10", name="ck_strength_major_relevant"),
    )
