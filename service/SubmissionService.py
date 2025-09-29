import asyncio

from sqlmodel import Session
from typing import List, Optional, Any

from config import engine
from pojo.Submission import Submission, SubmissionUpdate
from pojo.Problem import Problem
from mapper.SubmissionMapper import SubmissionMapper
from mapper.ProblemMapper import ProblemMapper
from pojo.Result import Result
from service.HojService import HojClient


class SubmissionService:


    @staticmethod
    def submit_answer(user_id: int, problem_id: int, data: str) -> Result[None] | Result[Submission]:

                problem: Optional[Problem] = ProblemMapper.find_by_id(problem_id)
                if not problem:
                    return Result.error(message="题目不存在")

                submission = Submission(
                    user_id=user_id,
                    problem_id=problem_id,
                    data=data,
                    status="PENDING",
                )

                SubmissionMapper.insert(submission)

                # 如果是编程题，丢给 HOJ 判题机异步执行
                if problem.type in ("CODING", "编程题"):
                    asyncio.create_task(SubmissionService._judge_with_hoj(submission.id, problem.id, data))

                else:  # 选择题/填空题直接判分
                    correct_answer = problem.answer
                    if correct_answer and correct_answer == data:
                        status = "accepted"
                    else:
                        status = "wrong"
                    user_answer = data
                    SubmissionMapper.update(submission, SubmissionUpdate(status=status, user_answer=user_answer))

                return Result.success(data=submission, message="提交成功")

    @staticmethod
    async def _judge_with_hoj(submission_id: int, problem_id: int, code: str):
            """
            异步提交到 HOJ 并回写数据库
            """
            client = HojClient()
            submit_id = await client.submit(pid=str(problem_id), code=code)

            # 轮询判题结果
            while True:
                result = await client.get_result(submit_id)
                status = result
                if status <1:
                    status = "accepted" if status == 1 else "rejected"
                    submission=SubmissionMapper.find_by_id(submit_id)
                    submission_update=SubmissionUpdate(status=status,user_answer=code)
                    SubmissionMapper.update(submission, submission_update)
                    break
                await asyncio.sleep(2)
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
            SubmissionMapper.update(submission,submission_update)
            return Result.success(data=submission, message="更新成功")


