
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_CLIENT_SECRET, CONF_INSTALLATION,
    AUTH_URL, WIDGETS_URL_TMPL
)
from .api import HargassnerClient

_LOGGER = logging.getLogger(__name__)

class HargassnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                client = HargassnerClient(
                    session,
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    installation=user_input[CONF_INSTALLATION],
                    auth_url=AUTH_URL,
                    widgets_url=WIDGETS_URL_TMPL.format(installation=user_input[CONF_INSTALLATION]),
                )
                await client.login()
                await self.async_set_unique_id(f"{user_input[CONF_USERNAME]}::{user_input[CONF_INSTALLATION]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Hargassner Cloud", data=user_input)
            except Exception as exc:
                _LOGGER.exception("Auth failed: %s", exc)
                errors["base"] = "auth"

        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_CLIENT_SECRET): str,
            vol.Required(CONF_INSTALLATION): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
