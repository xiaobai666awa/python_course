import asyncio
from typing import List, Optional

from sqlmodel import Session

from config import get_engine
from mapper.ProblemMapper import ProblemMapper
from mapper.SubmissionMapper import SubmissionMapper
from pojo.Problem import Problem, ProblemType
from pojo.Result import Result
from pojo.Submission import Submission, SubmissionPage, SubmissionRead, SubmissionUpdate
from service.HojService import HojClient


class SubmissionService:


    @staticmethod
    def submit_answer(user_id: int, problem_id: int, user_answer: str) -> Result[Submission] | Result[None]:
        problem: Optional[Problem] = ProblemMapper.find_by_id(problem_id)
        if not problem:
            return Result.error(message="题目不存在", code=404)

        is_coding = SubmissionService._is_coding_problem(problem)

        if is_coding and not getattr(problem, "code_id", None):
            return Result.error(message="编程题缺少判题配置", code=400)

        submission = Submission(
            user_id=user_id,
            problem_id=problem_id,
            user_answer=user_answer,
            status="pending",
        )

        SubmissionMapper.insert(submission)

        if is_coding:
            asyncio.create_task(
                SubmissionService._judge_with_hoj(submission.id, problem.code_id, user_answer)
            )
        else:
            status = SubmissionService._evaluate_answer(problem.answer, user_answer)
            SubmissionMapper.update(submission, SubmissionUpdate(status=status, user_answer=user_answer))
            submission.status = status

        return Result.success(data=submission, message="提交成功")

    @staticmethod
    async def _judge_with_hoj(submission_id: int, code_id: int, code: str):
            """
            异步提交到 HOJ 并回写数据库
            """
            client = HojClient()
            submit_id = await client.submit(pid=str(code_id), code=code)

            # 轮询判题结果
            while True:
                result = await client.get_result(submit_id)
                status = result
                if status <1:
                    status = "accepted" if status == 0 else "rejected"
                    submission=SubmissionMapper.find_by_id(submission_id)
                    submission_update=SubmissionUpdate(status=status,user_answer=code)
                    SubmissionMapper.update(submission, submission_update)
                    break
                await asyncio.sleep(2)
    @staticmethod
    def get_user_submissions(user_id: int, problem_id: int) -> Result[List[Submission]]:
        with Session(get_engine()) as session:
            submissions = SubmissionMapper.find_by_user_and_problem(user_id, problem_id, session)
            return Result.success(data=submissions)

    @staticmethod
    def get_all_user_submissions(user_id: int) -> Result[List[Submission]]:
        with Session(get_engine()) as session:
            submissions = SubmissionMapper.find_all_by_user(user_id, session)
            return Result.success(data=submissions)

    @staticmethod
    def list_all_submissions(page: int, page_size: int) -> Result[SubmissionPage]:
        submissions, total = SubmissionMapper.paginate_all(page, page_size)
        data = [SubmissionMapper.to_read(item) for item in submissions]
        page_data = SubmissionPage(items=data, total=total, page=page, page_size=page_size)
        return Result.success(data=page_data, message="获取提交列表成功")

    @staticmethod
    def list_submissions_by_user(user_id: int) -> Result[List[SubmissionRead]]:
        submissions = SubmissionMapper.list_all_by_user(user_id)
        data = [SubmissionMapper.to_read(item) for item in submissions]
        return Result.success(data=data, message="获取用户提交成功")

    @staticmethod
    def update_submission_status(submission_id: int, status: str) -> Result[Submission] | Result[None]:
        submission: Optional[Submission] = SubmissionMapper.find_by_id(submission_id)
        if not submission:
            return Result.error(message="提交记录不存在", code=404)

        updated = SubmissionMapper.update(submission, SubmissionUpdate(status=status))
        return Result.success(data=updated, message="更新成功")


    @staticmethod
    def get_submission_by_id(submission_id: int) -> Result[Submission]:
        submission: Optional[Submission] = SubmissionMapper.find_by_id(submission_id)
        if not submission:
            return Result.error(message="提交记录不存在", code=404)
        return Result.success(data=submission, message="成功获取submission")

    @staticmethod
    def _is_coding_problem(problem: Problem) -> bool:
        problem_type = getattr(problem, "type", None)
        if isinstance(problem_type, ProblemType):
            return problem_type == ProblemType.CODING
        return str(problem_type).lower() in {"coding", "编程题"}

    @staticmethod
    def _evaluate_answer(correct_answer: Optional[str], user_answer: str) -> str:
        if correct_answer and correct_answer == user_answer:
            return "accepted"
        return "wrong"
