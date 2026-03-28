"""
数据库连接配置模块

负责创建 SQLAlchemy 引擎、会话工厂，以及提供 FastAPI 依赖注入用的 get_db() 函数。
数据库连接字符串从环境变量 DATABASE_URL 读取，禁止硬编码。
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量读取数据库连接字符串
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("环境变量 DATABASE_URL 未设置，请检查 backend/.env 文件")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",  # DEBUG 模式下打印 SQL 语句
    pool_pre_ping=True,   # 自动检测断开的连接
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 所有 ORM Model 的基类，model 文件中继承此类
class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI 依赖注入函数，提供数据库会话。
    用法：在路由函数参数中写 db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
