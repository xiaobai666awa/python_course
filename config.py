import os
from threading import Lock
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class EngineManager:
    _lock: Lock = Lock()
    _engine: Optional[Engine] = None
    _database_url: Optional[str] = None

    @classmethod
    def _ensure_url(cls) -> str:
        if cls._database_url:
            return cls._database_url
        url = os.getenv("DATABASE_URL","mysql+pymysql://root:hoj123456@localhost:3306/PyClass")
        if not url:
            raise ValueError("未配置 DATABASE_URL 环境变量")
        cls._database_url = url
        return url

    @classmethod
    def get_engine(cls) -> Engine:
        with cls._lock:
            if cls._engine is None:
                cls._engine = create_engine(
                    url=cls._ensure_url(), pool_pre_ping=True, future=True
                )
            return cls._engine

    @classmethod
    def get_database_url(cls) -> str:
        return cls._ensure_url()

    @classmethod
    def set_database_url(cls, database_url: str) -> Engine:
        if not database_url:
            raise ValueError("数据库地址不能为空")
        with cls._lock:
            if cls._engine is not None:
                cls._engine.dispose()
            cls._database_url = database_url
            cls._engine = create_engine(
                url=database_url, pool_pre_ping=True, future=True
            )
        os.environ["DATABASE_URL"] = database_url
        return cls._engine


def get_engine() -> Engine:
    return EngineManager.get_engine()


def get_database_url() -> str:
    return EngineManager.get_database_url()


def update_database_url(database_url: str) -> Engine:
    return EngineManager.set_database_url(database_url)
