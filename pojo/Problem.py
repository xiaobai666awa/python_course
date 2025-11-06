from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.dialects.mysql import JSON
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class ProblemType(str, Enum):
    CHOICE = "choice"      # 选择题
    FILL = "fill"          # 填空题
    CODING = "coding"      # 编程题


# 数据库表模型
class Problem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code_id:Optional[int] =0
    title: str
    type: ProblemType
    description: str = Field(sa_column=Column(LONGTEXT))
    options: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    answer: Optional[str] = Field(default=None)
    solution: Optional[str] = Field(default=None, sa_column=Column(LONGTEXT))


# 请求模型（用于创建）
class ProblemCreate(SQLModel):
    title: str
    type: ProblemType
    code_id: Optional[int] = None
    description: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    solution: Optional[str] = None


# 响应模型（用于返回）
class ProblemRead(SQLModel):
    id: int
    title: str
    code_id: Optional[int]
    type: ProblemType
    description: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    solution: Optional[str] = None
    class Config:
        from_attributes = True


class ProblemPage(SQLModel):
    items: List[ProblemRead]
    total: int
    page: int
    page_size: int
