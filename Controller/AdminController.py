from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query

from Controller.UserController import admin_required
from pojo.Result import Result
from pojo.Submission import SubmissionPage, SubmissionRead
from service.SubmissionService import SubmissionService
from service.SystemConfigService import SystemConfigService


router = APIRouter()


@router.get("/config", response_model=Result[Dict[str, str]])
def get_system_config(_: dict = Depends(admin_required)):
    result = SystemConfigService.get_config()
    return _ensure_success(result)


@router.put("/config", response_model=Result[Dict[str, str]])
def update_system_config(payload: Dict[str, str], _: dict = Depends(admin_required)):
    result = SystemConfigService.update_config(payload)
    return _ensure_success(result)


@router.get("/submissions", response_model=Result[SubmissionPage])
def list_all_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: dict = Depends(admin_required),
):
    result = SubmissionService.list_all_submissions(page, page_size)
    return _ensure_success(result)


@router.get("/users/{user_id}/submissions", response_model=Result[List[SubmissionRead]])
def list_user_submissions(user_id: int, _: dict = Depends(admin_required)):
    result = SubmissionService.list_submissions_by_user(user_id)
    return _ensure_success(result)


def _ensure_success(result: Result):
    if result.code >= 400:
        raise HTTPException(status_code=result.code, detail=result.message)
    return result
