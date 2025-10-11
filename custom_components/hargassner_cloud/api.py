from __future__ import annotations

from typing import Any, Optional
from aiohttp import ClientSession, ClientResponseError, ClientTimeout
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class HargassnerAuthError(Exception):
    """Raised when authentication or widget fetch fails in a recoverable way."""
    pass


class HargassnerClient:
    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        username: str,
        password: str,
        client_secret: str,
        installation: str,
        client_id: str | None = None,
    ):
        self._session = session
        self._base = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._client_secret = client_secret
        self._client_id = client_id
        self._installation = str(installation).strip()
        self._token: Optional[str] = None

    async def login(self) -> None:
        """Log in and acquire access token. Uses only /api/auth/login with email/username variants."""
        url = f"{self._base}/api/auth/login"
        _LOGGER.debug("Starting login at %s for user=%s (client_id=%s)", url, self._username, self._client_id)

        payload_candidates = [
            {"email": self._username, "password": self._password, "client_secret": self._client_secret},
            {"username": self._username, "password": self._password, "client_secret": self._client_secret},
        ]
        if self._client_id:
            payload_candidates.insert(0, {"email": self._username, "password": self._password, "client_id": self._client_id, "client_secret": self._client_secret})
            payload_candidates.append({"username": self._username, "password": self._password, "client_id": self._client_id, "client_secret": self._client_secret})

        last_error_txt = ""
        for payload in payload_candidates:
            safe = payload.copy()
            safe["password"] = "***"
            if "client_secret" in safe:
                safe["client_secret"] = "***"
            _LOGGER.debug("→ POST %s payload=%s", url, safe)
            try:
                async with self._session.post(url, json=payload, headers={"Accept": "application/json"}) as resp:
                    text = await resp.text()
                    _LOGGER.debug("← Login response %s: %s", resp.status, text[:800])
                    if resp.status >= 400:
                        last_error_txt = f"{resp.status} {text[:200]}"
                        continue
                    try:
                        js = await resp.json()
                    except Exception:
                        last_error_txt = f"Non-JSON login response: {text[:200]}"
                        continue
                    token = js.get("access_token") or (js.get("data") or {}).get("access_token") or js.get("token")
                    if token:
                        _LOGGER.debug("✓ Login succeeded")
                        self._token = token
                        return
                    last_error_txt = f"Login JSON had no token: keys={list(js.keys())}"
            except ClientResponseError as cre:
                last_error_txt = f"HTTP error: {cre.status}"
                _LOGGER.warning("Login ClientResponseError: %s", last_error_txt)
            except Exception as exc:
                last_error_txt = f"Exception: {exc}"
                _LOGGER.warning("Login exception: %s", last_error_txt)

        raise HargassnerAuthError(f"Login failed. Last error: {last_error_txt}")

    async def get_widgets(self) -> dict[str, Any]:
        """
        Retrieve widgets for installation:
          1) /api/installations/<id>/widgets  (primär)
          2) /api/widgets?installationId=<id> (Fallback)
        """
        if not self._token:
            await self.login()
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        timeout = ClientTimeout(total=15)  # per-request cap
        relogin_done = False

        urls = [
            f"{self._base}/api/installations/{self._installation}/widgets",
            f"{self._base}/api/widgets?installationId={self._installation}",
        ]
        last_err = ""
        for url in urls:
            _LOGGER.debug("GET %s", url)
            try:
                async with self._session.get(url, headers=headers, timeout=timeout) as resp:
                    text = await resp.text()
                    _LOGGER.debug("Widgets response %s: %s", resp.status, text[:1200])
                    if resp.status == 401 and not relogin_done:
                        _LOGGER.warning("Token expired/invalid. Re-login (single retry)…")
                        await self.login()
                        headers["Authorization"] = f"Bearer {self._token}"
                        relogin_done = True
                        await asyncio.sleep(0.5)
                        continue
                    if resp.status >= 400:
                        last_err = f"{resp.status} {text[:200]}"
                        continue
                    try:
                        return await resp.json()
                    except Exception:
                        last_err = f"Non-JSON widgets response: {text[:200]}"
                        continue
            except Exception as exc:
                last_err = f"{type(exc).__name__}: {exc}"
                _LOGGER.debug("Widgets exception at %s: %s", url, last_err)
                continue

        raise HargassnerAuthError(f"Widgets fetch failed. Last error: {last_err}")
