from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SystemConfig(SQLModel, table=True):
    __tablename__ = "system_config"

    key: str = Field(primary_key=True, index=True)
    value: str
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SystemConfigRead(SQLModel):
    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemConfigUpdate(SQLModel):
    value: str
    description: Optional[str] = None
