from typing import List, Optional
from mapper.ProblemMapper import ProblemMapper
from pojo.Problem import ProblemRead


class ProblemService:

    @staticmethod
    def get_problem_by_id(problem_id: int) -> Optional[ProblemRead]:
        problem = ProblemMapper.find_by_id(problem_id)
        if problem:
            return ProblemMapper.to_read(problem)
        return None

    @staticmethod
    def get_problems_by_page(page: int, page_size: int = 20) -> List[ProblemRead]:
        problems = ProblemMapper.find_by_page(page, page_size)
        return [ProblemMapper.to_read(p) for p in problems]

    @staticmethod
    def get_problems_by_type(problem_type: str) -> List[ProblemRead]:
        problems = ProblemMapper.find_by_type(problem_type)
        return [ProblemMapper.to_read(p) for p in problems]

    @staticmethod
    def get_problems_by_name(name: str) -> List[ProblemRead]:
        problems = ProblemMapper.find_by_name(name)
        return [ProblemMapper.to_read(p) for p in problems]
