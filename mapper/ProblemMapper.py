from sqlmodel import Session, select
from typing import List, Optional

from config import engine
from pojo.Problem import Problem, ProblemRead


class ProblemMapper:

    @staticmethod
    def to_read(problem: Problem) -> ProblemRead:
        """ORM -> ProblemRead"""
        return ProblemRead.model_validate(problem)

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
