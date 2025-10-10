
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_CLIENT_SECRET, CONF_INSTALLATION
)

_LOGGER = logging.getLogger(__name__)

class HargassnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            # Try to authenticate quickly
            try:
                from hargassner import Hargassner
                client = Hargassner(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    installation=user_input[CONF_INSTALLATION],
                )
                await self.hass.async_add_executor_job(client.login)
                # Success
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

    async def async_step_reauth(self, entry_data) -> FlowResult:
        return await self.async_step_reauth_confirm(entry_data)

    async def async_step_reauth_confirm(self, entry_data=None) -> FlowResult:
        errors = {}
        if self.context.get("entry_id"):
            entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        else:
            entry = None

        if self._inline_step_data:
            user_input = self._inline_step_data
        else:
            user_input = None

        if user_input is not None:
            try:
                from hargassner import Hargassner
                client = Hargassner(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    installation=user_input[CONF_INSTALLATION],
                )
                await self.hass.async_add_executor_job(client.login)
                if entry:
                    self.hass.config_entries.async_update_entry(entry, data=user_input)
                    await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            except Exception:
                errors["base"] = "auth"

        schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_CLIENT_SECRET): str,
            vol.Required(CONF_INSTALLATION): str,
        })
        return self.async_show_form(step_id="reauth_confirm", data_schema=schema, errors=errors)
