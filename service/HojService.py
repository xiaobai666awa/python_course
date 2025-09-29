import httpx
import asyncio
import time


class HojClient:
    def __init__(self, base_url="http://127.0.0.1", username="python_course0", password="maekoz"):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.session = httpx.AsyncClient()

    async def login(self):
        url = f"{self.base_url}/api/login"
        resp = await self.session.post(url, json={"username": self.username, "password": self.password})
        resp.raise_for_status()
        self.token = resp.headers.get("authorization")

    async def _request(self, method, url, **kwargs):
        if not self.token:
            await self.login()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = self.token
        resp = await self.session.request(method, url, headers=headers, **kwargs)

        if resp.status_code in (401, 403):
            await self.login()
            headers["Authorization"] = self.token
            resp = await self.session.request(method, url, headers=headers, **kwargs)
        return resp

    async def submit(self, pid: str, code: str, language="Python3") -> int:
        url = f"{self.base_url}/api/submit-problem-judge"
        payload = {
            "pid": pid,
            "language": language,
            "code": code,
            "cid": 0,
            "tid": None,
            "gid": None,
            "isRemote": False
        }
        resp = await self._request("POST", url, json=payload)
        resp.raise_for_status()
        return resp.json()["data"]["submitId"]

    async def get_result(self, submit_id: int) -> int:
        url = f"{self.base_url}/api/get-submission-detail?submitId={submit_id}"
        resp = await self._request("GET", url)
        resp.raise_for_status()
        return resp.json()["data"]['status']
