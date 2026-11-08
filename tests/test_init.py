from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntry

from custom_components.hargassner_cloud import _create_client_credentials_issue


def test_client_credentials_issue_is_linked_when_supported() -> None:
    hass = MagicMock()
    entry = cast(ConfigEntry, SimpleNamespace(entry_id="entry-1"))
    signature = SimpleNamespace(parameters={"config_entry_id": object()})

    with (
        patch(
            "custom_components.hargassner_cloud.inspect.signature",
            return_value=signature,
        ),
        patch(
            "custom_components.hargassner_cloud.ir.async_create_issue"
        ) as create_issue,
    ):
        _create_client_credentials_issue(hass, entry)

    assert create_issue.call_args.kwargs["config_entry_id"] == "entry-1"


def test_client_credentials_issue_stays_compatible_without_linking_support() -> None:
    hass = MagicMock()
    entry = cast(ConfigEntry, SimpleNamespace(entry_id="entry-1"))
    signature = SimpleNamespace(parameters={})

    with (
        patch(
            "custom_components.hargassner_cloud.inspect.signature",
            return_value=signature,
        ),
        patch(
            "custom_components.hargassner_cloud.ir.async_create_issue"
        ) as create_issue,
    ):
        _create_client_credentials_issue(hass, entry)

    assert "config_entry_id" not in create_issue.call_args.kwargs
