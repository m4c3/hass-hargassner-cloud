
from __future__ import annotations

from typing import Any, Optional
from aiohttp import ClientSession

class HargassnerClient:
    def __init__(self, session: ClientSession, username: str, password: str, client_secret: str, installation: str, auth_url: str, widgets_url: str):
        self._session = session
        self._username = username
        self._password = password
        self._client_secret = client_secret
        self._installation = installation
        self._auth_url = auth_url
        self._widgets_url = widgets_url
        self._token: Optional[str] = None

    async def login(self) -> None:
        payload = {
            "username": self._username,
            "password": self._password,
            "client_secret": self._client_secret,
        }
        async with self._session.post(self._auth_url, json=payload) as resp:
            resp.raise_for_status()
            js = await resp.json()
            token = js.get("access_token") or (js.get("data") or {}).get("access_token") or js.get("token")
            if not token:
                raise RuntimeError("Login did not return an access_token")
            self._token = token

    async def get_widgets(self) -> dict[str, Any]:
        if not self._token:
            await self.login()
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        async with self._session.get(self._widgets_url, headers=headers) as resp:
            if resp.status == 401:
                await self.login()
                return await self.get_widgets()
            resp.raise_for_status()
            return await resp.json()
