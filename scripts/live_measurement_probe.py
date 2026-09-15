#!/usr/bin/env python3
"""Probe read-only heating measurements for local, private analysis."""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import UTC, datetime, timedelta
from getpass import getpass
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError

from custom_components.hargassner_cloud.api import (
    DEVICE_METADATA_RELATIONS,
    HargassnerAuthError,
    HargassnerClient,
    HargassnerConnectionError,
)
from custom_components.hargassner_cloud.const import DEFAULT_BASE_URL

REDACTED = "**REDACTED**"
PRIVATE_KEY_PATTERN = re.compile(
    r"(?:^|_)(?:access_?token|refresh_?token|token|password|secret|email|username|"
    r"serial(?:_number)?|installation_?id|device_?id|gateway_?id|customer_?id|id)$",
    re.IGNORECASE,
)
PRIVATE_VALUE_PATTERN = re.compile(
    r"(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.IGNORECASE,
)
DEVICE_ENDPOINTS = ("metric-fields", "fetch-metrics")


def _is_private_key(key: object) -> bool:
    """Recognize snake_case and camelCase private response fields."""
    text = str(key)
    normalized = re.sub(r"[^a-z0-9]", "", text.lower())
    return bool(PRIVATE_KEY_PATTERN.search(text)) or normalized in {
        "accesstoken",
        "refreshtoken",
        "installationid",
        "deviceid",
        "gatewayid",
        "customerid",
        "serialnumber",
    }


def sanitize_measurement_payload(value: Any) -> Any:
    """Remove credentials and stable identifiers while retaining measurements."""
    if isinstance(value, dict):
        return {
            str(key): (
                REDACTED
                if _is_private_key(key)
                else sanitize_measurement_payload(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [sanitize_measurement_payload(child) for child in value]
    if isinstance(value, str) and PRIVATE_VALUE_PATTERN.search(value):
        return REDACTED
    return value


def active_metric_definitions(payload: Any) -> list[dict[str, Any]]:
    """Extract active metric definitions while retaining IDs only internally."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []
    definitions: list[dict[str, Any]] = []
    for group in data:
        fields = group.get("fields") if isinstance(group, dict) else None
        if not isinstance(fields, list):
            continue
        for field in fields:
            if isinstance(field, dict) and field.get("id") is not None:
                definitions.append(
                    {
                        **field,
                        "_group": group.get("text") or group.get("type"),
                    }
                )
    return definitions


def latest_measurements(
    definitions: list[dict[str, Any]], payload: Any
) -> list[dict[str, Any]]:
    """Map opaque channel IDs to safe labels and their latest available values."""
    samples = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(samples, list):
        return []
    results: list[dict[str, Any]] = []
    for definition in definitions:
        channel_id = definition.get("id")
        latest: Any = None
        found = False
        for sample in reversed(samples):
            values = sample.get("values") if isinstance(sample, dict) else None
            if isinstance(values, dict):
                value_key = next(
                    (key for key in values if str(key) == str(channel_id)), None
                )
                if value_key is not None:
                    latest = values[value_key]
                    if latest is not None:
                        found = True
                        break
        results.append(
            {
                "group": definition.get("_group"),
                "name": definition.get("legend") or definition.get("text"),
                "unit": definition.get("unit") or None,
                "value": latest if found else None,
            }
        )
    return results


async def _get_json(
    session: ClientSession,
    token: str,
    url: str,
    *,
    params: dict[str, str] | None = None,
) -> tuple[int, Any | None]:
    """Fetch one read-only JSON endpoint."""
    async with session.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=ClientTimeout(total=30),
    ) as response:
        if response.status >= 400:
            return response.status, None
        try:
            return response.status, await response.json()
        except (ContentTypeError, TypeError, ValueError):
            return response.status, None


async def async_main() -> int:
    """Authenticate and print redacted measurement responses."""
    username = (
        os.environ.get("HARGASSNER_USERNAME") or input("Hargassner email: ").strip()
    )
    password = os.environ.get("HARGASSNER_PASSWORD") or getpass("Hargassner password: ")
    if not username or not password:
        print("ERROR: Email and password are required.")
        return 2

    print("WARNING: Output contains real heating measurements; keep it private.")
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

        token = client._token
        if not token:
            print("API ERROR: Login succeeded without an access token.")
            return 1

        print(f"OK: Found {len(installations)} installation(s).")
        for installation_number, installation in enumerate(installations, start=1):
            detail_url = f"{DEFAULT_BASE_URL}/api/installations/{installation['id']}"
            try:
                status, detail = await _get_json(
                    session,
                    token,
                    detail_url,
                    params={"with": DEVICE_METADATA_RELATIONS},
                )
            except (ClientError, TimeoutError):
                print(f"- Installation {installation_number}: connection failed")
                continue

            data = detail.get("data") if isinstance(detail, dict) else None
            devices = data.get("devices") if isinstance(data, dict) else None
            if status >= 400 or not isinstance(devices, list):
                print(
                    f"- Installation {installation_number}: HTTP {status}, no devices"
                )
                continue

            print(f"- Installation {installation_number}: {len(devices)} device(s)")
            for device_number, device in enumerate(devices, start=1):
                device_id = device.get("id") if isinstance(device, dict) else None
                if not device_id:
                    print(f"  Device {device_number}: missing internal ID")
                    continue
                print(f"  Device {device_number}:")
                definitions: list[dict[str, Any]] = []
                for endpoint in DEVICE_ENDPOINTS:
                    url = f"{DEFAULT_BASE_URL}/api/devices/{device_id}/{endpoint}"
                    try:
                        endpoint_status, payload = await _get_json(session, token, url)
                    except (ClientError, TimeoutError):
                        print(f"    {endpoint}: connection failed")
                        continue
                    print(f"    {endpoint}: HTTP {endpoint_status}")
                    if payload is not None:
                        if endpoint == "metric-fields":
                            definitions = active_metric_definitions(payload)
                        rendered = json.dumps(
                            sanitize_measurement_payload(payload),
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True,
                        )
                        for line in rendered.splitlines():
                            print(f"      {line}")
                if not definitions:
                    print("    measurements: skipped (no active channels)")
                    continue
                now = datetime.now(UTC)
                params = {
                    "channels": ";".join(str(item["id"]) for item in definitions),
                    "from": (now - timedelta(days=1)).isoformat(),
                    "to": (now + timedelta(minutes=5)).isoformat(),
                }
                measurements_url = (
                    f"{DEFAULT_BASE_URL}/api/devices/{device_id}/measurements"
                )
                try:
                    measurement_status, measurement_payload = await _get_json(
                        session, token, measurements_url, params=params
                    )
                except (ClientError, TimeoutError):
                    print("    measurements: connection failed")
                    continue
                print(f"    measurements: HTTP {measurement_status}")
                if measurement_payload is not None:
                    rendered = json.dumps(
                        latest_measurements(definitions, measurement_payload),
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    )
                    for line in rendered.splitlines():
                        print(f"      {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
