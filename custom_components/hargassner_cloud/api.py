from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError

_LOGGER = logging.getLogger(__name__)


class HargassnerAuthError(Exception):
    """Raised when authentication credentials are rejected."""


class HargassnerConnectionError(Exception):
    """Raised when the cloud API cannot be reached or returns invalid data."""


class HargassnerClient:
    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        username: str,
        password: str,
        client_secret: str | None,
        installation: str,
        client_id: str | None = None,
    ):
        self._session = session
        self._base = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._client_secret = client_secret or ""
        self._client_id = client_id
        self._installation = str(installation).strip()
        self._token: str | None = None

    async def login(self) -> None:
        """Discover the public web-client credentials and log in."""
        if await self._async_refresh_client_credentials():
            await self._login_once()
            return
        if not self._client_secret:
            raise HargassnerConnectionError(
                "Unable to discover Hargassner web-client credentials"
            )
        await self._login_once()

    async def _login_once(self) -> None:
        """Log in once with the currently configured client credentials."""
        url = f"{self._base}/api/auth/login"
        _LOGGER.debug(
            "Starting login at %s for user=%s (client_id=%s)",
            url,
            self._username,
            self._client_id,
        )

        payload_candidates = [
            {
                "email": self._username,
                "password": self._password,
                "client_secret": self._client_secret,
            },
            {
                "username": self._username,
                "password": self._password,
                "client_secret": self._client_secret,
            },
        ]
        if self._client_id:
            payload_candidates.insert(
                0,
                {
                    "email": self._username,
                    "password": self._password,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
            payload_candidates.append(
                {
                    "username": self._username,
                    "password": self._password,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                }
            )

        last_error_txt = ""
        auth_rejected = False
        for payload in payload_candidates:
            safe = payload.copy()
            safe["password"] = "***"
            if "client_secret" in safe:
                safe["client_secret"] = "***"
            _LOGGER.debug("→ POST %s payload=%s", url, safe)
            try:
                async with self._session.post(
                    url, json=payload, headers={"Accept": "application/json"}
                ) as resp:
                    text = await resp.text()
                    _LOGGER.debug("← Login response %s: %s", resp.status, text[:800])
                    if resp.status >= 400:
                        last_error_txt = f"{resp.status} {text[:200]}"
                        auth_rejected |= resp.status in (401, 403)
                        continue
                    try:
                        js = await resp.json()
                    except (ContentTypeError, TypeError, ValueError):
                        last_error_txt = f"Non-JSON login response: {text[:200]}"
                        continue
                    token = (
                        js.get("access_token")
                        or (js.get("data") or {}).get("access_token")
                        or js.get("token")
                    )
                    if token:
                        _LOGGER.debug("✓ Login succeeded")
                        self._token = token
                        return
                    last_error_txt = f"Login JSON had no token: keys={list(js.keys())}"
            except (ClientError, TimeoutError) as exc:
                last_error_txt = f"Exception: {exc}"
                _LOGGER.debug("Login connection error: %s", last_error_txt)

        if auth_rejected:
            raise HargassnerAuthError(f"Login failed. Last error: {last_error_txt}")
        raise HargassnerConnectionError(f"Login failed. Last error: {last_error_txt}")

    async def _async_refresh_client_credentials(self) -> bool:
        """Extract rotated public client credentials from the live web bundle."""
        try:
            async with self._session.get(
                f"{self._base}/login", timeout=ClientTimeout(total=15)
            ) as response:
                html = await response.text()
                if response.status >= 400:
                    return False

            script_match = re.search(
                r'<script[^>]+src=["\']([^"\']*?/build/assets/app-[^"\']+\.js)["\']',
                html,
            )
            if not script_match:
                return False

            bundle_url = urljoin(f"{self._base}/", script_match.group(1))
            async with self._session.get(
                bundle_url, timeout=ClientTimeout(total=20)
            ) as response:
                bundle = await response.text()
                if response.status >= 400:
                    return False

            anchor = re.search(r"client_id:(\w+),client_secret:(\w+)", bundle)
            if not anchor:
                return False

            def resolve(variable: str) -> str | None:
                match = re.search(
                    rf"(?:^|[,;]|\b(?:const|let|var)\s+){re.escape(variable)}="
                    r"[\"']([^\"']+)[\"']",
                    bundle,
                )
                return match.group(1) if match else None

            client_id = resolve(anchor.group(1))
            client_secret = resolve(anchor.group(2))
            if not client_id or not client_secret:
                return False
            if client_id == self._client_id and client_secret == self._client_secret:
                return False

            self._client_id = client_id
            self._client_secret = client_secret
            _LOGGER.info("Updated public Hargassner web-client credentials")
            return True
        except (ClientError, TimeoutError):
            return False

    async def get_widgets(self) -> dict[str, Any]:
        """
        Retrieve widgets for installation:
          1) /api/installations/<id>/widgets  (primär)
          2) /api/widgets?installationId=<id> (Fallback)
        """
        if not self._token:
            await self.login()
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        timeout = ClientTimeout(total=15)  # per-request cap
        relogin_done = False

        urls = [
            f"{self._base}/api/installations/{self._installation}/widgets",
            f"{self._base}/api/widgets?installationId={self._installation}",
        ]
        last_err = ""
        for url in urls:
            _LOGGER.debug("GET %s", url)
            for attempt in range(2):
                try:
                    async with self._session.get(
                        url, headers=headers, timeout=timeout
                    ) as resp:
                        text = await resp.text()
                        _LOGGER.debug(
                            "Widgets response %s: %s", resp.status, text[:1200]
                        )
                        if resp.status in (401, 403):
                            if relogin_done or attempt == 1:
                                raise HargassnerAuthError(
                                    "Widgets request rejected after re-login"
                                )
                            _LOGGER.debug(
                                "Token expired/invalid; re-login and retry same endpoint"
                            )
                            await self.login()
                            headers["Authorization"] = f"Bearer {self._token}"
                            relogin_done = True
                            await asyncio.sleep(0.5)
                            continue
                        if resp.status >= 400:
                            last_err = f"{resp.status} {text[:200]}"
                            break
                        try:
                            return await resp.json()
                        except (TypeError, ValueError):
                            last_err = f"Non-JSON widgets response: {text[:200]}"
                            break
                except HargassnerAuthError:
                    raise
                except (ClientError, TimeoutError) as exc:
                    last_err = f"{type(exc).__name__}: {exc}"
                    _LOGGER.debug("Widgets exception at %s: %s", url, last_err)
                    break

        raise HargassnerConnectionError(f"Widgets fetch failed. Last error: {last_err}")

    async def get_installations(self) -> list[dict[str, str]]:
        """Return installations available to the authenticated account."""
        if not self._token:
            await self.login()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        for path in ("/api/installations", "/api/user/installations"):
            url = f"{self._base}{path}"
            for attempt in range(2):
                try:
                    async with self._session.get(
                        url, headers=headers, timeout=ClientTimeout(total=15)
                    ) as response:
                        text = await response.text()
                        if response.status in (401, 403):
                            if attempt == 1:
                                raise HargassnerAuthError(
                                    "Installation discovery rejected after re-login"
                                )
                            await self.login()
                            headers["Authorization"] = f"Bearer {self._token}"
                            continue
                        if response.status == 404:
                            break
                        if response.status >= 400:
                            raise HargassnerConnectionError(
                                f"Installation discovery failed: {response.status} "
                                f"{text[:200]}"
                            )
                        try:
                            payload = await response.json()
                        except (ContentTypeError, TypeError, ValueError) as err:
                            raise HargassnerConnectionError(
                                "Installation discovery returned invalid JSON"
                            ) from err
                        installations = self._parse_installations(payload)
                        if installations:
                            return installations
                        break
                except HargassnerAuthError:
                    raise
                except HargassnerConnectionError:
                    raise
                except (ClientError, TimeoutError) as err:
                    raise HargassnerConnectionError(
                        f"Installation discovery failed: {err}"
                    ) from err

        raise HargassnerConnectionError(
            "No Hargassner installations were found for this account"
        )

    @staticmethod
    def _parse_installations(payload: Any) -> list[dict[str, str]]:
        """Normalize installation list responses from supported endpoints."""
        items = payload
        if isinstance(payload, dict):
            items = payload.get("data", payload.get("installations", []))
        if not isinstance(items, list):
            return []
        return [
            {
                "id": str(item["id"]),
                "name": str(item.get("name") or f"Installation {item['id']}"),
            }
            for item in items
            if isinstance(item, dict) and item.get("id") is not None
        ]
