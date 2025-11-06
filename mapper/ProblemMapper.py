from sqlalchemy import func
from sqlmodel import Session, select
from typing import List, Optional

from config import get_engine
from pojo.Problem import Problem, ProblemRead, ProblemCreate
from pojo.Result import Result


class ProblemMapper:

    @staticmethod
    def to_read(problem: Problem) -> ProblemRead:
        """ORM -> ProblemRead"""
        return ProblemRead.model_validate(problem)
    @staticmethod
    def to_create(problem: Problem) -> ProblemCreate:
        """ORM -> ProblemCreate"""
        return ProblemCreate.model_validate(problem)
    @staticmethod
    def from_create(problem:ProblemCreate) -> Problem:
        return Problem.model_validate(problem.model_dump())

    @staticmethod
    def find_by_id(problem_id: int) -> Optional[Problem]:
        """根据 ID 查找题目"""
        with Session(get_engine()) as session:
            stmt = select(Problem).where(Problem.id == problem_id)
            result = session.exec(stmt).first()
            return result

    @staticmethod
    def paginate(page: int, page_size: int = 20) -> tuple[List[Problem], int]:
        """分页获取题目"""
        with Session(get_engine()) as session:
            total_stmt = select(func.count()).select_from(Problem)
            total = session.exec(total_stmt).one()

            offset = (page - 1) * page_size
            stmt = select(Problem).offset(offset).limit(page_size)
            results = session.exec(stmt).all()
            return list(results), total

    @staticmethod
    def find_by_type(problem_type: str) -> List[Problem]:
        """根据题目类型获取题目"""
        with Session(get_engine()) as session:
            stmt = select(Problem).where(Problem.problem_type == problem_type)
            results = session.exec(stmt).all()
            return results

    @staticmethod
    def find_by_name(name: str) -> List[Problem]:
        """根据题目名称模糊匹配"""
        with Session(get_engine()) as session:
            stmt = select(Problem).where(Problem.title.like(f"%{name}%"))
            results = session.exec(stmt).all()
            return results
    @staticmethod
    def create(problem: ProblemCreate) -> ProblemRead:
        problem_obj = ProblemMapper.from_create(problem)
        with Session(get_engine()) as session:
            session.add(problem_obj)
            session.commit()
            session.refresh(problem_obj)
        return ProblemMapper.to_read(problem_obj)
