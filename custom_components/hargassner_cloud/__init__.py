from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry, ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    HargassnerAuthError,
    HargassnerClient,
    HargassnerClientCredentialsError,
    HargassnerConnectionError,
)
from .const import (
    CONF_BASE_URL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_INSTALLATION,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NAME,
    PLATFORMS,
)
from .utils.logfilter import RedactSecretsFilter

_LOGGER = logging.getLogger(__name__)
# Punkt 12: Logger-Filter anschließen
_LOGGER.addFilter(RedactSecretsFilter())

CLIENT_CREDENTIALS_ISSUE_URL = "https://github.com/m4c3/hass-hargassner-cloud/issues"


class HargassnerHub:
    def __init__(
        self,
        hass: HomeAssistant,
        base_url: str,
        username: str,
        password: str,
        client_secret: str | None,
        installation: str,
        client_id: str | None,
    ):
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


@dataclass
class HargassnerRuntimeData:
    """Runtime objects associated with a config entry."""

    hub: HargassnerHub
    coordinator: DataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Hargassner Cloud from a config entry."""
    hub = HargassnerHub(
        hass,
        entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_CLIENT_SECRET),
        entry.data[CONF_INSTALLATION],
        entry.data.get(CONF_CLIENT_ID),
    )

    async def _async_update():
        try:
            data = await hub.async_fetch()
            ir.async_delete_issue(hass, DOMAIN, f"client_credentials_{entry.entry_id}")
            return data
        except HargassnerAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except HargassnerClientCredentialsError as err:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"client_credentials_{entry.entry_id}",
                is_fixable=False,
                is_persistent=True,
                learn_more_url=CLIENT_CREDENTIALS_ISSUE_URL,
                severity=ir.IssueSeverity.ERROR,
                translation_key="client_credentials",
            )
            raise UpdateFailed(str(err)) from err
        except HargassnerConnectionError as err:
            raise UpdateFailed(str(err)) from err

    # Scan-Intervall aus Options oder Default
    update_seconds = entry.options.get("scan_interval_seconds", DEFAULT_SCAN_INTERVAL)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=NAME,
        config_entry=entry,
        update_method=_async_update,
        update_interval=timedelta(seconds=update_seconds),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = HargassnerRuntimeData(hub=hub, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a Hargassner Cloud config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
