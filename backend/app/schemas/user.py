"""
用户相关 Pydantic Schema

UserCreate  — 前端提交的 6 项基础信息（请求体）
UserResponse — 创建成功后返回给前端的数据（响应体）
"""

import uuid
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """前端提交的用户基础信息，对应 OnboardingPage 的表单"""

    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    gender: str = Field(..., description="性别，如 '男' / '女' / '其他'")
    grade: str = Field(..., description="年级，如 '大一' / '大二' / '研一'")
    major: str = Field(..., min_length=1, max_length=100, description="专业")
    team_goal: str = Field(..., min_length=1, max_length=100, description="组队目标，如 '数学建模比赛'")
    want_long_term: bool = Field(..., description="是否想要长期组队")
    gender_preference: str | None = Field(None, max_length=10, description="对搭子的性别要求，如 '男'/'女'/'任意'")
    grade_preference: str | None = Field(None, max_length=20, description="对搭子的年级要求，如 '大二'/'任意'")
    contact_info: str | None = Field(None, max_length=100, description="联系方式（微信/QQ），可选")


class UserResponse(BaseModel):
    """创建用户成功后的响应体"""

    id: uuid.UUID
    name: str
    gender: str
    grade: str
    major: str
    team_goal: str
    want_long_term: bool

    model_config = {"from_attributes": True}


class SessionCreateResponse(BaseModel):
    """创建用户后同步返回的匹配会话信息，前端用此 session_id 进入下一步"""

    user_id: uuid.UUID
    session_id: uuid.UUID
    message: str = "用户信息已提交，请进入下一步"
