from sqlmodel import Session
from typing import List, Optional

from config import engine
from pojo.Submission import Submission
from pojo.Problem import Problem
from mapper.SubmissionMapper import SubmissionMapper
from mapper.ProblemMapper import ProblemMapper


class SubmissionService:

    @staticmethod
    def submit_answer(user_id: int, problem_id: int, data: str) -> Submission:
        with Session(engine) as session:
            problem: Optional[Problem] = ProblemMapper.find_by_id(problem_id)
            if not problem:
                raise ValueError("题目不存在")

            submission = Submission(
                user_id=user_id,
                problem_id=problem_id,
                data=data
            )

            # 判题逻辑
            if problem.type == "编程题":
                # 编程题交给判题机，先置为 PENDING
                submission.status = "PENDING"
                submission.completed = False

            elif problem.type in ("选择题", "填空题"):
                # 客观题即时判分
                correct_answer = problem.answer
                if correct_answer and correct_answer == data:
                    submission.status = "ACCEPTED"
                    submission.completed = True
                else:
                    submission.status = "WRONG"
                    submission.completed = True

            else:
                raise ValueError(f"未知题目类型: {problem.type}")

            SubmissionMapper.insert(submission, session)
            return submission

    @staticmethod
    def get_user_submissions(user_id: int, problem_id: int) -> List[Submission]:
        with Session(engine) as session:
            return SubmissionMapper.find_by_user_and_problem(user_id, problem_id, session)

    @staticmethod
    def get_all_user_submissions(user_id: int) -> List[Submission]:
        with Session(engine) as session:
            return SubmissionMapper.find_all_by_user(user_id, session)

    @staticmethod
    def update_submission_status(submission_id: int, status: str) -> Submission:
        with Session(engine) as session:
            submission: Optional[Submission] = SubmissionMapper.find_by_id(submission_id, session)
            if not submission:
                raise ValueError("提交记录不存在")

            submission.status = status
            submission.completed = True
            SubmissionMapper.update(submission, session)
            return submission
