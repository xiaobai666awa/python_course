from typing import List, Optional

from sqlmodel import Session, select

from config import get_engine
from mapper.ProblemSetMapper import ProblemSetCompletionMapper, ProblemSetMapper
from mapper.SubmissionMapper import SubmissionMapper
from mapper.UserMapper import UserMapper
from pojo.Problem import Problem
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
from pojo.Submission import Submission


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
    def refresh_completion_for_user(user_id: int, problem_ids: List[int]) -> None:
        if not problem_ids:
            return

        related_problem_ids = set(problem_ids)
        problem_sets = ProblemSetMapper.find_all()

        for problem_set in problem_sets:
            if not problem_set.problem_ids:
                continue

            if not related_problem_ids.intersection(problem_set.problem_ids):
                continue

            completed = ProblemSetService._has_user_completed_problem_set(problem_set, user_id)
            if completed:
                ProblemSetCompletionMapper.mark_completed(user_id, problem_set.id)
            else:
                ProblemSetCompletionMapper.unmark_completed(user_id, problem_set.id)

    @staticmethod
    def _build_status(problem_set: ProblemSet, current_user_id: Optional[int]) -> ProblemSetStatus:
        completions = ProblemSetCompletionMapper.list_by_problem_set(problem_set.id)
        completed_users = []
        completion_user_ids = {comp.user_id for comp in completions}

        for user_id in completion_user_ids:
            user = UserMapper.find_by_id(user_id)
            if user:
                completed_users.append(UserMapper.to_read(user))

        is_completed = False
        solved_count = 0
        problem_statuses: List[ProblemSetProblemStatus] = []

        if current_user_id is not None:
            status_map = SubmissionMapper.last_status_by_user_for_problems(
                current_user_id, problem_set.problem_ids
            )
            for pid in problem_set.problem_ids:
                submission = status_map.get(pid)
                status = submission.status if submission else None
                if status == "accepted":
                    solved_count += 1
                problem_statuses.append(ProblemSetProblemStatus(problem_id=pid, status=status))

            if current_user_id in completion_user_ids:
                is_completed = True
            else:
                if ProblemSetService._has_user_completed_problem_set(problem_set, current_user_id):
                    ProblemSetCompletionMapper.mark_completed(current_user_id, problem_set.id)
                    is_completed = True
                    user = UserMapper.find_by_id(current_user_id)
                    if user:
                        completed_users.append(UserMapper.to_read(user))
        else:
            problem_statuses = []

        total_problems = len(problem_set.problem_ids)

        return ProblemSetStatus(
            id=problem_set.id,
            title=problem_set.title,
            description=problem_set.description,
            problem_ids=problem_set.problem_ids,
            created_at=problem_set.created_at,
            updated_at=problem_set.updated_at,
            completed_users=completed_users,
            is_completed=is_completed,
            solved_count=solved_count if current_user_id is not None else 0,
            problem_statuses=problem_statuses,
        )

    @staticmethod
    def _has_user_completed_problem_set(problem_set: ProblemSet, user_id: int) -> bool:
        if not problem_set.problem_ids:
            return False

        with Session(get_engine()) as session:
            stmt = select(Submission.problem_id).where(
                Submission.user_id == user_id,
                Submission.status == "accepted",
                Submission.problem_id.in_(problem_set.problem_ids),
            )
            accepted_problem_ids = {
                row[0] if isinstance(row, tuple) else row for row in session.exec(stmt).all()
            }

        return all(problem_id in accepted_problem_ids for problem_id in problem_set.problem_ids)
