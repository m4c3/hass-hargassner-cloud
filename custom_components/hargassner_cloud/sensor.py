from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
    # noqa: E701
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_INSTALLATION,
    CONF_BASE_URL,
    CONF_AREA,
)


# -------------------------------------------------
# Description: includes suggested_unit_of_measurement explicitly
# -------------------------------------------------
@dataclass
class HargassnerSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None
    suggested_unit_of_measurement: str | None = None  # wichtig für HA-Versionen, die es direkt abfragen


# ---------------- helpers ----------------

def _find_widgets(root: dict[str, Any], widget_name: str) -> List[dict[str, Any]]:
    items = (root or {}).get("data") or []
    return [w for w in items if w.get("widget") == widget_name]


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _val(root: dict[str, Any], widget: str, field: str, number: str | None = None):
    for w in _find_widgets(root, widget):
        if number is not None and str(w.get("number")) != str(number):
            continue
        return (w.get("values") or {}).get(field)
    return None


# ---------------- descriptions per widget ----------------

def descriptions_for_heater() -> list[HargassnerSensorDescription]:
    return [
        HargassnerSensorDescription(
            key="heater_state",
            name="Heater State",
            icon="mdi:fire",
            value_fn=lambda r: _val(r, "HEATER", "state"),
        ),
        HargassnerSensorDescription(
            key="heater_program",
            name="Heater Program",
            icon="mdi:cog",
            value_fn=lambda r: _val(r, "HEATER", "program"),
        ),
        HargassnerSensorDescription(
            key="heater_smoke_temp",
            name="Smoke Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _val(r, "HEATER", "smoke_temperature"),
        ),
        HargassnerSensorDescription(
            key="heater_temp_current",
            name="Heater Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _val(r, "HEATER", "heater_temperature_current"),
        ),
        HargassnerSensorDescription(
            key="outdoor_temp",
            name="Outdoor Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _first(
                _val(r, "HEATER", "outdoor_temperature"),
                _val(r, "HEATING_CIRCUIT_RADIATOR", "outdoor_temperature", number="1"),
                _val(r, "HEATING_CIRCUIT_FLOOR", "outdoor_temperature", number="2"),
            ),
        ),
        HargassnerSensorDescription(
            key="outdoor_temp_avg",
            name="Outdoor Temperature (avg)",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _first(
                _val(r, "HEATER", "outdoor_temperature_average"),
                _val(r, "HEATING_CIRCUIT_RADIATOR", "outdoor_temperature_average", number="1"),
                _val(r, "HEATING_CIRCUIT_FLOOR", "outdoor_temperature_average", number="2"),
            ),
        ),
        HargassnerSensorDescription(
            key="heater_efficiency",
            name="Efficiency",
            native_unit_of_measurement="%",
            suggested_unit_of_measurement="%",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:percent",
            value_fn=lambda r: _val(r, "HEATER", "efficiency"),
        ),
    ]


def descriptions_for_buffer() -> list[HargassnerSensorDescription]:
    return [
        HargassnerSensorDescription(
            key="buffer_state",
            name="Buffer State",
            icon="mdi:water-boiler",
            value_fn=lambda r: _val(r, "BUFFER", "state"),
        ),
        HargassnerSensorDescription(
            key="buffer_charge",
            name="Buffer Charge",
            native_unit_of_measurement="%",
            suggested_unit_of_measurement="%",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:battery-heart-variant",
            value_fn=lambda r: _val(r, "BUFFER", "buffer_charge"),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_top",
            name="Buffer Temperature Top",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _val(r, "BUFFER", "buffer_temperature_top"),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_center",
            name="Buffer Temperature Center",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _val(r, "BUFFER", "buffer_temperature_center"),
        ),
        HargassnerSensorDescription(
            key="buffer_temp_bottom",
            name="Buffer Temperature Bottom",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _val(r, "BUFFER", "buffer_temperature_bottom"),
        ),
    ]


def descriptions_for_boiler_1() -> list[HargassnerSensorDescription]:
    return [
        HargassnerSensorDescription(
            key="boiler1_temp_current",
            name="Boiler 1 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _val(r, "BOILER", "boiler_temperature_current", number="1"),
        ),
        HargassnerSensorDescription(
            key="boiler1_charge",
            name="Boiler 1 Charge",
            native_unit_of_measurement="%",
            suggested_unit_of_measurement="%",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r: _val(r, "BOILER", "boiler_charge", number="1"),
        ),
    ]


def descriptions_for_hc(widget: str, num: int, prefix: str) -> list[HargassnerSensorDescription]:
    n = str(num)
    return [
        HargassnerSensorDescription(
            key=f"{prefix}{num}_flow_temp_current",
            name=f"{prefix}{num} Flow Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: _val(r, w, "flow_temperature_current", number=n),
        ),
        HargassnerSensorDescription(
            key=f"{prefix}{num}_flow_temp_target",
            name=f"{prefix}{num} Flow Target",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: _val(r, w, "flow_temperature_target", number=n),
        ),
        HargassnerSensorDescription(
            key=f"{prefix}{num}_room_temp_target",
            name=f"{prefix}{num} Room Target",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: _val(r, w, "room_temperature_target", number=n),
        ),
        HargassnerSensorDescription(
            key=f"{prefix}{num}_room_temp_current",
            name=f"{prefix}{num} Room Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement="°C",
            suggested_unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda r, w=widget, n=n: _val(r, w, "room_temperature_current", number=n),
        ),
    ]


# ---------------- HA setup ----------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    root = coordinator.data or {}
    entities: list[SensorEntity] = []

    if _find_widgets(root, "HEATER"):
        for d in descriptions_for_heater():
            entities.append(HargassnerSensor(coordinator, entry, d))

    if _find_widgets(root, "BUFFER"):
        for d in descriptions_for_buffer():
            entities.append(HargassnerSensor(coordinator, entry, d))

    if _find_widgets(root, "BOILER"):
        for d in descriptions_for_boiler_1():
            entities.append(HargassnerSensor(coordinator, entry, d))

    if _find_widgets(root, "HEATING_CIRCUIT_RADIATOR"):
        for d in descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1, "HC1"):
            entities.append(HargassnerSensor(coordinator, entry, d))

    if _find_widgets(root, "HEATING_CIRCUIT_FLOOR"):
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

        # Units / device class / state class / icon aus Description übernehmen
        if description.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        if description.device_class:
            self._attr_device_class = description.device_class
        if description.state_class:
            self._attr_state_class = description.state_class
        if description.icon:
            self._attr_icon = description.icon

        # -------- Gemeinsames Gerät: Name exakt "NanoPK" --------
        root = coordinator.data or {}
        heater = next((w for w in (root.get("data") or []) if w.get("widget") == "HEATER"), None)
        values = (heater or {}).get("values") or {}
        model = values.get("device_type") or "Unknown"
        device_name = values.get("name") or "NanoPK"  # exakt "NanoPK"

        installation_id = str(entry.data.get(CONF_INSTALLATION, "unknown"))
        base_url = entry.data.get(CONF_BASE_URL, "https://web.hargassner.at")
        suggested_area = entry.data.get(CONF_AREA)

        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, installation_id)},   # alle Entitäten an EIN Gerät
            manufacturer="Hargassner",
            model=model,
            name=device_name,                          # exakt "NanoPK"
            configuration_url=f"{base_url}/",
            suggested_area=suggested_area,
        )

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            val = self.entity_description.value_fn(data) if self.entity_description.value_fn else None
            if isinstance(val, (int, float)) or val is None:
                return val
            if isinstance(val, str):
                v = val.replace(",", ".")
                try:
                    return float(v)
                except Exception:
                    return val
            return val
        except Exception:
            return None
