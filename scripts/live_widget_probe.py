#!/usr/bin/env python3
"""Probe current widget values for local, private analysis."""

from __future__ import annotations

import asyncio
import json
import os
import re
from getpass import getpass
from typing import Any

from aiohttp import ClientSession

from custom_components.hargassner_cloud.api import (
    HargassnerAuthError,
    HargassnerClient,
    HargassnerClientCredentialsError,
    HargassnerConnectionError,
)
from custom_components.hargassner_cloud.const import DEFAULT_BASE_URL

REDACTED = "**REDACTED**"
PRIVATE_VALUE_PATTERN = re.compile(
    r"(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.IGNORECASE,
)
PRIVATE_KEYS = {
    "accesstoken",
    "customerid",
    "deviceid",
    "email",
    "gatewayid",
    "id",
    "installationid",
    "location",
    "name",
    "password",
    "refreshtoken",
    "serialnumber",
    "token",
    "username",
}


def _normalized_key(key: object) -> str:
    """Normalize snake_case and camelCase keys for privacy checks."""
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def sanitize_widget_payload(value: Any) -> Any:
    """Redact credentials, stable identifiers, and user-defined names."""
    if isinstance(value, dict):
        return {
            str(key): (
                REDACTED
                if _normalized_key(key) in PRIVATE_KEYS
                else sanitize_widget_payload(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [sanitize_widget_payload(child) for child in value]
    if isinstance(value, str) and PRIVATE_VALUE_PATTERN.search(value):
        return REDACTED
    return value


async def async_main() -> int:
    """Authenticate and print redacted current widget responses."""
    username = (
        os.environ.get("HARGASSNER_USERNAME") or input("Hargassner email: ").strip()
    )
    password = os.environ.get("HARGASSNER_PASSWORD") or getpass("Hargassner password: ")
    if not username or not password:
        print("ERROR: Email and password are required.")
        return 2

    print("WARNING: Output contains real heating values; keep it private.")
    async with ClientSession() as session:
        discovery_client = HargassnerClient(
            session=session,
            base_url=DEFAULT_BASE_URL,
            username=username,
            password=password,
            client_id=None,
            client_secret=None,
            installation="",
        )
        try:
            await discovery_client.login()
            installations = await discovery_client.get_installations()
        except (HargassnerAuthError, HargassnerClientCredentialsError):
            print("AUTH ERROR: Login or public web-client authorization failed.")
            return 1
        except HargassnerConnectionError:
            print("API ERROR: Login or installation discovery failed.")
            return 1

        print(f"OK: Found {len(installations)} installation(s).")
        for number, installation in enumerate(installations, start=1):
            client = HargassnerClient(
                session=session,
                base_url=DEFAULT_BASE_URL,
                username=username,
                password=password,
                client_id=None,
                client_secret=None,
                installation=installation["id"],
            )
            try:
                payload = await client.get_widgets()
            except (HargassnerAuthError, HargassnerClientCredentialsError):
                print(f"- Installation {number}: authentication failed")
                continue
            except HargassnerConnectionError:
                print(f"- Installation {number}: widget request failed")
                continue

            print(f"- Installation {number}: widgets")
            rendered = json.dumps(
                sanitize_widget_payload(payload),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            for line in rendered.splitlines():
                print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
