from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select

from config import engine
from pojo.Submission import Submission, SubmissionCreate, SubmissionUpdate, SubmissionRead


class SubmissionMapper:

    @staticmethod
    def to_read(submission: Submission) -> SubmissionRead:
        """ORM -> SubmissionRead"""
        return SubmissionRead.model_validate(submission)

    @staticmethod
    def from_create(submission_create: SubmissionCreate) -> Submission:
        """SubmissionCreate -> ORM"""
        user_id = getattr(submission_create, "user_id", None)
        if user_id is None:
            raise ValueError("submission_create 缺少 user_id")

        return Submission(
            problem_id=submission_create.problem_id,
            user_id=user_id,
            user_answer=submission_create.user_answer,
            status="pending",
        )

    @staticmethod
    def apply_update(submission: Submission, submission_update: SubmissionUpdate) -> Submission:
        """在已有 ORM 对象上应用更新"""
        if submission_update.user_answer is not None:
            submission.user_answer = submission_update.user_answer
        if submission_update.status is not None:
            submission.status = submission_update.status
        submission.updated_at = datetime.utcnow()
        return submission

    @staticmethod
    def create(submission_create: SubmissionCreate) -> Submission:
        """插入新提交"""
        with Session(engine) as session:
            submission = SubmissionMapper.from_create(submission_create)
            session.add(submission)
            session.commit()
            session.refresh(submission)
            return submission

    @staticmethod
    def update(submission: Submission, submission_update: SubmissionUpdate) -> Submission:
        """更新提交"""
        with Session(engine) as session:
            db_submission = session.get(Submission, submission.id)
            if not db_submission:
                raise ValueError("提交记录不存在，无法更新")

            SubmissionMapper.apply_update(db_submission, submission_update)
            session.add(db_submission)
            session.commit()
            session.refresh(db_submission)
            return db_submission

    @staticmethod
    def find_by_id(submission_id: int) -> Optional[Submission]:
        """根据 ID 查找提交"""
        with Session(engine) as session:
            stmt = select(Submission).where(Submission.id == submission_id)
            return session.exec(stmt).first()

    @staticmethod
    def find_by_user(user_id: int) -> List[Submission]:
        """查找某个用户的所有提交"""
        with Session(engine) as session:
            stmt = select(Submission).where(Submission.user_id == user_id)
            return session.exec(stmt).all()

    @staticmethod
    def find_by_problem(problem_id: int) -> List[Submission]:
        """查找某个题目的所有提交"""
        with Session(engine) as session:
            stmt = select(Submission).where(Submission.problem_id == problem_id)
            return session.exec(stmt).all()
    @staticmethod
    def insert(submission: Submission) -> Submission:
        with Session(engine) as session:
            session.add(submission)
            session.commit()
            session.refresh(submission)
        return submission

    @staticmethod
    def find_by_user_and_problem(user_id: int, problem_id: int, session: Session) -> List[Submission]:
        """根据 用户ID + 题目ID 查找提交"""
        stmt = select(Submission).where(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id
        )
        return list(session.exec(stmt).all())

    @staticmethod
    def find_all_by_user(user_id: int, session: Session) -> List[Submission]:
        """查找某个用户的所有提交"""
        stmt = select(Submission).where(Submission.user_id == user_id)
        return list(session.exec(stmt).all())
