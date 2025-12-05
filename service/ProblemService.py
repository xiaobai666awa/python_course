import json
import os
import re
from typing import Any, List, Optional

import yaml

from mapper.ProblemMapper import ProblemMapper
from pojo.Problem import Problem, ProblemCreate, ProblemPage, ProblemRead, ProblemType
from pojo.Result import Result
from service.HojService import HojService

MAX_PROBLEM_IMPORT_BYTES = int(os.getenv("PROBLEM_IMPORT_MAX_BYTES", str(2 * 1024 * 1024)))  # 默认 2MB


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
        if problem.type == ProblemType.CODING:
            try:
                problem.code_id = ProblemService._ensure_valid_code_id(problem.code_id)
            except ValueError as exc:
                return Result.error(message=str(exc), code=400)
        problem_read = ProblemMapper.create(problem)
        return Result.success(data=problem_read, message="成功创建题目")

    @staticmethod
    def import_problems_from_file(
        file_bytes: bytes,
        requested_format: Optional[str] = None,
    ) -> Result[List[ProblemRead]]:
        if not file_bytes:
            return Result.error(message="上传文件为空", code=400)

        if len(file_bytes) > MAX_PROBLEM_IMPORT_BYTES:
            return Result.error(message="文件过大，请拆分后再上传", code=400)

        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return Result.error(message="文件必须为 UTF-8 编码", code=400)

        fmt = (requested_format or "auto").lower()
        parsed: Any | None = None
        last_error: str | None = None

        if fmt in {"json", "auto"}:
            try:
                parsed = json.loads(text)
                fmt = "json"
            except json.JSONDecodeError as exc:
                last_error = f"JSON 解析失败: {exc}"
                if requested_format == "json":
                    return Result.error(message=last_error, code=400)

        if parsed is None and fmt in {"text", "yaml", "yml", "auto"}:
            try:
                parsed = yaml.safe_load(text)
                fmt = "text"
            except yaml.YAMLError as exc:
                last_error = f"文本解析失败: {exc}"
                if requested_format in {"text", "yaml", "yml"}:
                    return Result.error(message=last_error, code=400)

        if parsed is None:
            message = last_error or "无法解析文件内容，请提供 JSON 或 YAML 文本"
            return Result.error(message=message, code=400)

        try:
            raw_items = ProblemService._normalize_problem_items(parsed)
        except ValueError as exc:
            return Result.error(message=str(exc), code=400)

        created: List[ProblemRead] = []
        skipped_messages: List[str] = []
        validated_code_ids: set[int] = set()

        for index, payload in enumerate(raw_items, start=1):
            try:
                problem_create = ProblemService._build_problem_create(
                    payload,
                    validated_code_ids=validated_code_ids,
                )
            except ValueError as exc:
                skipped_messages.append(f"第 {index} 题：{exc}")
                continue

            created.append(ProblemMapper.create(problem_create))

        if not created:
            detail = "文件中未找到有效题目"
            if skipped_messages:
                detail = f"{detail}。示例：{skipped_messages[0]}"
            return Result.error(message=detail, code=400)

        extra = f"，其中 {len(skipped_messages)} 道题被跳过" if skipped_messages else ""
        return Result.success(
            data=created,
            message=f"成功导入 {len(created)} 道题目{extra}",
        )

    @staticmethod
    def _normalize_problem_items(parsed: Any) -> List[dict]:
        if isinstance(parsed, list):
            items = parsed
        elif isinstance(parsed, dict):
            if "problems" in parsed and isinstance(parsed["problems"], list):
                items = parsed["problems"]
            else:
                items = [parsed]
        else:
            raise ValueError("文件内容必须是题目数组或包含 problems 字段的对象")

        if not items:
            raise ValueError("文件中未包含任何题目内容")

        normalized: List[dict] = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("题目内容必须为对象结构")
            normalized.append(item)
        return normalized

    @staticmethod
    def _build_problem_create(payload: dict, validated_code_ids: Optional[set[int]] = None) -> ProblemCreate:
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("缺少 title")

        type_value = payload.get("type") or payload.get("problem_type")
        if not type_value:
            raise ValueError("缺少 type")

        if isinstance(type_value, ProblemType):
            problem_type = type_value
        else:
            type_str = str(type_value)
            if type_str.startswith("ProblemType."):
                type_str = type_str.split(".", 1)[1]
            type_str = type_str.lower()
            try:
                problem_type = ProblemType(type_str)
            except ValueError:
                raise ValueError(f"type 不合法：{type_value}")

        description = str(payload.get("description") or "").strip()
        if not description:
            raise ValueError("缺少 description")

        options = ProblemService._normalize_options(payload.get("options"))
        if problem_type == ProblemType.CHOICE and not options:
            raise ValueError("选择题需要提供 options 列表")

        answer = payload.get("answer")
        if isinstance(answer, list):
            answer = "\n".join(str(item) for item in answer)
        elif answer is not None:
            answer = str(answer)

        code_id = ProblemService._parse_optional_int(payload.get("code_id") or payload.get("codeId"))


        solution = payload.get("solution")
        if solution is not None:
            solution = str(solution)

        return ProblemCreate(
            title=title,
            type=problem_type,
            description=description,
            options=options,
            answer=answer,
            code_id=code_id,
            solution=solution,
        )

    @staticmethod
    def _normalize_options(options_value: Any) -> Optional[List[str]]:
        if options_value is None:
            return None
        if isinstance(options_value, list):
            cleaned = [str(opt).strip() for opt in options_value if str(opt).strip()]
            return cleaned or None
        if isinstance(options_value, str):
            parts = [part.strip() for part in re.split(r"\r?\n|\|", options_value) if part.strip()]
            return parts or None
        raise ValueError("options 需要为数组或分隔字符串")

    @staticmethod
    def _parse_optional_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError("code_id 必须为数字")
