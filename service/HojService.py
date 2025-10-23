import asyncio
import os
from typing import Optional

import httpx


class HojClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        *,
        timeout: Optional[httpx.Timeout] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("HOJ_BASE_URL", "https://127.0.0.1")).rstrip("/")
        self.username = username or os.getenv("HOJ_USERNAME")
        self.password = password or os.getenv("HOJ_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("未配置 HOJ 登录账号或密码")

        self._timeout = timeout or httpx.Timeout(10.0, connect=5.0, read=30.0)
        self.session: Optional[httpx.AsyncClient] = None
        self.token: Optional[str] = None

    async def __aenter__(self) -> "HojClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self.session is not None:
            await self.session.aclose()
        self.session = None
        self.token = None

    async def _ensure_session(self) -> None:
        if self.session is None:
            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self._timeout,
                follow_redirects=True,
            )

    async def login(self) -> None:
        await self._ensure_session()
        assert self.session is not None
        resp = await self.session.post("/api/login", json={"username": self.username, "password": self.password})
        resp.raise_for_status()
        self.token = resp.headers.get("authorization")

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        await self._ensure_session()
        assert self.session is not None

        if not self.token:
            await self.login()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = self.token
        resp = await self.session.request(method, url, headers=headers, **kwargs)

        if resp.status_code in (401, 403):
            await self.login()
            headers["Authorization"] = self.token
            resp = await self.session.request(method, url, headers=headers, **kwargs)

        resp.raise_for_status()
        return resp

    async def submit(self, pid: str, code: str, language: str = "Python3") -> int:
        payload = {
            "pid": pid,
            "language": language,
            "code": code,
            "cid": 0,
            "tid": None,
            "gid": None,
            "isRemote": False,
        }
        resp = await self._request("POST", "/api/submit-problem-judge", json=payload)
        data = resp.json()
        return data["data"]["submitId"]

    async def get_result(self, submit_id: int) -> int:
        resp = await self._request("GET", f"/api/get-submission-detail?submitId={submit_id}")
        data = resp.json()
        return data["data"]["submission"]["status"]
