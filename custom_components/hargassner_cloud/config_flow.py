from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HargassnerAuthError, HargassnerClient, HargassnerConnectionError
from .const import (
    CONF_AREA,
    CONF_BASE_URL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_INSTALLATION,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_BASE_URL,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    DOMAIN,
)
from .options_flow import HargassnerOptionsFlowHandler

_LOGGER = logging.getLogger(__name__)


class HargassnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._pending_data: dict[str, Any] | None = None
        self._installations: list[dict[str, str]] = []

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HargassnerOptionsFlowHandler:
        return HargassnerOptionsFlowHandler()

    def _client(self, user_input: dict[str, Any]) -> HargassnerClient:
        return HargassnerClient(
            async_get_clientsession(self.hass),
            base_url=user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            client_secret=user_input.get(CONF_CLIENT_SECRET, DEFAULT_CLIENT_SECRET),
            installation=user_input.get(CONF_INSTALLATION, ""),
            client_id=user_input.get(CONF_CLIENT_ID, DEFAULT_CLIENT_ID),
        )

    async def _async_validate(self, user_input: dict[str, Any]) -> None:
        await self._client(user_input).login()

    async def _async_finish_setup(
        self, data: dict[str, Any], installation_id: str
    ) -> ConfigFlowResult:
        data[CONF_INSTALLATION] = installation_id
        await self.async_set_unique_id(installation_id)
        self._abort_if_unique_id_configured()
        installation = next(
            (item for item in self._installations if item["id"] == installation_id),
            None,
        )
        title = installation["name"] if installation else "Hargassner Cloud"
        return self.async_create_entry(title=title, data=data)

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                client = self._client(user_input)
                await client.login()
                self._installations = await client.get_installations()
            except HargassnerAuthError:
                errors["base"] = "auth"
            except (HargassnerConnectionError, ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected setup failure")
                errors["base"] = "unknown"
            else:
                if len(self._installations) == 1:
                    return await self._async_finish_setup(
                        user_input, self._installations[0]["id"]
                    )
                self._pending_data = user_input
                return await self.async_step_installation()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Optional(CONF_AREA): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_installation(self, user_input=None) -> ConfigFlowResult:
        """Choose one of multiple installations available to the account."""
        if self._pending_data is None or not self._installations:
            return self.async_abort(reason="cannot_connect")
        if user_input is not None:
            return await self._async_finish_setup(
                self._pending_data, str(user_input[CONF_INSTALLATION])
            )
        choices = {item["id"]: item["name"] for item in self._installations}
        return self.async_show_form(
            step_id="installation",
            data_schema=vol.Schema({vol.Required(CONF_INSTALLATION): vol.In(choices)}),
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication for an existing config entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> ConfigFlowResult:
        """Validate replacement credentials and update the existing entry."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            updated_data = {**entry.data, **user_input}
            try:
                await self._async_validate(updated_data)
            except HargassnerAuthError:
                errors["base"] = "auth"
            except (HargassnerConnectionError, ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected reauthentication failure")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    str(updated_data[CONF_INSTALLATION]).strip()
                )
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=schema, errors=errors
        )
