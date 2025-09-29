from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List

from Controller.UserController import admin_required
from pojo.Result import Result
from service.ProblemService import ProblemService
from pojo.Problem import ProblemRead, Problem, ProblemCreate

router = APIRouter()

@router.get("/{problem_id}", response_model=Result[ProblemRead])
def get_problem_by_id(problem_id: int):
    """根据 ID 获取题目"""
    problem = ProblemService.get_problem_by_id(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.get("/", response_model=Result[List[ProblemRead]])
def get_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    problem_type: str = Query(None, description="题目类型（choice/fill/code）"),
    name: str = Query(None, description="题目名称（模糊匹配）"),
):
    """获取题目列表，可分页/按类型/按名称筛选"""
    if problem_type:
        return ProblemService.get_problems_by_type(problem_type)
    if name:
        return ProblemService.get_problems_by_name(name)
    return ProblemService.get_problems_by_page(page, page_size)
@router.post("/create", response_model=Result[ProblemRead])
def create_problem(problem: ProblemCreate,_: dict = Depends(admin_required)):
    return ProblemService.create_problem(problem)
