from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from custom_components.hargassner_cloud.const import CONF_BASE_URL
from custom_components.hargassner_cloud.system_health import system_health_info


def test_system_health_uses_configured_endpoint_without_exposing_entry_data() -> None:
    hass = MagicMock()
    hass.config_entries.async_entries.return_value = [
        SimpleNamespace(data={CONF_BASE_URL: "https://example.test"})
    ]
    reachability = object()
    check_reachability = MagicMock(return_value=reachability)

    with patch(
        "custom_components.hargassner_cloud.system_health.system_health.async_check_can_reach_url",
        new=check_reachability,
    ):
        result = asyncio.run(system_health_info(hass))

    assert result == {
        "configured_entries": 1,
        "can_reach_server": reachability,
    }
    check_reachability.assert_called_once_with(hass, "https://example.test")
