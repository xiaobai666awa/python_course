from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List

from Controller.UserController import admin_required
from pojo.Result import Result
from service.ProblemService import ProblemService
from pojo.Problem import ProblemRead, Problem, ProblemCreate, ProblemPage

router = APIRouter()

@router.get("/{problem_id}", response_model=Result[ProblemRead])
def get_problem_by_id(problem_id: int):
    """根据 ID 获取题目"""
    result = ProblemService.get_problem_by_id(problem_id)
    return _ensure_success(result)


@router.get("/", response_model=Result[ProblemPage])
def get_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    problem_type: str = Query(None, description="题目类型（choice/fill/code）"),
    name: str = Query(None, description="题目名称（模糊匹配）"),
):
    """获取题目列表，可分页/按类型/按名称筛选"""
    if problem_type:
        return _ensure_success(ProblemService.get_problems_by_type(problem_type))
    if name:
        return _ensure_success(ProblemService.get_problems_by_name(name))
    return _ensure_success(ProblemService.get_problems_by_page(page, page_size))
@router.post("/create", response_model=Result[ProblemRead])
def create_problem(problem: ProblemCreate,_: dict = Depends(admin_required)):
    return _ensure_success(ProblemService.create_problem(problem))


def _ensure_success(result: Result):
    if result.code >= 400:
        raise HTTPException(status_code=result.code, detail=result.message)
    return result
