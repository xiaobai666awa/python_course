# pojo/Submission.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel


class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id")
    user_id: int = Field(foreign_key="user.id")

    answer: str  # 用户提交的答案（字符串，或者 JSON 序列化后的数据）
    status: str = Field(default="pending")  # pending / accepted / wrong / error

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 关系（方便 ORM 联查）
    problem: Optional["Problem"] = Relationship(back_populates="submissions")
    user: Optional["User"] = Relationship(back_populates="submissions")
