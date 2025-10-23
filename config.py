import os

from sqlalchemy import create_engine


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("未配置 DATABASE_URL 环境变量")


engine = create_engine(url=DATABASE_URL, pool_pre_ping=True, future=True)
