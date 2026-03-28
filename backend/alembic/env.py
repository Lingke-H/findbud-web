"""
Alembic 迁移环境配置

数据库连接字符串从环境变量 DATABASE_URL 读取，无需在 alembic.ini 中硬编码。
所有在 app/models/ 中定义的 Model 会被自动识别，支持自动生成迁移脚本。
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv(encoding="utf-8")

# 将 backend/ 目录加入 Python 路径，使 app 模块可被导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所有 Model，使 Alembic 能感知到表结构变化
from app.database import Base  # noqa: F401
from app.models.user import User, UserProfile  # noqa: F401
from app.models.session import MatchSession, QuestionAnswer, MatchResult  # noqa: F401

# Alembic 配置对象
config = context.config

# 从环境变量注入数据库连接字符串，覆盖 alembic.ini 中的空值
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", ""))

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标 metadata，Alembic 根据此生成迁移脚本
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移（不需要真实数据库连接，仅生成 SQL 文件）。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移（连接真实数据库执行变更）。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
