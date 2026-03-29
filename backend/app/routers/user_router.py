"""
用户信息接口

POST /api/v1/users  — 提交 6 项基础信息，创建用户并初始化匹配会话
GET  /api/v1/users/{user_id} — 查询用户基础信息
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserProfile, IELTSUserProfile
from app.models.session import MatchSession
from app.routers.question_router import trigger_question_prewarm
from app.schemas.user import UserCreate, UserResponse, SessionCreateResponse

router = APIRouter(prefix="/users", tags=["用户"])


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="提交用户基础信息",
    description="前端 OnboardingPage 提交 6 项基础信息后调用此接口。"
                "创建 User 记录、空白 UserProfile 记录，以及初始 MatchSession。"
                "返回 user_id 和 session_id，前端后续所有步骤都带上 session_id。",
)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    业务逻辑：
    1. 写入 users 表
    2. 写入空白 user_profiles（向量字段全为 NULL，等待 AI 题完成后填入）
    3. 创建 match_sessions（status = 'questioning'）
    4. 返回 user_id + session_id
    """

    # 写入用户基础信息
    new_user = User(
        name=user_data.name,
        gender=user_data.gender,
        grade=user_data.grade,
        major=user_data.major,
        team_goal=user_data.team_goal,
        want_long_term=user_data.want_long_term,
        gender_preference=user_data.gender_preference,
        grade_preference=user_data.grade_preference,
        contact_info=user_data.contact_info,
    )
    db.add(new_user)
    db.flush()  # 获取 new_user.id，不提交事务

    # 按 team_goal 初始化对应类型的空白向量画像（向量字段全部为 NULL，AI 题完成后更新）
    if user_data.team_goal == "雅思学习搭子":
        new_profile = IELTSUserProfile(user_id=new_user.id)
    else:
        new_profile = UserProfile(user_id=new_user.id)
    db.add(new_profile)

    # 创建匹配会话
    new_session = MatchSession(
        user_id=new_user.id,
        status="questioning",
        question_count=0,
    )
    db.add(new_session)

    db.commit()

    # 预热 AI 出题：用户进入 AI 问题页前后台先生成题目，减少首屏等待
    trigger_question_prewarm(str(new_session.id))

    return SessionCreateResponse(
        user_id=new_user.id,
        session_id=new_session.id,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="查询用户基础信息",
)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """根据 user_id 查询用户基础信息"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 {user_id} 不存在",
        )
    return user
