from typing import Any

import httpx

BASE_URL = "https://api.infusionsoft.com/crm/rest/v1"


class KeapError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Keap API error {status_code}: {message}")


class KeapClient:
    """Async httpx client wrapping the Keap (Infusionsoft) REST API v1.

    Auth: a Personal Access Token or Service Account Key
    (Settings > API Settings in the Keap app; no OAuth redirect needed),
    sent as `Authorization: Bearer <token>`.
    """

    def __init__(self, access_token: str):
        self._headers = {"Authorization": f"Bearer {access_token}"}

    def _clean_params(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    async def get(self, path: str, params: dict | None = None) -> Any:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}{path}",
                headers=self._headers,
                params=self._clean_params(params),
            )
            self._raise_for_status(resp)
            return resp.json() if resp.status_code != 204 else None

    async def post(self, path: str, body: dict | None = None, params: dict | None = None) -> Any:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}{path}",
                headers=self._headers,
                json=body,
                params=self._clean_params(params),
            )
            self._raise_for_status(resp)
            return resp.json() if resp.status_code != 204 else None

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise KeapError(resp.status_code, str(detail))
