#!/usr/bin/env python3
"""Run a minimal live API check without printing credentials or payload values."""

from __future__ import annotations

import asyncio
from getpass import getpass

from aiohttp import ClientSession

from custom_components.hargassner_cloud.api import (
    HargassnerAuthError,
    HargassnerClient,
    HargassnerConnectionError,
)
from custom_components.hargassner_cloud.const import (
    DEFAULT_BASE_URL,
)


async def async_main() -> int:
    """Authenticate, discover installations, and fetch one widget response."""
    username = input("Hargassner email: ").strip()
    password = getpass("Hargassner password: ")
    if not username or not password:
        print("ERROR: Email and password are required.")
        return 2

    async with ClientSession() as session:
        client = HargassnerClient(
            session=session,
            base_url=DEFAULT_BASE_URL,
            username=username,
            password=password,
            # Deliberately invalid: a successful login proves that the client can
            # discover the current public web-client credentials automatically.
            client_id="smoke-test-invalid",
            client_secret="smoke-test-invalid",
            installation="",
        )
        try:
            await client.login()
            installations = await client.get_installations()
            print(
                "OK: Login succeeded after automatic web-client credential discovery."
            )
            print(f"OK: Found {len(installations)} installation(s).")
            for number, installation in enumerate(installations, start=1):
                print(f"- Installation {number}: {installation['name']}")

            client._installation = installations[0]["id"]
            widgets = await client.get_widgets()
        except HargassnerAuthError:
            print("AUTH ERROR: Login or token authorization was rejected.")
            return 1
        except HargassnerConnectionError:
            print("API ERROR: The cloud request failed or returned unexpected data.")
            return 1

    keys = sorted(str(key) for key in widgets)
    print(f"OK: Widget response received with {len(keys)} top-level key(s).")
    print("Keys: " + ", ".join(keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
