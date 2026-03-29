"""
匹配会话相关 Pydantic Schema

QuestionsResponse  — GET  /sessions/{id}/questions 响应
SubmitRequest      — POST /sessions/{id}/submit 请求体
SubmitResponse     — POST /sessions/{id}/submit 响应体（含 Top3 候选人）
"""

import uuid
from pydantic import BaseModel


class SessionQuestionOption(BaseModel):
    option_id: str
    text: str


class SessionQuestion(BaseModel):
    id: str
    dimension: str
    text: str
    options: list[SessionQuestionOption]


class QuestionsResponse(BaseModel):
    session_id: str
    questions: list[SessionQuestion]
    total_count: int = 0
    ready_count: int = 0
    is_generating: bool = False


class AnswerItem(BaseModel):
    question_id: str
    option_id: str


class PreAnswerRequest(BaseModel):
    question_id: str
    option_id: str


class SubmitRequest(BaseModel):
    user_id: str
    session_id: str | None = None
    answers: list[AnswerItem]


class RadarDim(BaseModel):
    dimension: str
    user: int       # 当前用户在该维度的分数（0-10）
    candidate: int  # 候选人在该维度的分数（0-10）


class CandidateResult(BaseModel):
    user_id: str
    name: str
    grade: str
    major: str
    match_score: int    # 综合契合度百分比（0-100）
    contact_info: str
    summary: str
    radar: list[RadarDim]


class SubmitResponse(BaseModel):
    session_id: str
    top3: list[CandidateResult]
