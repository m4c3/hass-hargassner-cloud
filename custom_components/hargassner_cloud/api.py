
from __future__ import annotations

from typing import Any, Optional
import logging

from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

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
        _LOGGER.debug("Attempting to authenticate user '%s' against %s", self._username, self._auth_url)
        payload = {
            "username": self._username,
            "password": self._password,
            "client_secret": self._client_secret,
        }
        async with self._session.post(self._auth_url, json=payload) as resp:
            _LOGGER.debug("Authentication request completed with status %s", resp.status)
            if resp.status >= 400:
                _LOGGER.debug("Authentication failed with body: %s", await resp.text())
            resp.raise_for_status()
            js = await resp.json()
            token = js.get("access_token") or (js.get("data") or {}).get("access_token") or js.get("token")
            if not token:
                raise RuntimeError("Login did not return an access_token")
            self._token = token
            expires_in = js.get("expires_in") or (js.get("data") or {}).get("expires_in")
            token_type = js.get("token_type") or (js.get("data") or {}).get("token_type")
            if token_type:
                _LOGGER.debug("Authentication succeeded, token type: %s", token_type)
            if expires_in is not None:
                _LOGGER.debug("Access token expires in %s seconds", expires_in)
            _LOGGER.debug("Authentication succeeded, received access token (length=%d)", len(token))

    async def get_widgets(self) -> dict[str, Any]:
        if not self._token:
            _LOGGER.debug("No cached access token available, logging in before widgets request")
            await self.login()
        else:
            _LOGGER.debug(
                "Using cached access token to request widgets for installation '%s'", self._installation
            )
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        _LOGGER.debug(
            "Requesting widgets for installation '%s' from %s", self._installation, self._widgets_url
        )
        async with self._session.get(self._widgets_url, headers=headers) as resp:
            if resp.status == 401:
                _LOGGER.debug("Widgets request returned 401, refreshing access token and retrying")
                await self.login()
                return await self.get_widgets()
            _LOGGER.debug("Widgets request completed with status %s", resp.status)
            if resp.status >= 400:
                _LOGGER.debug("Widgets request failed with body: %s", await resp.text())
            resp.raise_for_status()
            data = await resp.json()
            widgets = data.get("data")
            if isinstance(widgets, list):
                summary_items: list[str] = []
                for widget in widgets:
                    if not isinstance(widget, dict):
                        continue
                    widget_type = widget.get("widget") or "UNKNOWN"
                    number = widget.get("number")
                    values = widget.get("values")
                    name: Optional[str] = None
                    if isinstance(values, dict):
                        name = values.get("name")
                    descriptor = widget_type
                    if number:
                        descriptor = f"{descriptor}#{number}"
                    if name:
                        descriptor = f"{descriptor} ({name})"
                    summary_items.append(descriptor)

                if summary_items:
                    _LOGGER.debug(
                        "Widgets payload includes %d widgets: %s",
                        len(summary_items),
                        ", ".join(summary_items),
                    )

            meta = data.get("meta")
            if isinstance(meta, dict):
                _LOGGER.debug(
                    "Widgets metadata: refresh=%s, timestamp=%s, online_state=%s",
                    meta.get("refresh"),
                    meta.get("current_timestamp"),
                    meta.get("online_state"),
                )
            _LOGGER.debug("Widgets API response: %s", data)
            return data
