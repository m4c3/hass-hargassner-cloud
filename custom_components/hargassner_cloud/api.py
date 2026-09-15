from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError

_LOGGER = logging.getLogger(__name__)

DEVICE_METADATA_RELATIONS = (
    "devices.gateway;devices.gateway.software;devices.software;devices.software.type"
)
SAFE_VERSION_PATTERN = re.compile(r"[A-Za-z0-9._+ -]{1,64}")


class HargassnerAuthError(Exception):
    """Raised when authentication credentials are rejected."""


class HargassnerConnectionError(Exception):
    """Raised when the cloud API cannot be reached or returns invalid data."""


class HargassnerMaintenanceError(HargassnerConnectionError):
    """Raised when Hargassner explicitly reports scheduled maintenance."""


class HargassnerClientCredentialsError(Exception):
    """Raised when public Hargassner web-client credentials are unavailable."""


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
        self._diagnostics: dict[str, str | int | None] = {
            "phase": "not_started",
            "outcome": None,
            "http_status": None,
            "credential_source": "unknown",
            "error_type": None,
        }

    @property
    def diagnostics(self) -> dict[str, str | int | None]:
        """Return structured diagnostics without credentials or response values."""
        return dict(self._diagnostics)

    def _record_diagnostic(
        self,
        phase: str,
        outcome: str,
        *,
        http_status: int | None = None,
        error_type: str | None = None,
    ) -> None:
        """Record the latest API operation in a safe, bounded form."""
        self._diagnostics.update(
            {
                "phase": phase,
                "outcome": outcome,
                "http_status": http_status,
                "error_type": error_type,
            }
        )

    async def login(self) -> None:
        """Discover the public web-client credentials and log in."""
        credentials_discovered = await self._async_refresh_client_credentials()
        if credentials_discovered:
            self._diagnostics["credential_source"] = "live_bundle"
            await self._login_once()
            return
        if not self._client_secret:
            self._diagnostics["credential_source"] = "unavailable"
            self._record_diagnostic("client_credentials", "failed")
            raise HargassnerClientCredentialsError(
                "Unable to discover Hargassner web-client credentials"
            )
        self._diagnostics["credential_source"] = "stored_legacy"
        try:
            await self._login_once()
        except HargassnerAuthError as err:
            raise HargassnerClientCredentialsError(
                "Stored Hargassner web-client credentials were rejected"
            ) from err

    async def _login_once(self) -> None:
        """Log in once with the currently configured client credentials."""
        url = f"{self._base}/api/auth/login"
        _LOGGER.debug("Starting Hargassner login")

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
        for attempt, payload in enumerate(payload_candidates, start=1):
            _LOGGER.debug("Sending Hargassner login attempt %s", attempt)
            try:
                async with self._session.post(
                    url, json=payload, headers={"Accept": "application/json"}
                ) as resp:
                    _LOGGER.debug("Hargassner login response status: %s", resp.status)
                    if resp.status >= 400:
                        last_error_txt = f"HTTP {resp.status}"
                        self._record_diagnostic(
                            "login", "failed", http_status=resp.status
                        )
                        auth_rejected |= resp.status in (401, 403)
                        continue
                    try:
                        js = await resp.json()
                    except (ContentTypeError, TypeError, ValueError):
                        last_error_txt = "Non-JSON login response"
                        self._record_diagnostic(
                            "login", "invalid_response", http_status=resp.status
                        )
                        continue
                    token = (
                        js.get("access_token")
                        or (js.get("data") or {}).get("access_token")
                        or js.get("token")
                    )
                    if token:
                        _LOGGER.debug("✓ Login succeeded")
                        self._token = token
                        self._record_diagnostic(
                            "login", "success", http_status=resp.status
                        )
                        return
                    last_error_txt = f"Login JSON had no token: keys={list(js.keys())}"
            except (ClientError, TimeoutError) as exc:
                last_error_txt = f"Exception: {exc}"
                self._record_diagnostic(
                    "login", "failed", error_type=type(exc).__name__
                )
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
                    self._record_diagnostic(
                        "login_page", "failed", http_status=response.status
                    )
                    return False

            script_match = re.search(
                r'<script[^>]+src=["\']([^"\']*?/build/assets/app-[^"\']+\.js)["\']',
                html,
            )
            if not script_match:
                if re.search(
                    r"<title[^>]*>[^<]*(?:wartungsarbeiten|maintenance)[^<]*</title>",
                    html,
                    flags=re.IGNORECASE,
                ):
                    self._diagnostics["credential_source"] = "unavailable"
                    self._record_diagnostic(
                        "login_page", "maintenance", http_status=response.status
                    )
                    raise HargassnerMaintenanceError(
                        "Hargassner Cloud is temporarily unavailable for maintenance"
                    )
                self._record_diagnostic("login_page", "script_not_found")
                return False

            bundle_url = urljoin(f"{self._base}/", script_match.group(1))
            async with self._session.get(
                bundle_url, timeout=ClientTimeout(total=20)
            ) as response:
                bundle = await response.text()
                if response.status >= 400:
                    self._record_diagnostic(
                        "web_bundle", "failed", http_status=response.status
                    )
                    return False

            anchor = re.search(r"client_id:(\w+),client_secret:(\w+)", bundle)
            if not anchor:
                self._record_diagnostic("web_bundle", "credential_anchor_not_found")
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
                self._record_diagnostic("web_bundle", "credential_values_not_found")
                return False
            if client_id == self._client_id and client_secret == self._client_secret:
                self._record_diagnostic("web_bundle", "success")
                return True

            self._client_id = client_id
            self._client_secret = client_secret
            _LOGGER.info("Updated public Hargassner web-client credentials")
            self._record_diagnostic("web_bundle", "success")
            return True
        except (ClientError, TimeoutError) as err:
            self._record_diagnostic(
                "client_credentials", "failed", error_type=type(err).__name__
            )
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
        for endpoint_number, url in enumerate(urls, start=1):
            _LOGGER.debug("Requesting widgets endpoint %s", endpoint_number)
            for attempt in range(2):
                try:
                    async with self._session.get(
                        url, headers=headers, timeout=timeout
                    ) as resp:
                        _LOGGER.debug("Widgets response status: %s", resp.status)
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
                            last_err = f"HTTP {resp.status}"
                            self._record_diagnostic(
                                "widgets", "failed", http_status=resp.status
                            )
                            break
                        try:
                            result = await resp.json()
                            self._record_diagnostic(
                                "widgets", "success", http_status=resp.status
                            )
                            return result
                        except (TypeError, ValueError):
                            last_err = "Non-JSON widgets response"
                            self._record_diagnostic(
                                "widgets", "invalid_response", http_status=resp.status
                            )
                            break
                except HargassnerAuthError:
                    raise
                except (ClientError, TimeoutError) as exc:
                    last_err = f"{type(exc).__name__}: {exc}"
                    self._record_diagnostic(
                        "widgets", "failed", error_type=type(exc).__name__
                    )
                    _LOGGER.debug("Widgets request failed: %s", type(exc).__name__)
                    break

        raise HargassnerConnectionError(f"Widgets fetch failed. Last error: {last_err}")

    async def get_device_metadata(self) -> dict[str, str]:
        """Return allowlisted device version metadata for the installation."""
        if not self._token:
            await self.login()

        url = f"{self._base}/api/installations/{self._installation}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        for attempt in range(2):
            try:
                async with self._session.get(
                    url,
                    params={"with": DEVICE_METADATA_RELATIONS},
                    headers=headers,
                    timeout=ClientTimeout(total=20),
                ) as response:
                    _LOGGER.debug(
                        "Device metadata response status: %s", response.status
                    )
                    if response.status == 401:
                        if attempt == 1:
                            return {}
                        await self.login()
                        headers["Authorization"] = f"Bearer {self._token}"
                        continue
                    if response.status in (403, 404):
                        return {}
                    if response.status >= 400:
                        raise HargassnerConnectionError(
                            f"Device metadata request failed: HTTP {response.status}"
                        )
                    try:
                        payload = await response.json()
                    except (ContentTypeError, TypeError, ValueError) as err:
                        raise HargassnerConnectionError(
                            "Device metadata request returned invalid JSON"
                        ) from err
                    return self._parse_device_metadata(payload)
            except HargassnerConnectionError:
                raise
            except (ClientError, TimeoutError) as err:
                raise HargassnerConnectionError(
                    "Device metadata request failed"
                ) from err
        return {}

    @staticmethod
    def _parse_device_metadata(payload: object) -> dict[str, str]:
        """Extract only non-sensitive version fields from installation details."""
        root = payload.get("data") if isinstance(payload, dict) else None
        devices = root.get("devices") if isinstance(root, dict) else None
        if not isinstance(devices, list):
            return {}

        for device in devices:
            if not isinstance(device, dict):
                continue
            metadata: dict[str, str] = {}
            software = device.get("software")
            version = (
                software.get("version_code") if isinstance(software, dict) else None
            )
            if isinstance(version, (int, str)) and SAFE_VERSION_PATTERN.fullmatch(
                str(version)
            ):
                metadata["software_version"] = str(version)
            io_version = device.get("io_firmware_version")
            if isinstance(io_version, (int, str)) and SAFE_VERSION_PATTERN.fullmatch(
                str(io_version)
            ):
                metadata["io_firmware_version"] = str(io_version)
            if metadata:
                return metadata
        return {}

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
                            self._record_diagnostic(
                                "installations", "failed", http_status=response.status
                            )
                            raise HargassnerConnectionError(
                                f"Installation discovery failed: HTTP {response.status}"
                            )
                        try:
                            payload = await response.json()
                        except (ContentTypeError, TypeError, ValueError) as err:
                            raise HargassnerConnectionError(
                                "Installation discovery returned invalid JSON"
                            ) from err
                        installations = self._parse_installations(payload)
                        if installations:
                            self._record_diagnostic(
                                "installations", "success", http_status=response.status
                            )
                            return installations
                        break
                except HargassnerAuthError:
                    raise
                except HargassnerConnectionError:
                    raise
                except (ClientError, TimeoutError) as err:
                    self._record_diagnostic(
                        "installations", "failed", error_type=type(err).__name__
                    )
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
