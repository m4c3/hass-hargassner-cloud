from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.diagnostics import async_redact_data

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_SECRET,
    CONF_INSTALLATION,
)

# Felder, die in den Diagnostics geschwärzt werden sollen
TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_SECRET,
    # Installation-ID darfst du mit aufnehmen oder ebenfalls schwärzen:
    # CONF_INSTALLATION,
}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
):
    """Return diagnostics for a config entry."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = data.get("coordinator")

    # Rohdaten aus dem Cloud-Polling (Widgets/State)
    raw_payload = coordinator.data if coordinator else None

    # Zugangsdaten in entry.data/options sicher schwärzen
    redacted_entry = {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
    }

    return {
        "entry": redacted_entry,
        "coordinator_last_update_success": getattr(coordinator, "last_update_success", None)
        if coordinator
        else None,
        "raw_widgets": raw_payload,
    }
