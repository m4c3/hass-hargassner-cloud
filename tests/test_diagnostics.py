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
            "data": [
                {
                    "widget": "HEATER",
                    "values": {
                        "temperature": 55,
                        "name": "Private heater",
                        "device_type": "NanoPK",
                    },
                    "parameters": {
                        "program": {
                            "resource": "/installations/12345/widgets/heater",
                            "value": "PROGRAM_OFF",
                        }
                    },
                }
            ],
            "meta": {"online_state": True, "current_timestamp": "private"},
        },
        last_update_success=True,
    )
    client = SimpleNamespace(
        diagnostics={
            "phase": "widgets",
            "outcome": "success",
            "credential_source": "live_bundle",
        }
    )
    entry = SimpleNamespace(
        data={"username": "user@example.test", "password": "secret"},
        options={"area": "Private room"},
        runtime_data=SimpleNamespace(
            coordinator=coordinator, hub=SimpleNamespace(client=client)
        ),
    )

    result = asyncio.run(async_get_config_entry_diagnostics(None, entry))  # type: ignore[arg-type]
    rendered = repr(result)

    assert "user@example.test" not in rendered
    assert "payload-token" not in rendered
    assert "secret" not in rendered
    assert "Private heater" not in rendered
    assert "Private room" not in rendered
    assert "12345" not in rendered
    assert "PROGRAM_OFF" not in rendered
    assert result["widget_structure"]["device"] == {"type": "NanoPK"}
    assert result["widget_structure"]["widgets"][0]["value_fields"] == {
        "temperature": "int",
        "name": "str",
        "device_type": "str",
    }
    assert result["widget_structure"]["widgets"][0]["parameter_fields"] == ["program"]
    assert result["api"]["phase"] == "widgets"


def test_diagnostics_work_without_runtime_data() -> None:
    entry = SimpleNamespace(
        data={"username": "user@example.test", "password": "secret"},
        options={},
        runtime_data=None,
    )

    result = asyncio.run(async_get_config_entry_diagnostics(None, entry))  # type: ignore[arg-type]
    rendered = repr(result)

    assert "user@example.test" not in rendered
    assert "secret" not in rendered
    assert result["coordinator_last_update_success"] is None
    assert result["api"]["outcome"] == "runtime_data_unavailable"
    assert result["widget_structure"]["device"] == {}
