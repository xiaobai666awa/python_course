from typing import Dict, List, Optional

from sqlmodel import Session, select

from config import get_engine
from pojo.ProblemSet import ProblemSetSubmission


class ProblemSetSubmissionMapper:
    @staticmethod
    def upsert(problem_set_id: int, problem_id: int, user_id: int, answer: str, status: str) -> ProblemSetSubmission:
        with Session(get_engine()) as session:
            stmt = select(ProblemSetSubmission).where(
                ProblemSetSubmission.problem_set_id == problem_set_id,
                ProblemSetSubmission.problem_id == problem_id,
                ProblemSetSubmission.user_id == user_id,
            )
            submission = session.exec(stmt).first()
            if submission is None:
                submission = ProblemSetSubmission(
                    problem_set_id=problem_set_id,
                    problem_id=problem_id,
                    user_id=user_id,
                )
            submission.answer = answer
            submission.status = status
            session.add(submission)
            session.commit()
            session.refresh(submission)
            return submission

    @staticmethod
    def list_by_user(problem_set_id: int, user_id: int) -> List[ProblemSetSubmission]:
        with Session(get_engine()) as session:
            stmt = (
                select(ProblemSetSubmission)
                .where(
                    ProblemSetSubmission.problem_set_id == problem_set_id,
                    ProblemSetSubmission.user_id == user_id,
                )
                .order_by(ProblemSetSubmission.submitted_at.desc())
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def map_latest_by_user(problem_set_id: int, user_id: int) -> Dict[int, ProblemSetSubmission]:
        submissions = ProblemSetSubmissionMapper.list_by_user(problem_set_id, user_id)
        latest: Dict[int, ProblemSetSubmission] = {}
        for submission in submissions:
            latest[submission.problem_id] = submission
        return latest

    @staticmethod
    def delete_by_problem_set(problem_set_id: int) -> None:
        with Session(get_engine()) as session:
            stmt = select(ProblemSetSubmission).where(ProblemSetSubmission.problem_set_id == problem_set_id)
            items = session.exec(stmt).all()
            for item in items:
                session.delete(item)
            session.commit()
