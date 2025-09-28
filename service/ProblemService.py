from typing import List, Optional
from mapper.ProblemMapper import ProblemMapper
from pojo.Problem import ProblemRead, Problem, ProblemCreate
from pojo.Result import Result


class ProblemService:

    @staticmethod
    def get_problem_by_id(problem_id: int) -> Result[Optional[ProblemRead]]:
        problem = ProblemMapper.find_by_id(problem_id)
        if problem:
            return Result.success(data=ProblemMapper.to_read(problem), message="查询成功")
        return Result.failure(message="未找到对应题目")

    @staticmethod
    def get_problems_by_page(page: int, page_size: int = 20) -> Result[List[ProblemRead]]:
        problems = ProblemMapper.find_by_page(page, page_size)
        data = [ProblemMapper.to_read(p) for p in problems]
        return Result.success(data=data, message="分页查询成功")

    @staticmethod
    def get_problems_by_type(problem_type: str) -> Result[List[ProblemRead]]:
        problems = ProblemMapper.find_by_type(problem_type)
        data = [ProblemMapper.to_read(p) for p in problems]
        return Result.success(data=data, message="按类型查询成功")

    @staticmethod
    def get_problems_by_name(name: str) -> Result[List[ProblemRead]]:
        problems = ProblemMapper.find_by_name(name)
        data = [ProblemMapper.to_read(p) for p in problems]
        return Result.success(data=data, message="按名称查询成功")

    @staticmethod
    def create_problem(problem: ProblemCreate) -> Result[ProblemRead]:
        problem_read = ProblemMapper.create(problem)
        return Result.success(data=problem_read, message="成功创建题目")
