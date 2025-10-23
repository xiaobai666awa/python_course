from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from Controller.UserController import admin_required
from pojo.ProblemSet import ProblemSetCreate, ProblemSetPage, ProblemSetStatus, ProblemSetUpdate
from pojo.Result import Result
from service.ProblemSetService import ProblemSetService
from utils.security import get_current_user, get_optional_user


router = APIRouter()


@router.get("/", response_model=Result[ProblemSetPage])
def list_problem_sets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    user_id = current_user.get("user_id") if current_user else None
    return ProblemSetService.list_problem_sets(page, page_size, user_id)


@router.get("/{problem_set_id}", response_model=Result[ProblemSetStatus])
def get_problem_set(
    problem_set_id: int,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    user_id = current_user.get("user_id") if current_user else None
    result = ProblemSetService.get_problem_set(problem_set_id, user_id)
    if result.code >= 400:
        raise HTTPException(status_code=result.code, detail=result.message)
    return result


@router.post("/", response_model=Result[ProblemSetStatus])
def create_problem_set(
    payload: ProblemSetCreate,
    _: dict = Depends(admin_required),
):
    result = ProblemSetService.create_problem_set(payload)
    return _ensure_success(result)


@router.put("/{problem_set_id}", response_model=Result[ProblemSetStatus])
def update_problem_set(
    problem_set_id: int,
    payload: ProblemSetUpdate,
    _: dict = Depends(admin_required),
):
    result = ProblemSetService.update_problem_set(problem_set_id, payload)
    return _ensure_success(result)


@router.delete("/{problem_set_id}", response_model=Result[None])
def delete_problem_set(problem_set_id: int, _: dict = Depends(admin_required)):
    result = ProblemSetService.delete_problem_set(problem_set_id)
    return _ensure_success(result)


@router.post("/{problem_set_id}/completion", response_model=Result[None])
def mark_problem_set_completed(
    problem_set_id: int,
    current_user: dict = Depends(get_current_user),
):
    result = ProblemSetService.mark_completion(problem_set_id, current_user["user_id"])
    return _ensure_success(result)


@router.delete("/{problem_set_id}/completion", response_model=Result[None])
def unmark_problem_set_completed(
    problem_set_id: int,
    current_user: dict = Depends(get_current_user),
):
    result = ProblemSetService.unmark_completion(problem_set_id, current_user["user_id"])
    return _ensure_success(result)


def _ensure_success(result: Result):
    if result.code >= 400:
        raise HTTPException(status_code=result.code, detail=result.message)
    return result
