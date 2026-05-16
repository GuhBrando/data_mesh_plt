import base64
import logging
import re

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.github.com"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class GitHubClient:
    def __init__(self, token: str, repo: str):
        self._repo = repo
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def contract_path(self, domain: str, title: str) -> str:
        return f"contracts/{_slugify(domain)}/{_slugify(title)}.yaml"

    async def _get_sha(self, client: httpx.AsyncClient, path: str) -> str | None:
        r = await client.get(
            f"{_API}/repos/{self._repo}/contents/{path}",
            headers=self._headers,
        )
        if r.status_code == 200:
            return r.json().get("sha")
        return None

    @staticmethod
    def _raise_for_status(r: httpx.Response) -> None:
        if not r.is_success:
            raise RuntimeError(f"GitHub API {r.status_code}: {r.text}")

    async def push(self, path: str, content: str, message: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            sha = await self._get_sha(client, path)
            payload: dict = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
            }
            if sha:
                payload["sha"] = sha
            r = await client.put(
                f"{_API}/repos/{self._repo}/contents/{path}",
                headers=self._headers,
                json=payload,
            )
            self._raise_for_status(r)

    async def delete(self, path: str, message: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            sha = await self._get_sha(client, path)
            if sha is None:
                return
            r = await client.request(
                "DELETE",
                f"{_API}/repos/{self._repo}/contents/{path}",
                headers=self._headers,
                json={"message": message, "sha": sha},
            )
            self._raise_for_status(r)

    async def list_all_yaml_contents(self) -> list[tuple[str, str]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{_API}/repos/{self._repo}/git/trees/HEAD?recursive=1",
                headers=self._headers,
            )
            if r.status_code != 200:
                return []
            tree = r.json().get("tree", [])
            blobs = [
                i
                for i in tree
                if i["path"].startswith("contracts/")
                and i["path"].endswith(".yaml")
                and i["type"] == "blob"
            ]
            results: list[tuple[str, str]] = []
            for item in blobs:
                blob_r = await client.get(item["url"], headers=self._headers)
                if blob_r.status_code == 200:
                    raw = blob_r.json().get("content", "")
                    content = base64.b64decode(raw.replace("\n", "")).decode()
                    results.append((item["path"], content))
            return results
