# pojo/Problem.py
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel

from pojo.Submission import Submission


class ProblemType(str, Enum):
    CHOICE = "choice"      # 选择题
    FILL = "fill"          # 填空题
    CODING = "coding"      # 编程题
class Problem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: ProblemType

    # options 和 answer 用 JSON 存储（仅部分题型用到）
    options: Optional[List[str]] = Field(default=None, sa_column_kwargs={"type_": "JSON"})
    answer: Optional[str] = Field(default=None)
    submissions: List["Submission"] = Relationship(back_populates="problem")
class ProblemCreate(BaseModel):
    title: str
    type: ProblemType
    options: Optional[List[str]] = None
    answer: Optional[str] = None


class ProblemRead(BaseModel):
    id: int
    title: str
    type: ProblemType
    options: Optional[List[str]] = None
    answer: Optional[str] = None


class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[ProblemType] = None
    options: Optional[List[str]] = None
    answer: Optional[str] = None
