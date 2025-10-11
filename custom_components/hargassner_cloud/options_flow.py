from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_SCAN_INTERVAL, CONF_AREA, CONF_MAPPING_OVERRIDES_JSON


class HargassnerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {
            "scan_interval_seconds": self._entry.options.get("scan_interval_seconds", DEFAULT_SCAN_INTERVAL),
            CONF_AREA: self._entry.options.get(CONF_AREA, self._entry.data.get(CONF_AREA, "")),
            CONF_MAPPING_OVERRIDES_JSON: self._entry.options.get(CONF_MAPPING_OVERRIDES_JSON, ""),
        }
        schema = vol.Schema(
            {
                vol.Required("scan_interval_seconds", default=defaults["scan_interval_seconds"]): int,
                vol.Optional(CONF_AREA, default=defaults[CONF_AREA]): str,
                # Freitext-JSON für Mapping-Overrides (Punkt 11)
                vol.Optional(CONF_MAPPING_OVERRIDES_JSON, default=defaults[CONF_MAPPING_OVERRIDES_JSON]): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


async def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return HargassnerOptionsFlowHandler(config_entry)
