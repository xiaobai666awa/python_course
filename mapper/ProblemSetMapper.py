from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from config import get_engine
from pojo.ProblemSet import (
    ProblemSet,
    ProblemSetCompletion,
    ProblemSetCreate,
    ProblemSetRead,
    ProblemSetUpdate,
)


class ProblemSetMapper:
    @staticmethod
    def to_read(problem_set: ProblemSet) -> ProblemSetRead:
        return ProblemSetRead.model_validate(problem_set)

    @staticmethod
    def create(problem_set_create: ProblemSetCreate) -> ProblemSetRead:
        with Session(get_engine()) as session:
            problem_set = ProblemSet.model_validate(problem_set_create.model_dump())
            session.add(problem_set)
            session.commit()
            session.refresh(problem_set)
            return ProblemSetMapper.to_read(problem_set)

    @staticmethod
    def update(problem_set_id: int, update_data: ProblemSetUpdate) -> Optional[ProblemSetRead]:
        with Session(get_engine()) as session:
            problem_set = session.get(ProblemSet, problem_set_id)
            if not problem_set:
                return None

            data = update_data.model_dump(exclude_unset=True)
            for key, value in data.items():
                setattr(problem_set, key, value)
            problem_set.updated_at = datetime.utcnow()

            session.add(problem_set)
            session.commit()
            session.refresh(problem_set)
            return ProblemSetMapper.to_read(problem_set)

    @staticmethod
    def delete(problem_set_id: int) -> bool:
        with Session(get_engine()) as session:
            problem_set = session.get(ProblemSet, problem_set_id)
            if not problem_set:
                return False
            session.delete(problem_set)
            session.commit()
            return True

    @staticmethod
    def find_by_id(problem_set_id: int) -> Optional[ProblemSet]:
        with Session(get_engine()) as session:
            return session.get(ProblemSet, problem_set_id)

    @staticmethod
    def find_all() -> List[ProblemSet]:
        with Session(get_engine()) as session:
            stmt = select(ProblemSet).order_by(ProblemSet.created_at.desc())
            return list(session.exec(stmt).all())

    @staticmethod
    def paginate(page: int, page_size: int) -> List[ProblemSet]:
        with Session(get_engine()) as session:
            offset = (page - 1) * page_size
            stmt = (
                select(ProblemSet)
                .order_by(ProblemSet.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def count() -> int:
        with Session(get_engine()) as session:
            stmt = select(func.count()).select_from(ProblemSet)
            return session.exec(stmt).one()


class ProblemSetCompletionMapper:
    @staticmethod
    def mark_completed(user_id: int, problem_set_id: int) -> ProblemSetCompletion:
        with Session(get_engine()) as session:
            stmt = select(ProblemSetCompletion).where(
                ProblemSetCompletion.user_id == user_id,
                ProblemSetCompletion.problem_set_id == problem_set_id,
            )
            existing = session.exec(stmt).first()
            if existing:
                return existing

            completion = ProblemSetCompletion(user_id=user_id, problem_set_id=problem_set_id)
            session.add(completion)
            session.commit()
            session.refresh(completion)
            return completion

    @staticmethod
    def unmark_completed(user_id: int, problem_set_id: int) -> None:
        with Session(get_engine()) as session:
            stmt = select(ProblemSetCompletion).where(
                ProblemSetCompletion.user_id == user_id,
                ProblemSetCompletion.problem_set_id == problem_set_id,
            )
            completion = session.exec(stmt).first()
            if completion:
                session.delete(completion)
                session.commit()

    @staticmethod
    def list_by_user(user_id: int) -> List[ProblemSetCompletion]:
        with Session(get_engine()) as session:
            stmt = select(ProblemSetCompletion).where(ProblemSetCompletion.user_id == user_id)
            return list(session.exec(stmt).all())

    @staticmethod
    def list_by_problem_set(problem_set_id: int) -> List[ProblemSetCompletion]:
        with Session(get_engine()) as session:
            stmt = select(ProblemSetCompletion).where(
                ProblemSetCompletion.problem_set_id == problem_set_id
            )
            return list(session.exec(stmt).all())
