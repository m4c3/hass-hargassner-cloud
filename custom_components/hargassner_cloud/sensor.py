from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Dict
import json

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_INSTALLATION,
    CONF_BASE_URL,
    CONF_AREA,
    CONF_MAPPING_OVERRIDES_JSON,
)
from .adapters import as_float, as_str
from .helpers import value_at, first_of

# -------------------------------------------------
# Description inkl. translation_key (Punkt 10)
# -------------------------------------------------
@dataclass
class HargassnerSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None


def _load_overrides(entry: ConfigEntry) -> Dict[str, Dict[str, str]]:
    try:
        txt = entry.options.get(CONF_MAPPING_OVERRIDES_JSON, "") or ""
        if not txt.strip():
            return {}
        data = json.loads(txt)
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except Exception:
        return {}
    return {}


# ---------------- descriptions per widget ----------------

def descriptions_for_heater() -> list[HargassnerSensorDescription]:
    return [
        HargassnerSensorDescription(
            key="heater_state",
            name="Heater State",
            icon="mdi:fire",
            translation_key="heater_state",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda r: as_str(value_at(r, "HEATER", "state")),
        ),
        HargassnerSensorDescription(
            key="heater_program",
            name="Heater Program",
            icon="mdi:cog",
            translation_key="heater_program",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda r: as_str(value_at(r, "HEATER", "program")),
        ),
        HargassnerSensorDescription(
            key="heater_smoke_temp",
            name="Smoke Temperature",
            translation_key="heater_smoke_temp",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "HEATER", "smoke_temperature")),
        ),
        HargassnerSensorDescription(
            key="heater_temp_current",
            name="Heater Temperature",
            translation_key="heater_temp_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "HEATER", "heater_temperature_current")),
        ),
        HargassnerSensorDescription(
            key="outdoor_temp",
            name="Outdoor Temperature",
            translation_key="outdoor_temp",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(first_of(
                value_at(r, "HEATER", "outdoor_temperature"),
                value_at(r, "HEATING_CIRCUIT_RADIATOR", "outdoor_temperature", number="1"),
                value_at(r, "HEATING_CIRCUIT_FLOOR", "outdoor_temperature", number="2"),
            )),
        ),
        HargassnerSensorDescription(
            key="outdoor_temp_avg",
            name="Outdoor Temperature (avg)",
            translation_key="outdoor_temp_avg",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(first_of(
                value_at(r, "HEATER", "outdoor_temperature_average"),
                value_at(r, "HEATING_CIRCUIT_RADIATOR", "outdoor_temperature_average", number="1"),
                value_at(r, "HEATING_CIRCUIT_FLOOR", "outdoor_temperature_average", number="2"),
            )),
        ),
        HargassnerSensorDescription(
            key="heater_efficiency",
            name="Efficiency",
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
            name="Buffer State",
            translation_key="buffer_state",
            icon="mdi:water-boiler",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda r: as_str(value_at(r, "BUFFER", "state")),
        ),
        HargassnerSensorDescription(
            key="buffer_charge",
            name="Buffer Charge",
            translation_key="buffer_charge",
            native_unit_of_measurement="%",
            icon="mdi:battery-heart-variant",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "BUFFER", "buffer_charge")),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_top",
            name="Buffer Temperature Top",
            translation_key="buffer_temp_top",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "BUFFER", "buffer_temperature_top")),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_center",
            name="Buffer Temperature Center",
            translation_key="buffer_temp_center",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "BUFFER", "buffer_temperature_center")),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_bottom",
            name="Buffer Temperature Bottom",
            translation_key="buffer_temp_bottom",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "BUFFER", "buffer_temperature_bottom")),
        ),
    ]


def descriptions_for_boiler_1() -> list[HargassnerSensorDescription]:
    return [
        HargassnerSensorDescription(
            key="boiler1_temp_current",
            name="Boiler 1 Temperature",
            translation_key="boiler1_temp_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "BOILER", "boiler_temperature_current", number="1")),
        ),
        HargassnerSensorDescription(
            key="boiler1_charge",
            name="Boiler 1 Charge",
            translation_key="boiler1_charge",
            native_unit_of_measurement="%",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: as_float(value_at(r, "BOILER", "boiler_charge", number="1")),
        ),
    ]


def descriptions_for_hc(widget: str, num: int, prefix: str) -> list[HargassnerSensorDescription]:
    n = str(num)
    return [
        HargassnerSensorDescription(
            key=f"{prefix}{num}_flow_temp_current",
            name=f"{prefix}{num} Flow Temperature",
            translation_key=f"{prefix}{num}_flow_temp_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: as_float(value_at(r, w, "flow_temperature_current", number=n)),
        ),
        HargassnerSensorDescription(
            key=f"{prefix}{num}_flow_temp_target",
            name=f"{prefix}{num} Flow Target",
            translation_key=f"{prefix}{num}_flow_temp_target",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: as_float(value_at(r, w, "flow_temperature_target", number=n)),
        ),
        HargassnerSensorDescription(
            key=f"{prefix}{num}_room_temp_target",
            name=f"{prefix}{num} Room Target",
            translation_key=f"{prefix}{num}_room_temp_target",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: as_float(value_at(r, w, "room_temperature_target", number=n)),
        ),
        HargassnerSensorDescription(
            key=f"{prefix}{num}_room_temp_current",
            name=f"{prefix}{num} Room Temperature",
            translation_key=f"{prefix}{num}_room_temp_current",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: as_float(value_at(r, w, "room_temperature_current", number=n)),
        ),
    ]


# ---------------- HA setup ----------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    mapping_overrides_text = data.get("mapping_overrides_json") or ""

    # Map-Overrides laden (Punkt 11)
    try:
        overrides = json.loads(mapping_overrides_text) if mapping_overrides_text else {}
    except Exception:
        overrides = {}

    def ov(key: str, default_widget: str, default_field: str, default_number: str | None = None):
        # hole override je Entity-Key
        o = overrides.get(key) if isinstance(overrides, dict) else None
        widget = (o.get("widget") if o else None) or default_widget
        field = (o.get("field") if o else None) or default_field
        number = (o.get("number") if o else None) or default_number
        return widget, field, number

    root = coordinator.data or {}
    entities: list[SensorEntity] = []

    # HEATER-Gruppe vorhanden?
    if any(w.get("widget") == "HEATER" for w in (root.get("data") or [])):
        for d in descriptions_for_heater():
            entities.append(HargassnerSensor(coordinator, entry, d))

    # BUFFER
    if any(w.get("widget") == "BUFFER" for w in (root.get("data") or [])):
        for d in descriptions_for_buffer():
            entities.append(HargassnerSensor(coordinator, entry, d))

    # BOILER
    if any(w.get("widget") == "BOILER" for w in (root.get("data") or [])):
        for d in descriptions_for_boiler_1():
            entities.append(HargassnerSensor(coordinator, entry, d))

    # HC
    if any(w.get("widget") == "HEATING_CIRCUIT_RADIATOR" for w in (root.get("data") or [])):
        for d in descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1, "HC1"):
            entities.append(HargassnerSensor(coordinator, entry, d))

    if any(w.get("widget") == "HEATING_CIRCUIT_FLOOR" for w in (root.get("data") or [])):
        for d in descriptions_for_hc("HEATING_CIRCUIT_FLOOR", 2, "HC2"):
            entities.append(HargassnerSensor(coordinator, entry, d))

    async_add_entities(entities)


class HargassnerSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, description: HargassnerSensorDescription):
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name

        if description.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = description.native_unit_of_measurement
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
        heater = next((w for w in (root.get("data") or []) if w.get("widget") == "HEATER"), None)
        values = (heater or {}).get("values") or {}
        model = values.get("device_type") or "Unknown"
        device_name = values.get("name") or "NanoPK"

        installation_id = str(entry.data.get(CONF_INSTALLATION, "unknown"))
        base_url = entry.data.get(CONF_BASE_URL, "https://web.hargassner.at")
        suggested_area = entry.data.get(CONF_AREA)

        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, installation_id)},
            manufacturer="Hargassner",
            model=model,
            name=device_name,
            configuration_url=f"{base_url}/",
            suggested_area=suggested_area,
        )

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        try:
            root = self.coordinator.data or {}
            meta = (root.get("meta") or {}).copy()
            allowed = {"online_state", "refreshed", "timestamp", "source"}
            return {k: v for k, v in meta.items() if k in allowed}
        except Exception:
            return None

    @property
    def native_value(self):
        # value_fn kümmert sich bereits um Typ-Konvertierung (Adapter)
        data = self.coordinator.data or {}
        try:
            return self.entity_description.value_fn(data) if self.entity_description.value_fn else None
        except Exception:
            return None
