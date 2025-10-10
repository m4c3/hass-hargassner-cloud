
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

@dataclass
class HargassnerSensorDescription:
    key: str
    name: str
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    value_fn: Callable[[dict[str, Any]], Any] | None = None

def get_nested(data, path: list[str], default=None):
    cur = data
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur

def first_of(data: dict, paths: Iterable[list[str]], default=None):
    for p in paths:
        val = get_nested(data, p, None)
        if val is not None:
            return val
    return default

SENSOR_MAPPINGS: list[HargassnerSensorDescription] = [
    HargassnerSensorDescription(
        key="outdoor_temperature",
        name="Outdoor Temperature",
        unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda root: first_of(root, [
            ["widgets", "Outdoor", "temperature_current"],
            ["widgets", "OUTDOOR", "temperature_current"],
            ["widgets", "WEATHER", "outdoor_temperature"]
        ]),
    ),
    HargassnerSensorDescription(
        key="boiler_temperature",
        name="Boiler Temperature",
        unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda root: first_of(root, [
            ["widgets", "HEATER", "heater_temperature_current"],
            ["widgets", "BOILER", "temperature_current"]
        ]),
    ),
    HargassnerSensorDescription(
        key="smoke_temperature",
        name="Smoke Temperature",
        unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda root: first_of(root, [
            ["widgets", "HEATER", "smoke_temperature"],
            ["widgets", "BOILER", "flue_gas_temperature"]
        ]),
    ),
    HargassnerSensorDescription(
        key="buffer_top_temperature",
        name="Buffer Top Temperature",
        unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda root: first_of(root, [
            ["widgets", "BUFFER", "buffer_top_temperature"],
            ["widgets", "BUFFER", "temperature_top"]
        ]),
    ),
    HargassnerSensorDescription(
        key="power_output",
        name="Boiler Power",
        unit="kW",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda root: first_of(root, [
            ["widgets", "HEATER", "current_power_kw"],
            ["widgets", "HEATER", "power_current_kw"]
        ]),
    ),
    HargassnerSensorDescription(
        key="pellet_level",
        name="Pellet Level",
        unit="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda root: first_of(root, [
            ["widgets", "PELLET", "level_percent"],
            ["widgets", "FUEL", "level_percent"],
            ["widgets", "FUEL", "level"]
        ]),
    ),
    HargassnerSensorDescription(
        key="pellet_consumption_day",
        name="Pellet Consumption (today)",
        unit="kg",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda root: first_of(root, [
            ["widgets", "PELLET", "consumption_today_kg"],
            ["widgets", "FUEL", "consumption_today_kg"]
        ]),
    ),
    HargassnerSensorDescription(
        key="operating_state",
        name="Operating State",
        value_fn=lambda root: first_of(root, [
            ["widgets", "HEATER", "operating_state_text"],
            ["widgets", "HEATER", "state_text"],
            ["widgets", "HEATER", "state"]
        ]),
    ),
    HargassnerSensorDescription(
        key="burner_hours",
        name="Burner Hours",
        unit="h",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda root: first_of(root, [
            ["widgets", "HEATER", "burner_hours_total"],
            ["widgets", "HEATER", "operating_hours_burner"]
        ]),
    ),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities: list[SensorEntity] = []
    for desc in SENSOR_MAPPINGS:
        entities.append(HargassnerSensor(coordinator, entry, desc))
    async_add_entities(entities)

class HargassnerSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, description: HargassnerSensorDescription):
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        if description.unit:
            self._attr_native_unit_of_measurement = description.unit
        if description.device_class:
            self._attr_device_class = description.device_class
        if description.state_class:
            self._attr_state_class = description.state_class

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            val = self.entity_description.value_fn(data) if self.entity_description.value_fn else None
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, str):
                v = val.replace(",", ".")
                if v.replace(".", "", 1).isdigit():
                    return float(v)
            return val
        except Exception:
            return None
