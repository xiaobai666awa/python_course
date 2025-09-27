from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

# --- 数据模型 ---
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    password: str
    create_at: datetime = Field(default_factory=datetime.utcnow)
    update_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    name: str
    password: str


class UserRead(SQLModel):
    id: int
    name: str
    create_at: datetime
    update_at: datetime


class UserUpdate(SQLModel):
    name: Optional[str] = None
    password: Optional[str] = None