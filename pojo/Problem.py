from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.dialects.mysql import JSON
from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel


class ProblemType(str, Enum):
    CHOICE = "choice"      # 选择题
    FILL = "fill"          # 填空题
    CODING = "coding"      # 编程题


# 数据库表模型
class Problem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code_id:Optional[str] =""
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
    code_id: Optional[str] = None
    description: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    solution: Optional[str] = None


# 响应模型（用于返回）
class ProblemRead(SQLModel):
    id: int
    title: str
    code_id: Optional[str]
    type: ProblemType
    description: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    solution: Optional[str] = None
    is_multi_choice: bool = False
    class Config:
        from_attributes = True


class ProblemPage(SQLModel):
    items: List[ProblemRead]
    total: int
    page: int
    page_size: int


def is_multi_choice_answer(
    problem_type: Union[ProblemType, str, None],
    answer: Optional[str],
    options: Optional[List[str]] = None,
) -> bool:
    """Return True if a choice-type answer string implies multiple selections."""
    if not answer:
        return False

    if isinstance(problem_type, ProblemType):
        type_value = problem_type.value
    elif problem_type is None:
        type_value = None
    else:
        type_value = str(problem_type).strip().lower()

    if type_value not in {ProblemType.CHOICE.value, "choice"}:
        return False

    from service.choice_utils import normalize_choice_answer

    normalized = normalize_choice_answer(answer, options)
    if not normalized:
        return False
    return len(normalized) > 1
