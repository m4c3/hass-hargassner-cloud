from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.data_entry_flow import AbortFlow, FlowResultType

from custom_components.hargassner_cloud.api import (
    HargassnerAuthError,
    HargassnerConnectionError,
)
from custom_components.hargassner_cloud.config_flow import HargassnerConfigFlow
from custom_components.hargassner_cloud.const import (
    CONF_INSTALLATION,
    CONF_MAPPING_OVERRIDES_JSON,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from custom_components.hargassner_cloud.options_flow import HargassnerOptionsFlowHandler

USER_INPUT = {
    CONF_USERNAME: "user@example.test",
    CONF_PASSWORD: "password",
}


def make_flow(installations: list[dict[str, str]]) -> HargassnerConfigFlow:
    flow = HargassnerConfigFlow()
    flow.hass = MagicMock()
    client = SimpleNamespace(
        login=AsyncMock(), get_installations=AsyncMock(return_value=installations)
    )
    flow._client = MagicMock(return_value=client)  # type: ignore[method-assign]
    flow.async_set_unique_id = AsyncMock()  # type: ignore[method-assign]
    flow._abort_if_unique_id_configured = MagicMock()  # type: ignore[method-assign]
    return flow


def test_single_installation_is_selected_automatically() -> None:
    flow = make_flow([{"id": "42", "name": "Home"}])
    result = asyncio.run(flow.async_step_user(dict(USER_INPUT)))

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home"
    assert result["data"][CONF_INSTALLATION] == "42"


def test_multiple_installations_show_selection() -> None:
    flow = make_flow([{"id": "42", "name": "Home"}, {"id": "84", "name": "Workshop"}])
    result = asyncio.run(flow.async_step_user(dict(USER_INPUT)))
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "installation"

    result = asyncio.run(flow.async_step_installation({CONF_INSTALLATION: "84"}))
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Workshop"
    assert result["data"][CONF_INSTALLATION] == "84"


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (HargassnerAuthError("bad credentials"), "auth"),
        (HargassnerConnectionError("offline"), "cannot_connect"),
    ],
)
def test_setup_errors(exception: Exception, error: str) -> None:
    flow = make_flow([])
    flow._client.return_value.login.side_effect = exception  # type: ignore[attr-defined]
    result = asyncio.run(flow.async_step_user(dict(USER_INPUT)))

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


def test_duplicate_installation_is_rejected() -> None:
    flow = make_flow([{"id": "42", "name": "Home"}])
    flow._abort_if_unique_id_configured.side_effect = AbortFlow(  # type: ignore[attr-defined]
        "already_configured"
    )

    with pytest.raises(AbortFlow, match="already_configured"):
        asyncio.run(flow.async_step_user(dict(USER_INPUT)))


def test_reauthentication_updates_credentials() -> None:
    flow = HargassnerConfigFlow()
    flow.hass = MagicMock()
    entry = SimpleNamespace(data={**USER_INPUT, CONF_INSTALLATION: "42"})
    flow._get_reauth_entry = MagicMock(return_value=entry)  # type: ignore[method-assign]
    flow._async_validate = AsyncMock()  # type: ignore[method-assign]
    flow.async_set_unique_id = AsyncMock()  # type: ignore[method-assign]
    flow._abort_if_unique_id_mismatch = MagicMock()  # type: ignore[method-assign]
    expected = {"type": FlowResultType.ABORT, "reason": "reauth_successful"}
    flow.async_update_reload_and_abort = MagicMock(  # type: ignore[method-assign]
        return_value=expected
    )

    updates = {
        CONF_USERNAME: USER_INPUT[CONF_USERNAME],
        CONF_PASSWORD: "new-password",
    }
    result = asyncio.run(flow.async_step_reauth_confirm(updates))

    assert result == expected
    flow.async_update_reload_and_abort.assert_called_once_with(  # type: ignore[attr-defined]
        entry, data_updates=updates
    )


def test_options_reject_invalid_mapping() -> None:
    handler = HargassnerOptionsFlowHandler()
    handler.hass = MagicMock()
    entry = SimpleNamespace(options={}, data={})

    with patch.object(
        HargassnerOptionsFlowHandler,
        "config_entry",
        new_callable=PropertyMock,
        return_value=entry,
    ):
        result = asyncio.run(
            handler.async_step_init(
                {
                    "scan_interval_seconds": 300,
                    CONF_MAPPING_OVERRIDES_JSON: "not-json",
                }
            )
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_MAPPING_OVERRIDES_JSON: "invalid_mapping"}
