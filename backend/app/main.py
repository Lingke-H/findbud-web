"""
FindBud 后端应用入口

启动方式（在 backend/ 目录下执行）：
    uvicorn app.main:app --reload

启动后访问 http://127.0.0.1:8000/docs 查看接口文档。
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import user_router, question_router
from app.services import ai_service

# 加载环境变量
load_dotenv(encoding="utf-8")

# 创建 FastAPI 应用实例
app = FastAPI(
    title="FindBud API",
    description="找搭子 App 后端接口文档",
    version="0.1.0",
)

# 跨域配置（允许 React Native 前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有来源，上线前收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 健康检查接口 ==========

@app.get("/health", tags=["系统"])
def health_check():
    """
    健康检查接口，用于确认服务是否正常运行。
    返回 {"status": "ok"} 表示服务正常。
    """
    return {"status": "ok", "message": "FindBud 后端服务运行正常"}


# ========== 诊断接口 ==========

@app.get("/test/ai", tags=["诊断"])
async def test_ai():
    """
    测试 AI API 连通性。
    返回 {"status": "ok", "reply": "..."} 表示 AI 正常响应。
    返回 {"status": "error", "detail": "..."} 表示配置或网络问题。
    """
    try:
        result = await ai_service.generate_batch_questions(
            competition_type="数学建模",
            dimensions=[{"name": "skill_modeling", "description": "数学建模能力"}],
        )
        return {"status": "ok", "question_count": len(result), "first_question": result[0] if result else None}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ========== 注册路由模块 ==========

app.include_router(user_router.router, prefix="/api/v1")
app.include_router(question_router.router, prefix="/api/v1")
