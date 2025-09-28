from sqlmodel import Session
from typing import List, Optional, Any

from config import engine
from pojo.Submission import Submission, SubmissionUpdate
from pojo.Problem import Problem
from mapper.SubmissionMapper import SubmissionMapper
from mapper.ProblemMapper import ProblemMapper
from pojo.Result import Result


class SubmissionService:

    @staticmethod
    def submit_answer(user_id: int, problem_id: int, data: str) -> Result[None] | Result[Submission]:
        with Session(engine) as session:
            problem: Optional[Problem] = ProblemMapper.find_by_id(problem_id)
            if not problem:
                return Result.error(message="题目不存在")

            submission = Submission(
                user_id=user_id,
                problem_id=problem_id,
                data=data
            )

            # 判题逻辑
            if problem.type == "CODING" or problem.type == "编程题":
                submission.status = "PENDING"
                submission.completed = False
                return Result.success(data=submission,message="题目以加入判题机")

            elif problem.type in ("CHOICE", "FILL", "选择题", "填空题"):
                correct_answer = problem.answer
                if correct_answer and correct_answer == data:
                    submission.status = "ACCEPTED"
                    submission.completed = True
                else:
                    submission.status = "WRONG"
                    submission.completed = True
            else:
                return Result.error(message="未知题目类型: {problem.type}")

            SubmissionMapper.insert(submission, session)
            return Result.success(data=submission, message="提交成功")

    @staticmethod
    def get_user_submissions(user_id: int, problem_id: int) -> Result[List[Submission]]:
        with Session(engine) as session:
            submissions = SubmissionMapper.find_by_user_and_problem(user_id, problem_id, session)
            return Result.success(data=submissions)

    @staticmethod
    def get_all_user_submissions(user_id: int) -> Result[List[Submission]]:
        with Session(engine) as session:
            submissions = SubmissionMapper.find_all_by_user(user_id, session)
            return Result.success(data=submissions)

    @staticmethod
    def update_submission_status(submission_id: int, status: str) -> Result[None] | Result[Submission]:
        with Session(engine) as session:
            submission: Optional[Submission] = SubmissionMapper.find_by_id(submission_id)
            if not submission:
                return Result.error(message="提交记录不存在")
            submission_update=SubmissionUpdate.model_value(submission)
            submission_update.status = status
            submission_update.completed = True
            SubmissionMapper.update(submission,submission_update)
            return Result.success(data=submission, message="更新成功")
