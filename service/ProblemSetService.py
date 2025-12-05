from typing import List, Optional

from config import get_engine
from mapper.ProblemMapper import ProblemMapper
from mapper.ProblemSetMapper import ProblemSetCompletionMapper, ProblemSetMapper
from mapper.ProblemSetSubmissionMapper import ProblemSetSubmissionMapper
from mapper.UserMapper import UserMapper
from pojo.Problem import Problem, ProblemType
from pojo.ProblemSet import (
    ProblemSet,
    ProblemSetCreate,
    ProblemSetPage,
    ProblemSetProblemStatus,
    ProblemSetRead,
    ProblemSetStatus,
    ProblemSetUpdate,
)
from pojo.Result import Result
from service.HojService import HojService
from service.choice_utils import is_choice_problem, normalize_choice_answer


class ProblemSetService:
    @staticmethod
    def create_problem_set(data: ProblemSetCreate) -> Result[ProblemSetStatus] | Result[None]:
        problem_set = ProblemSetMapper.create(data)
        status = ProblemSetService._build_status(
            ProblemSet.model_validate(problem_set.model_dump()), None
        )
        return Result.success(data=status, message="成功创建题集")

    @staticmethod
    def update_problem_set(
        problem_set_id: int, data: ProblemSetUpdate
    ) -> Result[ProblemSetStatus] | Result[None]:
        updated = ProblemSetMapper.update(problem_set_id, data)
        if not updated:
            return Result.error(message="题集不存在", code=404)
        status = ProblemSetService._build_status(
            ProblemSet.model_validate(updated.model_dump()), None
        )
        return Result.success(data=status, message="成功更新题集")

    @staticmethod
    def delete_problem_set(problem_set_id: int) -> Result[None]:
        deleted = ProblemSetMapper.delete(problem_set_id)
        if not deleted:
            return Result.error(message="题集不存在", code=404)
        return Result.success(message="成功删除题集")

    @staticmethod
    def submit_problem_answer(problem_set_id: int, problem_id: int, user_id: int, answer: str) -> Result[ProblemSetProblemStatus]:
        problem_set = ProblemSetMapper.find_by_id(problem_set_id)
        if not problem_set:
            return Result.error(message="题集不存在", code=404)
        if problem_id not in problem_set.problem_ids:
            return Result.error(message="题目不属于该题集", code=400)

        problem = ProblemMapper.find_by_id(problem_id)
        if not problem:
            return Result.error(message="题目不存在", code=404)

        normalized_answer = answer.strip()

        if ProblemSetService._is_coding_problem(problem):
            status, error = ProblemSetService._evaluate_coding_answer(problem, normalized_answer)
            if error:
                return Result.error(message=error, code=502)
        else:
            status = ProblemSetService._evaluate_answer(problem, normalized_answer)

        submission = ProblemSetSubmissionMapper.upsert(
            problem_set_id, problem_id, user_id, normalized_answer, status
        )

        if ProblemSetService._has_user_completed_problem_set(problem_set, user_id):
            ProblemSetCompletionMapper.mark_completed(user_id, problem_set_id)
        else:
            ProblemSetCompletionMapper.unmark_completed(user_id, problem_set_id)

        revealed = ProblemSetService._has_user_completed_problem_set(problem_set, user_id)
        problem_status = ProblemSetProblemStatus(
            problem_id=problem_id,
            status=submission.status,
            user_answer=submission.answer,
            answer=problem.answer if revealed else None,
            solution=getattr(problem, "solution", None) if revealed else None,
        )

        return Result.success(data=problem_status, message="提交成功")

    @staticmethod
    def list_problem_sets(
        page: int,
        page_size: int,
        current_user_id: Optional[int] = None,
    ) -> Result[ProblemSetPage]:
        total = ProblemSetMapper.count()
        sets = ProblemSetMapper.paginate(page, page_size)
        data = [ProblemSetService._build_status(s, current_user_id) for s in sets]
        page_model = ProblemSetPage(items=data, total=total, page=page, page_size=page_size)
        return Result.success(data=page_model, message="获取题集列表成功")

    @staticmethod
    def get_problem_set(
        problem_set_id: int, current_user_id: Optional[int] = None
    ) -> Result[ProblemSetStatus] | Result[None]:
        problem_set = ProblemSetMapper.find_by_id(problem_set_id)
        if not problem_set:
            return Result.error(message="题集不存在", code=404)
        status = ProblemSetService._build_status(problem_set, current_user_id)
        return Result.success(data=status, message="获取题集详情成功")

    @staticmethod
    def mark_completion(problem_set_id: int, user_id: int) -> Result[None]:
        problem_set = ProblemSetMapper.find_by_id(problem_set_id)
        if not problem_set:
            return Result.error(message="题集不存在", code=404)
        if not ProblemSetService._has_user_completed_problem_set(problem_set, user_id):
            return Result.error(message="尚未完成题集中的所有题目", code=400)
        ProblemSetCompletionMapper.mark_completed(user_id=user_id, problem_set_id=problem_set_id)
        return Result.success(message="已标记题集完成")

    @staticmethod
    def unmark_completion(problem_set_id: int, user_id: int) -> Result[None]:
        ProblemSetCompletionMapper.unmark_completed(user_id=user_id, problem_set_id=problem_set_id)
        return Result.success(message="已取消题集完成标记")

    @staticmethod
    def _build_status(problem_set: ProblemSet, current_user_id: Optional[int]) -> ProblemSetStatus:
        completions = ProblemSetCompletionMapper.list_by_problem_set(problem_set.id)
        completion_user_ids = {comp.user_id for comp in completions}
        completed_users = []
        for user_id in completion_user_ids:
            user = UserMapper.find_by_id(user_id)
            if user:
                completed_users.append(UserMapper.to_read(user))

        problem_statuses: List[ProblemSetProblemStatus] = []
        solved_count = 0
        answers_revealed = False

        if current_user_id is not None:
            submissions_map = ProblemSetSubmissionMapper.map_latest_by_user(problem_set.id, current_user_id)
            problems = {pid: ProblemMapper.find_by_id(pid) for pid in problem_set.problem_ids}
            answers_revealed = ProblemSetService._has_user_completed_problem_set(problem_set, current_user_id)

            for pid in problem_set.problem_ids:
                submission = submissions_map.get(pid)
                status = submission.status if submission else None
                if status == "accepted":
                    solved_count += 1

                problem = problems.get(pid)
                answer = problem.answer if problem else None
                solution = getattr(problem, "solution", None) if problem else None

                problem_statuses.append(
                    ProblemSetProblemStatus(
                        problem_id=pid,
                        status=status,
                        user_answer=submission.answer if submission else None,
                        answer=answer if answers_revealed else None,
                        solution=solution if answers_revealed else None,
                    )
                )

            if answers_revealed:
                if current_user_id not in completion_user_ids:
                    ProblemSetCompletionMapper.mark_completed(current_user_id, problem_set.id)
                    user = UserMapper.find_by_id(current_user_id)
                    if user:
                        completed_users.append(UserMapper.to_read(user))
            else:
                ProblemSetCompletionMapper.unmark_completed(current_user_id, problem_set.id)

        return ProblemSetStatus(
            id=problem_set.id,
            title=problem_set.title,
            description=problem_set.description,
            problem_ids=problem_set.problem_ids,
            created_at=problem_set.created_at,
            updated_at=problem_set.updated_at,
            completed_users=completed_users,
            is_completed=answers_revealed,
            solved_count=solved_count,
            problem_statuses=problem_statuses,
            answers_revealed=answers_revealed,
        )

    @staticmethod
    def _has_user_completed_problem_set(problem_set: ProblemSet, user_id: int) -> bool:
        if not problem_set.problem_ids:
            return False
        submissions_map = ProblemSetSubmissionMapper.map_latest_by_user(problem_set.id, user_id)
        return all(pid in submissions_map for pid in problem_set.problem_ids)

    @staticmethod
    def _evaluate_answer(problem: Problem, user_answer: str) -> str:
        correct_answer = getattr(problem, "answer", None)
        options = getattr(problem, "options", None)

        if is_choice_problem(problem):
            normalized_correct = normalize_choice_answer(correct_answer, options)
            normalized_user = normalize_choice_answer(user_answer, options)
            if normalized_correct is None or normalized_user is None:
                return "wrong"
            return "accepted" if normalized_correct == normalized_user else "wrong"

        if correct_answer is None:
            return "accepted"
        return "accepted" if str(correct_answer).strip() == user_answer.strip() else "wrong"

    @staticmethod
    def _evaluate_coding_answer(problem: Problem, user_answer: str) -> tuple[str, Optional[str]]:
        code_id = getattr(problem, "code_id", None)
        if code_id is None:
            return "error", "编程题缺少判题配置"

        status, error = HojService.judge_submission(int(code_id), user_answer)
        if status:
            return HojService.normalize_status(status), None
        return "error", error or "HOJ 判题失败"

    @staticmethod
    def _is_coding_problem(problem: Problem) -> bool:
        problem_type = getattr(problem, "type", None)
        if isinstance(problem_type, ProblemType):
            return problem_type == ProblemType.CODING
        return str(problem_type).lower() in {"coding", "编程题"}
