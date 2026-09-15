from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .adapters import as_float, as_str
from .const import (
    CONF_AREA,
    CONF_BASE_URL,
    CONF_INSTALLATION,
    CONF_MAPPING_OVERRIDES_JSON,
    DOMAIN,
)
from .helpers import first_of, parameter_value_at, value_at

HEATER_PROGRAM_OPTIONS = [
    "automatic",
    "boiler",
    "chimney_sweeper",
    "combination_off",
    "combination_on",
    "manual",
    "off",
    "pellets_disabled",
    "stop_firing",
]
HEATING_STATE_OPTIONS = ["off", "on"]


def _state_value(value: object) -> str | None:
    """Normalize a heater or buffer state for Home Assistant translations."""
    state = as_str(value)
    if not state or not state.startswith("STATE_"):
        return None
    normalized = state.removeprefix("STATE_").lower()
    return normalized if normalized in HEATING_STATE_OPTIONS else None


def _program_value(root: dict[str, Any]) -> str | None:
    """Normalize the current heater program for Home Assistant translations."""
    value = as_str(parameter_value_at(root, "HEATER", "program"))
    if not value or not value.startswith("PROGRAM_"):
        return None
    normalized = value.removeprefix("PROGRAM_").lower()
    return normalized if normalized in HEATER_PROGRAM_OPTIONS else None


def _positive_number(value: object, default: int | None = None) -> int | None:
    """Normalize a positive widget number."""
    candidate = default if value is None else value
    if isinstance(candidate, bool) or not isinstance(candidate, (int, str)):
        return None
    try:
        number = int(candidate)
    except ValueError:
        return None
    return number if number > 0 else None


# -------------------------------------------------
# Description inkl. translation_key (Punkt 10)
# -------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class HargassnerSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None
    legacy_unique_id_key: str | None = None


def _load_overrides(entry: ConfigEntry) -> dict[str, dict[str, str]]:
    try:
        txt = entry.options.get(CONF_MAPPING_OVERRIDES_JSON, "") or ""
        if not txt.strip():
            return {}
        data = json.loads(txt)
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except (TypeError, ValueError):
        return {}
    return {}


# ---------------- descriptions per widget ----------------


def descriptions_for_heater() -> list[HargassnerSensorDescription]:
    return [
        HargassnerSensorDescription(
            key="heater_state",
            icon="mdi:fire",
            translation_key="heater_state",
            device_class=SensorDeviceClass.ENUM,
            options=HEATING_STATE_OPTIONS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda r: _state_value(value_at(r, "HEATER", "state")),
        ),
        HargassnerSensorDescription(
            key="heater_program",
            icon="mdi:cog",
            translation_key="heater_program",
            device_class=SensorDeviceClass.ENUM,
            options=HEATER_PROGRAM_OPTIONS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_program_value,
        ),
        HargassnerSensorDescription(
            key="heater_smoke_temp",
            translation_key="heater_smoke_temp",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "HEATER", "smoke_temperature")),
        ),
        HargassnerSensorDescription(
            key="heater_temp_current",
            translation_key="heater_temp_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                value_at(r, "HEATER", "heater_temperature_current")
            ),
        ),
        HargassnerSensorDescription(
            key="outdoor_temp",
            translation_key="outdoor_temp",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                first_of(
                    value_at(r, "HEATER", "outdoor_temperature"),
                    value_at(
                        r, "HEATING_CIRCUIT_RADIATOR", "outdoor_temperature", number="1"
                    ),
                    value_at(
                        r, "HEATING_CIRCUIT_FLOOR", "outdoor_temperature", number="2"
                    ),
                )
            ),
        ),
        HargassnerSensorDescription(
            key="outdoor_temp_avg",
            translation_key="outdoor_temp_avg",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                first_of(
                    value_at(r, "HEATER", "outdoor_temperature_average"),
                    value_at(
                        r,
                        "HEATING_CIRCUIT_RADIATOR",
                        "outdoor_temperature_average",
                        number="1",
                    ),
                    value_at(
                        r,
                        "HEATING_CIRCUIT_FLOOR",
                        "outdoor_temperature_average",
                        number="2",
                    ),
                )
            ),
        ),
        HargassnerSensorDescription(
            key="heater_efficiency",
            translation_key="heater_efficiency",
            native_unit_of_measurement="%",
            icon="mdi:percent",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "HEATER", "efficiency")),
        ),
    ]


def descriptions_for_buffer() -> list[HargassnerSensorDescription]:
    return [
        HargassnerSensorDescription(
            key="buffer_state",
            translation_key="buffer_state",
            icon="mdi:water-boiler",
            device_class=SensorDeviceClass.ENUM,
            options=HEATING_STATE_OPTIONS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda r: _state_value(value_at(r, "BUFFER", "state")),
        ),
        HargassnerSensorDescription(
            key="buffer_charge",
            translation_key="buffer_charge",
            native_unit_of_measurement="%",
            icon="mdi:battery-heart-variant",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "BUFFER", "buffer_charge")),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_top",
            translation_key="buffer_temp_top",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                value_at(r, "BUFFER", "buffer_temperature_top")
            ),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_center",
            translation_key="buffer_temp_center",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                value_at(r, "BUFFER", "buffer_temperature_center")
            ),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_bottom",
            translation_key="buffer_temp_bottom",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                value_at(r, "BUFFER", "buffer_temperature_bottom")
            ),
        ),
    ]


def descriptions_for_boiler(num: int) -> list[HargassnerSensorDescription]:
    number = str(num)
    return [
        HargassnerSensorDescription(
            key=f"boiler{num}_temp_current",
            translation_key="boiler_temp_current",
            translation_placeholders={"number": number},
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                value_at(r, "BOILER", "boiler_temperature_current", number=number)
            ),
        ),
        HargassnerSensorDescription(
            key=f"boiler{num}_charge",
            translation_key="boiler_charge",
            translation_placeholders={"number": number},
            native_unit_of_measurement="%",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(
                value_at(r, "BOILER", "boiler_charge", number=number)
            ),
        ),
    ]


def descriptions_for_hc(widget: str, num: int) -> list[HargassnerSensorDescription]:
    n = str(num)
    translation_prefix = f"hc{num}"
    legacy_prefix = f"HC{num}{num}" if num in (1, 2) else None

    def hc_value(field: str) -> Callable[[dict[str, Any]], float | None]:
        return lambda root: as_float(value_at(root, widget, field, number=n))

    return [
        HargassnerSensorDescription(
            key=f"{translation_prefix}_flow_temp_current",
            translation_key="hc_flow_temp_current",
            translation_placeholders={"number": n},
            legacy_unique_id_key=(
                f"{legacy_prefix}_flow_temp_current" if legacy_prefix else None
            ),
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=hc_value("flow_temperature_current"),
        ),
        HargassnerSensorDescription(
            key=f"{translation_prefix}_flow_temp_target",
            translation_key="hc_flow_temp_target",
            translation_placeholders={"number": n},
            legacy_unique_id_key=(
                f"{legacy_prefix}_flow_temp_target" if legacy_prefix else None
            ),
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=hc_value("flow_temperature_target"),
        ),
        HargassnerSensorDescription(
            key=f"{translation_prefix}_room_temp_target",
            translation_key="hc_room_temp_target",
            translation_placeholders={"number": n},
            legacy_unique_id_key=(
                f"{legacy_prefix}_room_temp_target" if legacy_prefix else None
            ),
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=hc_value("room_temperature_target"),
        ),
        HargassnerSensorDescription(
            key=f"{translation_prefix}_room_temp_current",
            translation_key="hc_room_temp_current",
            translation_placeholders={"number": n},
            legacy_unique_id_key=(
                f"{legacy_prefix}_room_temp_current" if legacy_prefix else None
            ),
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=hc_value("room_temperature_current"),
        ),
    ]


# ---------------- HA setup ----------------


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator = entry.runtime_data.coordinator
    overrides = _load_overrides(entry)

    root = coordinator.data or {}
    entities: list[SensorEntity] = []

    # HEATER-Gruppe vorhanden?
    if any(w.get("widget") == "HEATER" for w in (root.get("data") or [])):
        for d in descriptions_for_heater():
            entities.append(
                HargassnerSensor(coordinator, entry, d, overrides.get(d.key))
            )

    # BUFFER
    if any(w.get("widget") == "BUFFER" for w in (root.get("data") or [])):
        for d in descriptions_for_buffer():
            entities.append(
                HargassnerSensor(coordinator, entry, d, overrides.get(d.key))
            )

    widgets = root.get("data") or []
    boiler_numbers: set[int] = set()
    for widget_data in widgets:
        if widget_data.get("widget") != "BOILER":
            continue
        number = _positive_number(widget_data.get("number"), default=1)
        if number is None or number in boiler_numbers:
            continue
        boiler_numbers.add(number)
        for d in descriptions_for_boiler(number):
            entities.append(
                HargassnerSensor(coordinator, entry, d, overrides.get(d.key))
            )

    heating_circuit_numbers: set[int] = set()
    for widget_data in widgets:
        widget = widget_data.get("widget")
        if not isinstance(widget, str) or not widget.startswith("HEATING_CIRCUIT_"):
            continue
        number = _positive_number(widget_data.get("number"))
        if number is None or number in heating_circuit_numbers:
            continue
        heating_circuit_numbers.add(number)
        for d in descriptions_for_hc(widget, number):
            entities.append(
                HargassnerSensor(coordinator, entry, d, overrides.get(d.key))
            )

    async_add_entities(entities)


class HargassnerSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: HargassnerSensorDescription,
        override: dict[str, str] | None,
    ):
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._description = description
        self._mapping_override = override
        self._attr_unique_id = (
            f"{entry.entry_id}_{description.legacy_unique_id_key or description.key}"
        )

        if description.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = (
                description.native_unit_of_measurement
            )
        if description.device_class:
            self._attr_device_class = description.device_class
        if description.state_class:
            self._attr_state_class = description.state_class
        if description.icon:
            self._attr_icon = description.icon
        if description.entity_category:
            self._attr_entity_category = description.entity_category
        if description.translation_key:
            self._attr_translation_key = description.translation_key

        # Gemeinsames Gerät
        root = coordinator.data or {}
        heater = next(
            (w for w in (root.get("data") or []) if w.get("widget") == "HEATER"), None
        )
        values = (heater or {}).get("values") or {}
        model = values.get("device_type") or "Unknown"
        device_name = values.get("name") or "NanoPK"

        installation_id = str(entry.data.get(CONF_INSTALLATION, "unknown"))
        base_url = entry.data.get(CONF_BASE_URL, "https://web.hargassner.at")
        suggested_area = entry.options.get(CONF_AREA, entry.data.get(CONF_AREA))
        software_version = entry.runtime_data.device_metadata.get("software_version")

        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, installation_id)},
            manufacturer="Hargassner",
            model=model,
            name=device_name,
            sw_version=software_version,
            configuration_url=f"{base_url}/",
            suggested_area=suggested_area,
        )

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        root = self.coordinator.data or {}
        meta = (root.get("meta") or {}).copy()
        allowed = {"online_state", "refreshed", "timestamp", "source"}
        return {k: v for k, v in meta.items() if k in allowed}

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        if self._mapping_override:
            widget = self._mapping_override.get("widget")
            field = self._mapping_override.get("field")
            if widget and field:
                raw = value_at(
                    data, widget, field, self._mapping_override.get("number")
                )
                if (
                    self.entity_description.device_class
                    == SensorDeviceClass.TEMPERATURE
                    or self.entity_description.native_unit_of_measurement == "%"
                ):
                    return as_float(raw)
                return as_str(raw)
        return self._description.value_fn(data) if self._description.value_fn else None
