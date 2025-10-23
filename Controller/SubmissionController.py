# Controller/SubmissionController.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from Controller.UserController import admin_required
from pojo.Result import Result
from pojo.Submission import Submission, SubmissionCreate
from service.SubmissionService import SubmissionService
from utils.security import get_current_user  # 你之前写的鉴权方法

router = APIRouter()


@router.post("/submit", response_model=Result[Submission])
async def submit_answer(
    submission:SubmissionCreate,
    current_user: dict = Depends(get_current_user)  # 鉴权
):
    """
    提交答案（需要登录）
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="用户信息无效")
    result = SubmissionService.submit_answer(user_id, submission.problem_id, submission.user_answer)
    if result.code >= 400:
        raise HTTPException(status_code=result.code, detail=result.message)
    return result


@router.get("/user/{problem_id}", response_model=Result[List[Submission]])
def get_user_submissions(
    problem_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户在某题目的提交记录（需要登录）
    """
    user_id = current_user.get("user_id")
    return SubmissionService.get_user_submissions(user_id, problem_id)

@router.get("/{submission_id}", response_model=Result[Submission])
def get_submissions(
    submission_id:int,
    current_user: dict = Depends(get_current_user)
):
    result = SubmissionService.get_submission_by_id(submission_id)
    if result.code >= 400 or not result.data:
        raise HTTPException(status_code=result.code, detail=result.message)

    submission = result.data
    if submission.user_id != current_user.get("user_id") and current_user.get("name") != "admin":
        raise HTTPException(status_code=403, detail="无访问权限")

    return result
@router.get("/user", response_model=Result[List[Submission]])
def get_all_user_submissions(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户所有提交记录（需要登录）
    """
    user_id = current_user.get("user_id")
    return SubmissionService.get_all_user_submissions(user_id)


@router.put("/{submission_id}", response_model=Result[Submission])
def update_submission_status(
    submission_id: int,
    status: str,
    _: dict = Depends(admin_required)
):
    """
    更新提交状态（仅限管理员）
    """
    result = SubmissionService.update_submission_status(submission_id, status)
    if result.code >= 400:
        raise HTTPException(status_code=result.code, detail=result.message)
    return result
