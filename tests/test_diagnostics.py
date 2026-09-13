from __future__ import annotations

import asyncio
from types import SimpleNamespace

from custom_components.hargassner_cloud.diagnostics import (
    async_get_config_entry_diagnostics,
)


def test_diagnostics_redacts_entry_and_payload() -> None:
    coordinator = SimpleNamespace(
        data={
            "access_token": "payload-token",
            "data": [{"widget": "HEATER", "values": {"temperature": 55}}],
        },
        last_update_success=True,
    )
    entry = SimpleNamespace(
        data={"username": "user@example.test", "password": "secret"},
        options={},
        runtime_data=SimpleNamespace(coordinator=coordinator),
    )

    result = asyncio.run(async_get_config_entry_diagnostics(None, entry))  # type: ignore[arg-type]
    rendered = repr(result)

    assert "user@example.test" not in rendered
    assert "payload-token" not in rendered
    assert "secret" not in rendered
    assert result["widgets"]["data"][0]["values"]["temperature"] == 55
