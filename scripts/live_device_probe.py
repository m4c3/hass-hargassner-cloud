#!/usr/bin/env python3
"""Probe read-only device metadata without printing private API values."""

from __future__ import annotations

import asyncio
import os
import re
from getpass import getpass

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError

from custom_components.hargassner_cloud.api import (
    DEVICE_METADATA_RELATIONS,
    HargassnerAuthError,
    HargassnerClient,
    HargassnerConnectionError,
)
from custom_components.hargassner_cloud.const import DEFAULT_BASE_URL

VERSION_FIELD_PATTERN = re.compile(
    r"(?:firmware|software|version|revision|build)", re.IGNORECASE
)
SAFE_VERSION_PATTERN = re.compile(r"[A-Za-z0-9._+ -]{1,64}")


def _value_type(value: object) -> str:
    """Return a stable JSON value type without exposing the value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def version_field_types(value: object, path: str = "response") -> list[str]:
    """List version-related field paths and types, never their values."""
    fields: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if VERSION_FIELD_PATTERN.search(str(key)):
                fields.append(f"{child_path}: {_value_type(child)}")
            fields.extend(version_field_types(child, child_path))
    elif isinstance(value, list) and value:
        fields.extend(version_field_types(value[0], f"{path}[]"))
    return sorted(set(fields))


def safe_version_candidates(value: object, path: str = "response") -> list[str]:
    """Return allowlisted version-code values with their structural paths."""
    candidates: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if (
                key == "version_code"
                and isinstance(child, (int, str))
                and SAFE_VERSION_PATTERN.fullmatch(str(child))
            ):
                candidates.append(f"{child_path}: {child}")
            candidates.extend(safe_version_candidates(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value, start=1):
            candidates.extend(safe_version_candidates(child, f"{path}[{index}]"))
    return candidates


async def async_main() -> int:
    """Authenticate and inspect read-only installation device metadata."""
    username = (
        os.environ.get("HARGASSNER_USERNAME") or input("Hargassner email: ").strip()
    )
    password = os.environ.get("HARGASSNER_PASSWORD") or getpass("Hargassner password: ")
    if not username or not password:
        print("ERROR: Email and password are required.")
        return 2

    async with ClientSession() as session:
        client = HargassnerClient(
            session=session,
            base_url=DEFAULT_BASE_URL,
            username=username,
            password=password,
            client_id=None,
            client_secret=None,
            installation="",
        )
        try:
            await client.login()
            installations = await client.get_installations()
        except HargassnerAuthError:
            print("AUTH ERROR: Login or token authorization was rejected.")
            return 1
        except HargassnerConnectionError:
            print("API ERROR: Login or installation discovery failed.")
            return 1

        if not client._token:
            print("API ERROR: Login succeeded without an access token.")
            return 1

        print(f"OK: Found {len(installations)} installation(s).")
        for number, installation in enumerate(installations, start=1):
            url = f"{DEFAULT_BASE_URL}/api/installations/{installation['id']}"
            try:
                async with session.get(
                    url,
                    params={"with": DEVICE_METADATA_RELATIONS},
                    headers={
                        "Authorization": f"Bearer {client._token}",
                        "Accept": "application/json",
                    },
                    timeout=ClientTimeout(total=20),
                ) as response:
                    print(f"- Installation {number}: HTTP {response.status}")
                    if response.status >= 400:
                        continue
                    try:
                        payload = await response.json()
                    except (ContentTypeError, TypeError, ValueError):
                        print("  Response was not JSON; content omitted.")
                        continue
            except (ClientError, TimeoutError):
                print("  Connection failed; details omitted.")
                continue

            candidates = safe_version_candidates(payload)
            fields = version_field_types(payload)
            print("  Safe version candidates:")
            if candidates:
                for candidate in candidates:
                    print(f"    {candidate}")
            else:
                print("    none")
            print("  Version-related field paths and types:")
            if fields:
                for field in fields:
                    print(f"    {field}")
            else:
                print("    none")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
