from typing import Dict, List, Optional

from sqlmodel import Session, select

from config import get_engine
from pojo.SystemConfig import SystemConfig


class SystemConfigMapper:
    @staticmethod
    def get(key: str) -> Optional[SystemConfig]:
        with Session(get_engine()) as session:
            return session.get(SystemConfig, key)

    @staticmethod
    def set(key: str, value: str, description: Optional[str] = None) -> SystemConfig:
        with Session(get_engine()) as session:
            config = session.get(SystemConfig, key)
            if config is None:
                config = SystemConfig(key=key, value=value, description=description)
                session.add(config)
            else:
                config.value = value
                if description is not None:
                    config.description = description
            session.commit()
            session.refresh(config)
            return config

    @staticmethod
    def get_many(keys: List[str]) -> Dict[str, SystemConfig]:
        if not keys:
            return {}
        with Session(get_engine()) as session:
            stmt = select(SystemConfig).where(SystemConfig.key.in_(keys))
            results = session.exec(stmt).all()
            return {item.key: item for item in results}

    @staticmethod
    def all() -> List[SystemConfig]:
        with Session(get_engine()) as session:
            stmt = select(SystemConfig)
            return list(session.exec(stmt).all())
