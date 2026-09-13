from __future__ import annotations

import asyncio
import os

import pytest
from aiohttp import ClientSession

from custom_components.hargassner_cloud.api import HargassnerClient
from custom_components.hargassner_cloud.const import DEFAULT_BASE_URL

USERNAME = os.environ.get("HARGASSNER_USERNAME")
PASSWORD = os.environ.get("HARGASSNER_PASSWORD")

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not USERNAME or not PASSWORD,
        reason="real Hargassner credentials were not provided",
    ),
]


def test_live_login_installation_discovery_and_widgets() -> None:
    """Exercise the real cloud API without logging response values or secrets."""

    async def exercise_api() -> None:
        assert USERNAME is not None
        assert PASSWORD is not None

        async with ClientSession() as session:
            discovery_client = HargassnerClient(
                session=session,
                base_url=DEFAULT_BASE_URL,
                username=USERNAME,
                password=PASSWORD,
                client_id=None,
                client_secret=None,
                installation="",
            )
            await discovery_client.login()
            installations = await discovery_client.get_installations()

            assert installations
            assert all(installation.get("id") for installation in installations)

            widget_client = HargassnerClient(
                session=session,
                base_url=DEFAULT_BASE_URL,
                username=USERNAME,
                password=PASSWORD,
                client_id=None,
                client_secret=None,
                installation=installations[0]["id"],
            )
            widgets = await widget_client.get_widgets()

            assert isinstance(widgets, dict)
            assert isinstance(widgets.get("data"), list)
            assert "meta" in widgets

    asyncio.run(exercise_api())
