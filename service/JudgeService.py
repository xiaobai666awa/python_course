import json
from pojo.Submission import Submission
from pojo.Problem import Problem


class JudgeService:

    @staticmethod
    def judge(problem: Problem, submission: Submission) -> str:
        """判题核心入口"""
        if problem.problem_type == "choice":
            return JudgeService.judge_choice(problem, submission)

        elif problem.problem_type == "fill":
            return JudgeService.judge_fill(problem, submission)

        elif problem.problem_type == "code":
            # 代码题交给外部判题机
            return "pending"  # 或者 "waiting"

        return "error"

    @staticmethod
    def judge_choice(problem: Problem, submission: Submission) -> str:
        """选择题判题"""
        return "accepted" if submission.user_answer.strip() == problem.answer.strip() else "wrong"

    @staticmethod
    def judge_fill(problem: Problem, submission: Submission) -> str:
        """填空题判题（答案是 JSON 数组）"""
        try:
            correct_answers = json.loads(problem.answer)  # e.g. ["hello", "world"]
            user_answers = json.loads(submission.answer)  # e.g. ["Hello", "world"]

            if len(correct_answers) != len(user_answers):
                return "wrong"

            for ca, ua in zip(correct_answers, user_answers):
                if ca.strip().lower() != ua.strip().lower():
                    return "wrong"
            return "accepted"
        except Exception:
            return "error"
