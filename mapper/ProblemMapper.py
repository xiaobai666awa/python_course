from sqlmodel import Session, select
from typing import List, Optional

from config import engine
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
        with Session(engine) as session:
            stmt = select(Problem).where(Problem.id == problem_id)
            result = session.exec(stmt).first()
            return result

    @staticmethod
    def find_by_page(page: int, page_size: int = 20) -> List[Problem]:
        """分页获取题目"""
        with Session(engine) as session:
            offset = (page - 1) * page_size
            stmt = select(Problem).offset(offset).limit(page_size)
            results = session.exec(stmt).all()
            return results

    @staticmethod
    def find_by_type(problem_type: str) -> List[Problem]:
        """根据题目类型获取题目"""
        with Session(engine) as session:
            stmt = select(Problem).where(Problem.problem_type == problem_type)
            results = session.exec(stmt).all()
            return results

    @staticmethod
    def find_by_name(name: str) -> List[Problem]:
        """根据题目名称模糊匹配"""
        with Session(engine) as session:
            stmt = select(Problem).where(Problem.title.like(f"%{name}%"))
            results = session.exec(stmt).all()
            return results
    @staticmethod
    def create(problem: ProblemCreate) -> ProblemRead:
        problem = ProblemMapper.from_create(problem)
        with Session(engine) as session:
            session.add(problem)
            session.commit()
            session.refresh(problem)
        return ProblemMapper.to_read(problem)

