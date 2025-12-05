from time import sleep
from typing import List, Optional

from sqlmodel import Session

from config import get_engine
from mapper.ProblemMapper import ProblemMapper
from mapper.SubmissionMapper import SubmissionMapper
from pojo.Problem import Problem, ProblemType
from pojo.Result import Result
from pojo.Submission import Submission, SubmissionPage, SubmissionRead, SubmissionUpdate
from service.HojService import HojClient
from service.choice_utils import is_choice_problem, normalize_choice_answer


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
            status,error = SubmissionService._evaluate_coding_answer(problem, user_answer)
            SubmissionMapper.update(submission, SubmissionUpdate(status=status, user_answer=user_answer))
            submission.status = status
            if error:
                return Result.error(message=error, code=502)
        else:
            status = SubmissionService._evaluate_answer(problem, user_answer)
            SubmissionMapper.update(submission, SubmissionUpdate(status=status, user_answer=user_answer))
            submission.status = status

        return Result.success(data=submission, message="提交成功")

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
    def _evaluate_answer(problem: Problem, user_answer: str) -> str:
        options = getattr(problem, "options", None)
        correct_answer = getattr(problem, "answer", None)

        if is_choice_problem(problem):
            normalized_correct = normalize_choice_answer(correct_answer, options)
            normalized_user = normalize_choice_answer(user_answer, options)
            if not normalized_correct or not normalized_user:
                return "wrong"
            return "accepted" if normalized_correct == normalized_user else "wrong"

        if correct_answer and correct_answer == user_answer:
            return "accepted"
        return "wrong"

    @staticmethod
    def _evaluate_coding_answer(problem: Problem, user_answer: str) -> tuple[str, Optional[str]]:
        code_id = getattr(problem, "code_id", None)
        if code_id is None:
            return "error", "编程题缺少判题配置"
        client = HojClient()
        try:
            try:
                submit_id = client.submit(pid=code_id, code=user_answer)
            except ValueError as exc:
                return "error", str(exc)

            status = client.get_result(submit_id)
            # HOJ 中 5/6/7 通常表示评测中，这里继续轮询直到获得最终态
            while status in (5, 6, 7):
                sleep(1)
                status = client.get_result(submit_id)

            if status is None:
                return "error", "HOJ 未返回判题状态"

            if status == -1:
                return "wrong answer", "答案错误"
            if status == 0:
                return "accepted", None
            if status == -3:
                return "PLE", "输出格式错误"

            return "error", f"HOJ 判题失败，状态：{status}"
        finally:
            client.close()
