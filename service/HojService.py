import time
from typing import Optional, Tuple

import httpx

from service.SystemConfigService import SystemConfigService


class HojClient:
    """轻量级 HOJ HTTP 客户端，负责登录与发起请求。"""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1",
        username: str = "root",
        password: str = "hoj123456",
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.token: Optional[str] = None
        self.session = httpx.Client(timeout=timeout)

    @classmethod
    def from_settings(cls) -> "HojClient":
        """使用系统配置创建客户端实例。"""
        settings = SystemConfigService.get_hoj_settings()
        return cls(
            base_url=settings.get("base_url", "http://127.0.0.1"),
            username=settings.get("username", "root"),
            password=settings.get("password", "hoj123456"),
        )

    @staticmethod
    def _build_url(base: str, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        prefix = base.rstrip("/")
        suffix = path if path.startswith("/") else f"/{path}"
        return f"{prefix}{suffix}"

    def login(self) -> None:
        """登录并缓存 token。"""
        url = self._build_url(self.base_url, "/api/login")
        resp = self.session.post(url, json={"username": self.username, "password": self.password})
        resp.raise_for_status()
        token = resp.headers.get("authorization") or resp.headers.get("Authorization")
        if not token:
            raise ValueError("HOJ 登录成功但未返回 authorization 头")
        self.token = token

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """带自动登录与 token 失效重试的请求封装。"""
        if not self.token:
            self.login()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = self.token
        resp = self.session.request(method, url, headers=headers, **kwargs)

        if resp.status_code in (401, 403):
            self.login()
            headers["Authorization"] = self.token
            resp = self.session.request(method, url, headers=headers, **kwargs)

        return resp

    def submit(self, pid: str | int, code: str, language: str = "Python3") -> int:
        """提交代码，返回 HOJ 的提交 ID。"""
        url = self._build_url(self.base_url, "/api/submit-problem-judge")
        payload = {
            "pid": str(pid),
            "language": language,
            "code": code,
            "cid": 0,
            "tid": None,
            "gid": None,
            "isRemote": False,
        }
        resp = self._request("POST", url, json=payload)
        resp.raise_for_status()

        data = resp.json() or {}
        submit_info = data.get("data") or {}
        submit_id = submit_info.get("submitId")
        if submit_id is None:
            raise ValueError(f"HOJ 未返回 submitId，响应: {data}")
        return submit_id

    def get_result(self, submit_id: int) -> Optional[int]:
        """获取判题结果状态码。"""
        url = self._build_url(self.base_url, f"/api/get-submission-detail?submitId={submit_id}")
        resp = self._request("GET", url)
        resp.raise_for_status()
        data = resp.json() or {}

        submission = (data.get("data") or {}).get("submission") or {}
        return submission.get("status")

    def wait_for_result(self, submit_id: int, interval: float = 2.0) -> Optional[int]:
        """轮询直到获得最终状态。"""
        status = self.get_result(submit_id)
        while status in HojService.PENDING_STATUS_CODES:
            time.sleep(interval)
            status = self.get_result(submit_id)
        return status

    def close(self) -> None:
        """关闭 HTTP 会话。"""
        self.session.close()

    def _problem_exists(self, code_id: int) -> Tuple[bool, Optional[str]]:
        url = self._build_url(self.base_url, f"/api/get-problem-detail?pid={code_id}")
        resp = self._request("GET", url)

        if resp.status_code == 404:
            return False, f"HOJ 中未找到题目 {code_id}"

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return False, f"HOJ 校验失败：{exc.response.text}"

        try:
            payload = resp.json() or {}
        except ValueError:
            return False, "HOJ 返回非 JSON 内容"

        status = payload.get("status") or payload.get("code")
        if status not in (200, 0, "200", "success", "SUCCESS"):
            message = payload.get("msg") or payload.get("message") or f"HOJ 未找到题目 {code_id}"
            return False, message

        data = payload.get("data")
        if data is None:
            return False, f"HOJ 未找到题目 {code_id}"

        return True, None

    @classmethod
    def problem_exists(cls, code_id: int) -> Tuple[bool, Optional[str]]:
        client = cls.from_settings()
        try:
            return client._problem_exists(code_id)
        except httpx.HTTPError as exc:
            return False, f"HOJ 请求失败：{exc}"
        finally:
            client.close()


class HojService:
    """封装常用的 HOJ 判题逻辑，供业务层复用。"""

    PENDING_STATUS_CODES = {5, 6, 7}
    POLL_INTERVAL_SECONDS = 1.0
    MAX_POLL_ATTEMPTS = 60

    STATUS_MAP = {
        0: "accepted",
        -1: "wrong answer",
        -2: "time limit exceeded",
        -3: "presentation error",
        -4: "memory limit exceeded",
        -5: "runtime error",
        -6: "compile error",
        -7: "system error",
        -10: "system error",
        5: "pending",
        6: "pending",
        7: "pending",
    }

    @staticmethod
    def problem_exists(code_id: int) -> Tuple[bool, Optional[str]]:
        return HojClient.problem_exists(code_id)

    @classmethod
    def judge_submission(
        cls,
        code_id: int,
        user_answer: str,
        language: str = "Python3",
    ) -> Tuple[Optional[int], Optional[str]]:
        client = HojClient.from_settings()
        try:
            submit_id = client.submit(pid=code_id, code=user_answer, language=language)
            status = client.get_result(submit_id)
            attempts = 0

            while status in cls.PENDING_STATUS_CODES and attempts < cls.MAX_POLL_ATTEMPTS:
                time.sleep(cls.POLL_INTERVAL_SECONDS)
                status = client.get_result(submit_id)
                attempts += 1

            if status in cls.PENDING_STATUS_CODES:
                return None, "HOJ 判题超时，请稍后再试"

            if status is None:
                return None, "HOJ 未返回判题状态"

            return status, None
        except ValueError as exc:
            return None, str(exc)
        except httpx.HTTPError as exc:
            return None, f"HOJ 请求失败：{exc}"
        finally:
            client.close()

    @classmethod
    def normalize_status(cls, status: Optional[int | str]) -> str:
        if status is None:
            return "error"
        try:
            status_int = int(status)
        except (TypeError, ValueError):
            normalized = str(status).strip().lower()
            if normalized in {"accepted", "ac"}:
                return "accepted"
            if normalized in {"wrong answer", "wa"}:
                return "wrong answer"
            return "error"

        return cls.STATUS_MAP.get(status_int, "error")
