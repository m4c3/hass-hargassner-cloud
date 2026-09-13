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
    "authorization",
    "client_id",
    "coordinates",
    "location",
    "token",
    "email",
    "name",
    "serial_number",
}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    """Return redacted diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    payload = async_redact_data(coordinator.data, TO_REDACT)

    redacted_entry = {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
    }

    return {
        "entry": redacted_entry,
        "coordinator_last_update_success": coordinator.last_update_success,
        "widgets": payload,
    }
