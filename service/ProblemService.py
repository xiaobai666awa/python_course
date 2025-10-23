from typing import List, Optional
from mapper.ProblemMapper import ProblemMapper
from pojo.Problem import Problem, ProblemCreate, ProblemPage, ProblemRead, ProblemType
from pojo.Result import Result


class ProblemService:

    @staticmethod
    def get_problem_by_id(problem_id: int) -> Result[ProblemRead] | Result[None]:
        problem = ProblemMapper.find_by_id(problem_id)
        if problem:
            return Result.success(data=ProblemMapper.to_read(problem), message="查询成功")
        return Result.error(message="未找到对应题目", code=404)

    @staticmethod
    def get_problems_by_page(page: int, page_size: int = 20) -> Result[ProblemPage]:
        problems, total = ProblemMapper.paginate(page, page_size)
        items = [ProblemMapper.to_read(p) for p in problems]
        page_data = ProblemPage(items=items, total=total, page=page, page_size=page_size)
        return Result.success(data=page_data, message="分页查询成功")

    @staticmethod
    def get_problems_by_type(problem_type: str) -> Result[ProblemPage]:
        problems = ProblemMapper.find_by_type(problem_type)
        items = [ProblemMapper.to_read(p) for p in problems]
        page_data = ProblemPage(items=items, total=len(items), page=1, page_size=len(items) or 1)
        return Result.success(data=page_data, message="按类型查询成功")

    @staticmethod
    def get_problems_by_name(name: str) -> Result[ProblemPage]:
        problems = ProblemMapper.find_by_name(name)
        items = [ProblemMapper.to_read(p) for p in problems]
        page_data = ProblemPage(items=items, total=len(items), page=1, page_size=len(items) or 1)
        return Result.success(data=page_data, message="按名称查询成功")

    @staticmethod
    def create_problem(problem: ProblemCreate) -> Result[ProblemRead] | Result[None]:
        if problem.type == ProblemType.CODING and problem.code_id is None:
            return Result.error(message="编程题请提供对应判题id")
        problem_read = ProblemMapper.create(problem)
        return Result.success(data=problem_read, message="成功创建题目")
