from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, NAME, PLATFORMS,
    CONF_USERNAME, CONF_PASSWORD, CONF_CLIENT_SECRET, CONF_CLIENT_ID, CONF_INSTALLATION, CONF_BASE_URL,
    DEFAULT_SCAN_INTERVAL, DEFAULT_BASE_URL
)
from .api import HargassnerClient, HargassnerAuthError

_LOGGER = logging.getLogger(__name__)


class HargassnerHub:
    def __init__(self, hass: HomeAssistant, base_url: str, username: str, password: str, client_secret: str, installation: str, client_id: str | None):
        self.hass = hass
        self.client = HargassnerClient(
            async_get_clientsession(hass),
            base_url=base_url or DEFAULT_BASE_URL,
            username=username,
            password=password,
            client_secret=client_secret,
            installation=installation,
            client_id=client_id,
        )

    async def async_fetch(self):
        return await self.client.get_widgets()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    hub = HargassnerHub(
        hass,
        entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_CLIENT_SECRET],
        entry.data[CONF_INSTALLATION],
        entry.data.get(CONF_CLIENT_ID),
    )

    async def _async_update():
        try:
            data = await hub.async_fetch()
            return data
        except HargassnerAuthError as err:
            raise UpdateFailed(f"Auth: {err}") from err
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
