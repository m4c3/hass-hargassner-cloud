from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_SECRET,
    CONF_CLIENT_ID,
    CONF_INSTALLATION,
    CONF_BASE_URL,
    CONF_AREA,
    DEFAULT_BASE_URL,
)
from .api import HargassnerClient

_LOGGER = logging.getLogger(__name__)


class HargassnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                # Live-Auth prüfen
                session = async_get_clientsession(self.hass)
                client = HargassnerClient(
                    session,
                    base_url=user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    installation=user_input[CONF_INSTALLATION],
                    client_id=user_input.get(CONF_CLIENT_ID),
                )
                await client.login()

                unique = str(user_input[CONF_INSTALLATION]).strip()
                await self.async_set_unique_id(unique)

                # Falls schon vorhanden: updaten statt abbrechen
                for ent in self._async_current_entries():
                    if ent.unique_id == unique:
                        self.hass.config_entries.async_update_entry(ent, data=user_input)
                        await self.hass.config_entries.async_reload(ent.entry_id)
                        return self.async_abort(reason="reauth_successful")

                return self.async_create_entry(title="Hargassner Cloud", data=user_input)

            except Exception as exc:
                _LOGGER.exception("Setup failed: %s", exc)
                msg = str(exc).lower()
                if "401" in msg or "auth" in msg or "unauthor" in msg:
                    errors["base"] = "auth"
                elif "timeout" in msg or "connect" in msg or "ssl" in msg:
                    errors["base"] = "cannot_connect"
                else:
                    errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_CLIENT_SECRET): str,
                vol.Optional(CONF_CLIENT_ID): str,
                vol.Required(CONF_INSTALLATION): str,
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Optional(CONF_AREA): str,  # neuer Bereich
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
