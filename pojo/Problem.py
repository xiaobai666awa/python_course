from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.dialects.mysql import JSON
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel


class ProblemType(str, Enum):
    CHOICE = "choice"      # 选择题
    FILL = "fill"          # 填空题
    CODING = "coding"      # 编程题


# 数据库表模型
class Problem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: ProblemType
    description: str = Field(sa_column=Column(LONGTEXT))
    options: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    answer: Optional[str] = Field(default=None)


# 请求模型（用于创建）
class ProblemCreate(SQLModel):
    title: str
    type: ProblemType
    description: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None


# 响应模型（用于返回）
class ProblemRead(SQLModel):
    id: int
    title: str
    type: ProblemType
    description: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    class Config:
        from_attributes = True
