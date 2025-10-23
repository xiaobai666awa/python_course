import asyncio
from typing import List, Optional

from sqlmodel import Session

from config import engine
from mapper.ProblemMapper import ProblemMapper
from mapper.SubmissionMapper import SubmissionMapper
from pojo.Problem import Problem, ProblemType
from pojo.Result import Result
from pojo.Submission import Submission, SubmissionUpdate
from service.HojService import HojClient
from service.ProblemSetService import ProblemSetService


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
            if status == "accepted":
                ProblemSetService.refresh_completion_for_user(user_id, [problem_id])

        return Result.success(data=submission, message="提交成功")

    @staticmethod
    async def _judge_with_hoj(submission_id: int, code_id: int, code: str):
        """
        异步提交到 HOJ 并回写数据库
        """
        try:
            async with HojClient() as client:
                submit_id = await client.submit(pid=str(code_id), code=code)

                while True:
                    status_code = await client.get_result(submit_id)
                    if status_code < 1:
                        final_status = "accepted" if status_code == 0 else "rejected"
                        submission = SubmissionMapper.find_by_id(submission_id)
                        if submission:
                            updated = SubmissionMapper.update(
                                submission,
                                SubmissionUpdate(status=final_status, user_answer=code),
                            )
                            if final_status == "accepted":
                                ProblemSetService.refresh_completion_for_user(updated.user_id, [updated.problem_id])
                        break
                    await asyncio.sleep(2)
        except Exception:
            submission = SubmissionMapper.find_by_id(submission_id)
            if submission:
                SubmissionMapper.update(submission, SubmissionUpdate(status="error"))

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
    def update_submission_status(submission_id: int, status: str) -> Result[Submission] | Result[None]:
        submission: Optional[Submission] = SubmissionMapper.find_by_id(submission_id)
        if not submission:
            return Result.error(message="提交记录不存在", code=404)

        updated = SubmissionMapper.update(submission, SubmissionUpdate(status=status))
        if status == "accepted":
            ProblemSetService.refresh_completion_for_user(updated.user_id, [updated.problem_id])
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
