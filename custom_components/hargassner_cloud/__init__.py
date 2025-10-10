
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, NAME, PLATFORMS,
    CONF_USERNAME, CONF_PASSWORD, CONF_CLIENT_SECRET, CONF_INSTALLATION,
    DEFAULT_SCAN_INTERVAL
)

_LOGGER = logging.getLogger(__name__)

class HargassnerHub:
    def __init__(self, hass: HomeAssistant, username: str, password: str, client_secret: str, installation: str):
        self.hass = hass
        self.username = username
        self.password = password
        self.client_secret = client_secret
        self.installation = installation
        self.client = None  # late init

    async def async_connect(self):
        # Import on runtime to avoid blocking setup without deps
        from hargassner import Hargassner
        self.client = Hargassner(
            username=self.username,
            password=self.password,
            client_secret=self.client_secret,
            installation=self.installation,
        )
        # Some libs are sync-only; run in executor if needed
        await self.hass.async_add_executor_job(self.client.login)

    async def async_fetch(self):
        # Returns the full widgets payload (dict)
        def _fetch():
            # Assuming the library exposes a method to read widgets/state
            # Common naming patterns: get_widgets(), get_state(), read_widgets()
            # We try the canonical name and fall back for older versions.
            if hasattr(self.client, "get_widgets"):
                return self.client.get_widgets()
            if hasattr(self.client, "get_state"):
                return self.client.get_state()
            if hasattr(self.client, "widgets"):
                return self.client.widgets()
            raise RuntimeError("Hargassner client: no data method found")
        return await self.hass.async_add_executor_job(_fetch)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    hub = HargassnerHub(
        hass,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_CLIENT_SECRET],
        entry.data[CONF_INSTALLATION],
    )
    await hub.async_connect()

    async def _async_update():
        try:
            data = await hub.async_fetch()
            return data
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=NAME,
        update_method=_async_update,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "hub": hub,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
