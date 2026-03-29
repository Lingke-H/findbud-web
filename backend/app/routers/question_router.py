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
from app.models.user import User, UserProfile, IELTSUserProfile as IELTSOrmProfile
from app.models.session import MatchSession
from app.services import ai_service
from app.services.match_service import UserProfile as MatchProfile, find_top_matches
from app.services.ielts_match_service import IELTSUserProfile as IELTSMatchProfile, find_top_matches_ielts
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


# ── 数学建模大赛维度定义 ────
_MATH_DIMS: list[dict] = [
    {"key": "skill_modeling",     "label": "建模", "name": "skill_modeling",     "description": "数学建模与方案设计能力，包括数学思维、建模经验"},
    {"key": "skill_coding",       "label": "编程", "name": "skill_coding",       "description": "编程实现与数据处理能力，包括 Python/MATLAB/代码调试"},
    {"key": "skill_writing",      "label": "写作", "name": "skill_writing",      "description": "论文写作与排版能力，包括文字表达、摘要写作"},
    {"key": "personality_leader", "label": "协作", "name": "personality_leader", "description": "团队协作与领导力，包括主动推进、协调分工"},
    {"key": "strength_ambition",  "label": "动力", "name": "strength_ambition",  "description": "参赛动力与获奖欲望，对比赛结果的重视程度"},
]

_MATH_AI_DIMS: list[dict] = [{"name": d["name"], "description": d["description"]} for d in _MATH_DIMS]

_MATH_MVP_QUESTIONS: list[SessionQuestion] = [
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

_MATH_OPTION_SCORES: dict[str, float] = {"A": 9.0, "B": 7.0, "C": 5.0, "D": 3.0}

_MATH_MOCK_CANDIDATES: list[dict] = [
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

_MATH_Q_DIM_MAP: dict[str, str] = {q.id: q.dimension for q in _MATH_MVP_QUESTIONS}


# ═══════════════ 雅思学习搭子：维度 / 题目 / Mock ═══════════════

_IELTS_DIMS: list[dict] = [
    {"key": "skill_listening",       "label": "听力", "name": "skill_listening",       "description": "雅思听力模块的理解与应试能力"},
    {"key": "skill_reading",         "label": "阅读", "name": "skill_reading",         "description": "雅思阅读模块的速读与精读能力"},
    {"key": "skill_writing",         "label": "写作", "name": "skill_writing",         "description": "雅思写作模块的表达与论述能力"},
    {"key": "skill_speaking",        "label": "口语", "name": "skill_speaking",        "description": "雅思口语模块的流利度与准确度"},
    {"key": "strength_target_score", "label": "目标", "name": "strength_target_score", "description": "目标雅思成绩期望与备考动力"},
]
_IELTS_AI_DIMS: list[dict] = [{"name": d["name"], "description": d["description"]} for d in _IELTS_DIMS]

_IELTS_OPTION_SCORES: dict[str, float] = {"A": 9.0, "B": 7.0, "C": 5.0, "D": 3.0}

_IELTS_MVP_QUESTIONS: list[SessionQuestion] = [
    SessionQuestion(
        id="q_ielts_skill",
        dimension="skill_listening",
        text="在雅思四项技能中，你目前最擅长哪一项？",
        options=[
            SessionQuestionOption(option_id="A", text="听力（Listening）"),
            SessionQuestionOption(option_id="B", text="阅读（Reading）"),
            SessionQuestionOption(option_id="C", text="写作（Writing）"),
            SessionQuestionOption(option_id="D", text="口语（Speaking）"),
        ],
    ),
    SessionQuestion(
        id="q_ielts_personality",
        dimension="personality_planner",
        text="在学习小组中，你通常扮演什么角色？",
        options=[
            SessionQuestionOption(option_id="A", text="计划者：制定学习计划并推动大家执行"),
            SessionQuestionOption(option_id="B", text="资源者：广泛搜集学习资料和方法分享给组员"),
            SessionQuestionOption(option_id="C", text="协调者：协调组员关系，保持团队氛围融洽"),
            SessionQuestionOption(option_id="D", text="执行者：按计划踏实完成自己的学习任务"),
        ],
    ),
    SessionQuestion(
        id="q_ielts_fluency",
        dimension="strength_fluency",
        text="你在日常生活中用英语交流的顺畅程度如何？",
        options=[
            SessionQuestionOption(option_id="A", text="非常流利，能够自如地表达复杂观点"),
            SessionQuestionOption(option_id="B", text="比较流利，偶尔需要组织语言"),
            SessionQuestionOption(option_id="C", text="基本能交流，但词汇和语法有明显局限"),
            SessionQuestionOption(option_id="D", text="比较困难，需要大量时间思考才能开口"),
        ],
    ),
    SessionQuestion(
        id="q_ielts_commitment",
        dimension="strength_weekly_hours",
        text="你每周能投入多少时间与搭子共同学习雅思？",
        options=[
            SessionQuestionOption(option_id="A", text="15 小时以上（高强度冲刺备考）"),
            SessionQuestionOption(option_id="B", text="8~14 小时（稳定推进型）"),
            SessionQuestionOption(option_id="C", text="3~7 小时（利用碎片时间）"),
            SessionQuestionOption(option_id="D", text="1~2 小时（以交流为主）"),
        ],
    ),
    SessionQuestion(
        id="q_ielts_target",
        dimension="strength_target_score",
        text="你备考雅思的目标分数是？",
        options=[
            SessionQuestionOption(option_id="A", text="7.5 分及以上（高分目标）"),
            SessionQuestionOption(option_id="B", text="7.0 分（主流院校要求）"),
            SessionQuestionOption(option_id="C", text="6.5 分（达标优先）"),
            SessionQuestionOption(option_id="D", text="6.0 或以下（初次尝试）"),
        ],
    ),
]

_IELTS_SKILL_OPTION_FIELDS: dict[str, dict] = {
    "A": {"skill_listening": 9.0, "skill_reading": 3.0, "skill_writing": 3.0, "skill_speaking": 3.0},
    "B": {"skill_listening": 3.0, "skill_reading": 9.0, "skill_writing": 3.0, "skill_speaking": 3.0},
    "C": {"skill_listening": 3.0, "skill_reading": 3.0, "skill_writing": 9.0, "skill_speaking": 3.0},
    "D": {"skill_listening": 3.0, "skill_reading": 3.0, "skill_writing": 3.0, "skill_speaking": 9.0},
}
_IELTS_PERSONALITY_OPTION_FIELDS: dict[str, dict] = {
    "A": {"personality_planner": 9.0, "personality_resourcer": 3.0, "personality_coordinator": 3.0},
    "B": {"personality_planner": 3.0, "personality_resourcer": 9.0, "personality_coordinator": 3.0},
    "C": {"personality_planner": 3.0, "personality_resourcer": 3.0, "personality_coordinator": 9.0},
    "D": {"personality_planner": 5.0, "personality_resourcer": 5.0, "personality_coordinator": 5.0},
}
_IELTS_COMMITMENT_OPTION_HOURS: dict[str, int] = {"A": 18, "B": 10, "C": 5, "D": 1}

_IELTS_Q_DIM_MAP: dict[str, str] = {q.id: q.dimension for q in _IELTS_MVP_QUESTIONS}

_IELTS_MOCK_CANDIDATES: list[dict] = [
    {
        "user_id": "ielts-mock-001", "name": "陈语桐", "grade": "大三", "major": "英语",
        "contact_info": "WeChat: chenyutong_ielts",
        "skill_listening": 9.0, "skill_reading": 6.0, "skill_writing": 5.0, "skill_speaking": 4.0,
        "personality_planner": 8.0, "personality_resourcer": 4.0, "personality_coordinator": 5.0,
        "strength_fluency": 8.0, "strength_has_ielts_exp": True, "strength_willing_training": True,
        "strength_weekly_hours": 12, "strength_target_score": 8.0,
    },
    {
        "user_id": "ielts-mock-002", "name": "刘一鸣", "grade": "大二", "major": "国际贸易",
        "contact_info": "WeChat: liuym_study",
        "skill_listening": 4.0, "skill_reading": 8.0, "skill_writing": 7.0, "skill_speaking": 4.0,
        "personality_planner": 4.0, "personality_resourcer": 9.0, "personality_coordinator": 5.0,
        "strength_fluency": 6.0, "strength_has_ielts_exp": False, "strength_willing_training": True,
        "strength_weekly_hours": 8, "strength_target_score": 7.0,
    },
    {
        "user_id": "ielts-mock-003", "name": "吴晓岚", "grade": "大四", "major": "教育学",
        "contact_info": "email: wuxiaolan@example.com",
        "skill_listening": 5.0, "skill_reading": 5.0, "skill_writing": 4.0, "skill_speaking": 9.0,
        "personality_planner": 4.0, "personality_resourcer": 4.0, "personality_coordinator": 9.0,
        "strength_fluency": 9.0, "strength_has_ielts_exp": True, "strength_willing_training": False,
        "strength_weekly_hours": 6, "strength_target_score": 7.5,
    },
]


# ═══════════════ 工具函数 ═══════════════

def _get_team_goal(session_id: uuid.UUID, db: Session) -> str:
    """通过 session_id 反查当前用户的 team_goal，默认返回 '数学建模大赛'。"""
    try:
        session = db.query(MatchSession).filter(MatchSession.id == session_id).first()
        if not session:
            return "数学建模大赛"
        user = db.query(User).filter(User.id == session.user_id).first()
        return user.team_goal if user and user.team_goal else "数学建模大赛"
    except Exception:
        return "数学建模大赛"


# ── 路由 ─────────────────────────────────────────────────────

@router.get(
    "/{session_id}/questions",
    response_model=QuestionsResponse,
    summary="获取 AI 问题列表",
    description="调用 AI 动态生成选择题；AI 不可用时降级为 MVP 固定题目。",
)
async def get_questions(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """优先调用 AI 生成差异化题目，失败时回退到 MVP 本地题目。"""
    team_goal = _get_team_goal(session_id, db)
    if team_goal == "雅思学习搭子":
        ai_dims = _IELTS_AI_DIMS[:3]
        comp_type = "雅思"
        fallback_questions = _IELTS_MVP_QUESTIONS
        dims = _IELTS_DIMS
    else:
        ai_dims = _MATH_AI_DIMS[:3]
        comp_type = "数学建模"
        fallback_questions = _MATH_MVP_QUESTIONS
        dims = _MATH_DIMS

    try:
        raw_questions = await asyncio.wait_for(
            ai_service.generate_batch_questions(
                competition_type=comp_type,
                dimensions=ai_dims,
            ),
            timeout=40.0,
        )
        questions = [
            SessionQuestion(
                id=q.get("id", f"q_{i+1}"),
                dimension=q.get("dimension", dims[i % len(dims)]["key"]),
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
        print(f"[AI] generate_batch_questions timed out, using MVP fallback ({team_goal})")
    except Exception as e:
        print(f"[AI] generate_batch_questions failed, using MVP fallback: {e}")

    return QuestionsResponse(session_id=str(session_id), questions=fallback_questions)


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
    """按 team_goal 分流至数学建模或雅思匹配服务。"""
    team_goal = _get_team_goal(session_id, db)
    if team_goal == "雅思学习搭子":
        return _submit_ielts(session_id, body, db)
    return _submit_math(session_id, body, db)


# ─── 数学建模大赛匹配逻辑 ───

def _submit_math(session_id: uuid.UUID, body: SubmitRequest, db: Session) -> SubmitResponse:
    # ── 1. 构建维度分数 ──
    user_dim_scores: dict[str, float] = {d["key"]: 5.0 for d in _MATH_DIMS}
    for ans in body.answers:
        dim = _MATH_Q_DIM_MAP.get(ans.question_id)
        if dim and ans.option_id in _MATH_OPTION_SCORES:
            user_dim_scores[dim] = _MATH_OPTION_SCORES[ans.option_id]

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
        pass

    # ── 3. 更新 session 状态 ──
    session = db.query(MatchSession).filter(MatchSession.id == session_id).first()
    if session:
        session.status = "matching"
        try:
            db.commit()
        except Exception:
            db.rollback()

    # ── 4. 查询候选人 ──
    db_candidate_profiles: list[MatchProfile] = []
    db_candidate_info: dict[str, dict] = {}
    try:
        query = db.query(User, UserProfile).join(UserProfile, User.id == UserProfile.user_id)
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

    # ── 5. 补充 Mock 候选人 ──
    all_profiles = list(db_candidate_profiles)
    all_info = dict(db_candidate_info)
    for mock in _MATH_MOCK_CANDIDATES:
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

    # ── 7. 组装响应（含雷达图）──
    dim_labels = {d["key"]: d["label"] for d in _MATH_DIMS}
    result_candidates: list[CandidateResult] = []
    for match in match_output.results:
        info = all_info.get(match.recommended_user_id, {})
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
        result_candidates.append(CandidateResult(
            user_id=match.recommended_user_id,
            name=info.get("name", "候选人"),
            grade=info.get("grade", "-"),
            major=info.get("major", "-"),
            match_score=int(round(match.match_score * 100)),
            contact_info=info.get("contact_info", "请通过平台联系"),
            summary=match.match_reasons.get("summary", "综合匹配度较高"),
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


# ─── 雅思学习搭子匹配逻辑 ───

def _submit_ielts(session_id: uuid.UUID, body: SubmitRequest, db: Session) -> SubmitResponse:
    # ── 1. 构建雅思维度分数 ──
    ielts_scores: dict = {
        "skill_listening": 5.0, "skill_reading": 5.0,
        "skill_writing": 5.0, "skill_speaking": 5.0,
        "personality_planner": 5.0, "personality_resourcer": 5.0, "personality_coordinator": 5.0,
        "strength_fluency": 5.0, "strength_has_ielts_exp": False,
        "strength_willing_training": True, "strength_weekly_hours": 5,
        "strength_target_score": 5.0,
    }
    for ans in body.answers:
        opt = ans.option_id
        if ans.question_id == "q_ielts_skill":
            ielts_scores.update(_IELTS_SKILL_OPTION_FIELDS.get(opt, {}))
        elif ans.question_id == "q_ielts_personality":
            ielts_scores.update(_IELTS_PERSONALITY_OPTION_FIELDS.get(opt, {}))
        elif ans.question_id == "q_ielts_fluency":
            ielts_scores["strength_fluency"] = _IELTS_OPTION_SCORES.get(opt, 5.0)
            ielts_scores["strength_has_ielts_exp"] = _IELTS_OPTION_SCORES.get(opt, 5.0) >= 7.0
        elif ans.question_id == "q_ielts_commitment":
            ielts_scores["strength_weekly_hours"] = _IELTS_COMMITMENT_OPTION_HOURS.get(opt, 5)
            ielts_scores["strength_willing_training"] = opt in ("A", "B")
        elif ans.question_id == "q_ielts_target":
            ielts_scores["strength_target_score"] = _IELTS_OPTION_SCORES.get(opt, 5.0)

    user_dim_scores: dict[str, float] = {
        "skill_listening":       ielts_scores["skill_listening"],
        "skill_reading":         ielts_scores["skill_reading"],
        "skill_writing":         ielts_scores["skill_writing"],
        "skill_speaking":        ielts_scores["skill_speaking"],
        "strength_target_score": ielts_scores["strength_target_score"],
    }

    # ── 2. 写入 IELTSUserProfile ──
    user_uuid: uuid.UUID | None = None
    try:
        user_uuid = uuid.UUID(body.user_id)
        profile = db.query(IELTSOrmProfile).filter(IELTSOrmProfile.user_id == user_uuid).first()
        if profile:
            for field_name, val in ielts_scores.items():
                if hasattr(profile, field_name):
                    setattr(profile, field_name, val)
            db.commit()
    except Exception:
        pass

    # ── 3. 更新 session 状态 ──
    session = db.query(MatchSession).filter(MatchSession.id == session_id).first()
    if session:
        session.status = "matching"
        try:
            db.commit()
        except Exception:
            db.rollback()

    # ── 4. 查询雅思候选人 ──
    db_candidate_profiles: list[IELTSMatchProfile] = []
    db_candidate_info: dict[str, dict] = {}
    try:
        query = (
            db.query(User, IELTSOrmProfile)
            .join(IELTSOrmProfile, User.id == IELTSOrmProfile.user_id)
        )
        if user_uuid:
            query = query.filter(User.id != user_uuid)
        for user, profile in query.all():
            uid = str(user.id)
            db_candidate_profiles.append(IELTSMatchProfile(
                user_id=uid,
                skill_listening=float(profile.skill_listening or 5.0),
                skill_reading=float(profile.skill_reading or 5.0),
                skill_writing=float(profile.skill_writing or 5.0),
                skill_speaking=float(profile.skill_speaking or 5.0),
                personality_planner=float(profile.personality_planner or 5.0),
                personality_resourcer=float(profile.personality_resourcer or 5.0),
                personality_coordinator=float(profile.personality_coordinator or 5.0),
                strength_fluency=float(profile.strength_fluency or 5.0),
                strength_has_ielts_exp=bool(profile.strength_has_ielts_exp),
                strength_willing_training=bool(profile.strength_willing_training),
                strength_weekly_hours=int(profile.strength_weekly_hours or 0),
                strength_target_score=float(profile.strength_target_score or 5.0),
            ))
            db_candidate_info[uid] = {
                "name": user.name, "grade": user.grade,
                "major": user.major,
                "contact_info": user.contact_info or "请通过平台联系",
            }
    except Exception:
        pass

    # ── 5. 补充 Mock 候选人 ──
    all_profiles = list(db_candidate_profiles)
    all_info = dict(db_candidate_info)
    for mock in _IELTS_MOCK_CANDIDATES:
        if len(all_profiles) >= 3:
            break
        all_profiles.append(IELTSMatchProfile(
            user_id=mock["user_id"],
            skill_listening=mock["skill_listening"],
            skill_reading=mock["skill_reading"],
            skill_writing=mock["skill_writing"],
            skill_speaking=mock["skill_speaking"],
            personality_planner=mock["personality_planner"],
            personality_resourcer=mock["personality_resourcer"],
            personality_coordinator=mock["personality_coordinator"],
            strength_fluency=mock["strength_fluency"],
            strength_has_ielts_exp=mock["strength_has_ielts_exp"],
            strength_willing_training=mock["strength_willing_training"],
            strength_weekly_hours=mock["strength_weekly_hours"],
            strength_target_score=mock["strength_target_score"],
        ))
        all_info[mock["user_id"]] = {
            "name": mock["name"], "grade": mock["grade"],
            "major": mock["major"], "contact_info": mock["contact_info"],
        }

    # ── 6. 运行雅思匹配算法 ──
    current_profile = IELTSMatchProfile(
        user_id=body.user_id,
        skill_listening=ielts_scores["skill_listening"],
        skill_reading=ielts_scores["skill_reading"],
        skill_writing=ielts_scores["skill_writing"],
        skill_speaking=ielts_scores["skill_speaking"],
        personality_planner=ielts_scores["personality_planner"],
        personality_resourcer=ielts_scores["personality_resourcer"],
        personality_coordinator=ielts_scores["personality_coordinator"],
        strength_fluency=ielts_scores["strength_fluency"],
        strength_has_ielts_exp=ielts_scores["strength_has_ielts_exp"],
        strength_willing_training=ielts_scores["strength_willing_training"],
        strength_weekly_hours=ielts_scores["strength_weekly_hours"],
        strength_target_score=ielts_scores["strength_target_score"],
    )
    match_output = find_top_matches_ielts(user_a=current_profile, candidates=all_profiles)

    # ── 7. 组装响应（含雷达图）──
    dim_labels = {d["key"]: d["label"] for d in _IELTS_DIMS}
    result_candidates: list[CandidateResult] = []
    for match in match_output.results:
        info = all_info.get(match.recommended_user_id, {})
        cand_prof = next((p for p in all_profiles if p.user_id == match.recommended_user_id), None)
        cand_dim = {
            "skill_listening":       cand_prof.skill_listening       if cand_prof else 5.0,
            "skill_reading":         cand_prof.skill_reading         if cand_prof else 5.0,
            "skill_writing":         cand_prof.skill_writing         if cand_prof else 5.0,
            "skill_speaking":        cand_prof.skill_speaking        if cand_prof else 5.0,
            "strength_target_score": cand_prof.strength_target_score if cand_prof else 5.0,
        }
        radar = [
            RadarDim(
                dimension=dim_labels.get(dim_key, dim_key),
                user=int(round(user_dim_scores.get(dim_key, 5.0))),
                candidate=int(round(cand_dim.get(dim_key, 5.0))),
            )
            for dim_key in user_dim_scores
        ]
        result_candidates.append(CandidateResult(
            user_id=match.recommended_user_id,
            name=info.get("name", "候选人"),
            grade=info.get("grade", "-"),
            major=info.get("major", "-"),
            match_score=int(round(match.match_score * 100)),
            contact_info=info.get("contact_info", "请通过平台联系"),
            summary=match.match_reasons.get("summary", "综合匹配度较高"),
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
