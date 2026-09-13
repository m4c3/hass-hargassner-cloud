from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CLIENT_SECRET, CONF_INSTALLATION, CONF_PASSWORD, CONF_USERNAME

TO_REDACT = {
    CONF_PASSWORD,
    CONF_CLIENT_SECRET,
    CONF_USERNAME,
    CONF_INSTALLATION,
    "access_token",
    "address",
    "area",
    "authorization",
    "client_id",
    "coordinates",
    "location",
    "token",
    "email",
    "name",
    "serial_number",
}


def _value_type(value: object) -> str:
    """Return a stable, non-sensitive JSON value type."""
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


def _widget_structure(payload: object) -> dict[str, object]:
    """Reduce a widget response to keys and types without operational values."""
    if not isinstance(payload, dict):
        return {"payload_type": _value_type(payload)}

    widgets: list[dict[str, object]] = []
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                widgets.append({"item_type": _value_type(item)})
                continue
            widget: dict[str, object] = {}
            if isinstance(item.get("widget"), str):
                widget["widget"] = item["widget"]
            if isinstance(item.get("number"), (int, str)):
                widget["number"] = str(item["number"])
            values = item.get("values")
            if isinstance(values, dict):
                widget["value_fields"] = {
                    str(key): _value_type(value) for key, value in values.items()
                }
            parameters = item.get("parameters")
            if isinstance(parameters, dict):
                widget["parameter_fields"] = sorted(str(key) for key in parameters)
            widgets.append(widget)

    meta = payload.get("meta")
    meta_fields = (
        {str(key): _value_type(value) for key, value in meta.items()}
        if isinstance(meta, dict)
        else {}
    )
    return {"widgets": widgets, "meta_fields": meta_fields}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    """Return redacted diagnostics for a config entry."""
    redacted_entry = {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
    }
    runtime_data = entry.runtime_data
    if runtime_data is None:
        return {
            "entry": redacted_entry,
            "coordinator_last_update_success": None,
            "api": {"phase": "setup", "outcome": "runtime_data_unavailable"},
            "widget_structure": {"widgets": [], "meta_fields": {}},
        }

    coordinator = runtime_data.coordinator
    payload = _widget_structure(coordinator.data)

    return {
        "entry": redacted_entry,
        "coordinator_last_update_success": coordinator.last_update_success,
        "api": async_redact_data(runtime_data.hub.client.diagnostics, TO_REDACT),
        "widget_structure": payload,
    }
