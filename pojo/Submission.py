# pojo/Submission.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import TINYTEXT
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from pojo.Problem import Problem
from pojo.User import User

class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id")
    user_id: int = Field(foreign_key="users.id")
    user_answer: str =Field(sa_column=Column(TINYTEXT))  # 用户提交的答案（字符串，或者 JSON 序列化后的数据）
    status: str = Field(default="pending")  # pending / accepted / wrong / error

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 关系（方便 ORM 联查）

class SubmissionCreate(SQLModel):
    problem_id: int
    user_answer: str # 用户提交的答案（字符串，或者 JSON 序列化后的数据）


class SubmissionRead(SQLModel):
    id: int
    problem_id: int
    user_id: int
    user_answer: str  # 用户提交的答案（字符串，或者 JSON 序列化后的数据）
    status: str
    created_at: datetime
    updated_at: datetime


class SubmissionUpdate(BaseModel):
    user_answer: str # 用户提交的答案（字符串，或者 JSON 序列化后的数据）
    status: Optional[str] = None
