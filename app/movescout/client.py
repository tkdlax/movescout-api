from typing import Any

import httpx

from app.config import get_settings
from app.movescout.headers import movescout_request_headers


class MoveScoutError(Exception):
    def __init__(self, message: str, status_code: int = 502, code: str = "MOVESCOUT_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class MoveScoutClient:
    def __init__(self, access_token: str) -> None:
        self.settings = get_settings()
        self.access_token = access_token
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "MoveScoutClient":
        self._client = httpx.AsyncClient(
            base_url=self.settings.movescout_base_url,
            timeout=httpx.Timeout(120.0, connect=10.0),
            headers=self._base_headers(),
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    def _base_headers(self) -> dict[str, str]:
        return movescout_request_headers(access_token=self.access_token)

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if not self._client:
            raise RuntimeError("MoveScoutClient must be used as async context manager")

        try:
            response = await self._client.request(method, path, json=json, params=params)
        except httpx.TimeoutException as exc:
            raise MoveScoutError("MoveScout request timed out", code="MOVESCOUT_TIMEOUT") from exc
        except httpx.HTTPError as exc:
            raise MoveScoutError(
                f"MoveScout connection error: {exc}", code="MOVESCOUT_CONNECTION"
            ) from exc

        if response.status_code == 401:
            raise MoveScoutError(
                "MoveScout authentication failed", status_code=401, code="MOVESCOUT_AUTH"
            )

        if response.status_code >= 400:
            detail = response.text[:500] if response.text else response.reason_phrase
            raise MoveScoutError(
                f"MoveScout error ({response.status_code}): {detail}",
                status_code=response.status_code,
                code="MOVESCOUT_UPSTREAM",
            )

        if not response.content:
            return {}

        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}
