
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, NAME, PLATFORMS,
    CONF_USERNAME, CONF_PASSWORD, CONF_CLIENT_SECRET, CONF_INSTALLATION,
    DEFAULT_SCAN_INTERVAL, AUTH_URL, WIDGETS_URL_TMPL
)
from .api import HargassnerClient

_LOGGER = logging.getLogger(__name__)

class HargassnerHub:
    def __init__(self, hass: HomeAssistant, username: str, password: str, client_secret: str, installation: str):
        self.hass = hass
        self.client = HargassnerClient(
            async_get_clientsession(hass),
            username=username,
            password=password,
            client_secret=client_secret,
            installation=installation,
            auth_url=AUTH_URL,
            widgets_url=WIDGETS_URL_TMPL.format(installation=installation),
        )

    async def async_fetch(self):
        return await self.client.get_widgets()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    hub = HargassnerHub(
        hass,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_CLIENT_SECRET],
        entry.data[CONF_INSTALLATION],
    )

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
