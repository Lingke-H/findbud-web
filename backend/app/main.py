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

from app.routers import user_router

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


# ========== 注册路由模块 ==========

app.include_router(user_router.router, prefix="/api/v1")
# hlk 完成后在这里追加：
# app.include_router(match_router.router, prefix="/api/v1")
