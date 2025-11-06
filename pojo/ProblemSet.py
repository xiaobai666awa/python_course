from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import JSON
from sqlmodel import Field, SQLModel

from pojo.User import UserRead


class ProblemSet(SQLModel, table=True):
    __tablename__ = "problem_sets"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    problem_ids: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProblemSetCreate(SQLModel):
    title: str
    description: Optional[str] = None
    problem_ids: List[int] = Field(default_factory=list)


class ProblemSetRead(SQLModel):
    id: int
    title: str
    description: Optional[str]
    problem_ids: List[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProblemSetUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    problem_ids: Optional[List[int]] = None


class ProblemSetCompletion(SQLModel, table=True):
    __tablename__ = "problem_set_completions"

    id: Optional[int] = Field(default=None, primary_key=True)
    problem_set_id: int = Field(foreign_key="problem_sets.id")
    user_id: int = Field(foreign_key="users.id")
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class ProblemSetProblemStatus(SQLModel):
    problem_id: int
    status: Optional[str] = None
    user_answer: Optional[str] = None
    answer: Optional[str] = None
    solution: Optional[str] = None


class ProblemSetStatus(ProblemSetRead):
    completed_users: List[UserRead]
    is_completed: bool = False
    solved_count: int = 0
    problem_statuses: List[ProblemSetProblemStatus] = Field(default_factory=list)
    answers_revealed: bool = False


class ProblemSetPage(SQLModel):
    items: List[ProblemSetStatus]
    total: int
    page: int
    page_size: int


class ProblemSetSubmission(SQLModel, table=True):
    __tablename__ = "problem_set_submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    problem_set_id: int = Field(foreign_key="problem_sets.id")
    problem_id: int = Field(foreign_key="problem.id")
    user_id: int = Field(foreign_key="users.id")
    answer: Optional[str] = None
    status: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


ProblemSetStatus.model_rebuild(force=True)
ProblemSetPage.model_rebuild(force=True)
ProblemSetSubmission.model_rebuild(force=True)
