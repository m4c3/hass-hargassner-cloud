from __future__ import annotations

import json

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload

from .const import CONF_AREA, CONF_MAPPING_OVERRIDES_JSON, DEFAULT_SCAN_INTERVAL


class HargassnerOptionsFlowHandler(OptionsFlowWithReload):
    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                overrides = json.loads(
                    user_input.get(CONF_MAPPING_OVERRIDES_JSON) or "{}"
                )
                if not isinstance(overrides, dict) or any(
                    not isinstance(value, dict) for value in overrides.values()
                ):
                    raise ValueError
            except (TypeError, ValueError):
                errors[CONF_MAPPING_OVERRIDES_JSON] = "invalid_mapping"
            else:
                return self.async_create_entry(title="", data=user_input)

        defaults = {
            "scan_interval_seconds": self.config_entry.options.get(
                "scan_interval_seconds", DEFAULT_SCAN_INTERVAL
            ),
            CONF_AREA: self.config_entry.options.get(
                CONF_AREA, self.config_entry.data.get(CONF_AREA, "")
            ),
            CONF_MAPPING_OVERRIDES_JSON: self.config_entry.options.get(
                CONF_MAPPING_OVERRIDES_JSON, ""
            ),
        }
        if user_input is not None:
            defaults.update(user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    "scan_interval_seconds", default=defaults["scan_interval_seconds"]
                ): int,
                vol.Optional(CONF_AREA, default=defaults[CONF_AREA]): str,
                # Freitext-JSON für Mapping-Overrides (Punkt 11)
                vol.Optional(
                    CONF_MAPPING_OVERRIDES_JSON,
                    default=defaults[CONF_MAPPING_OVERRIDES_JSON],
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
