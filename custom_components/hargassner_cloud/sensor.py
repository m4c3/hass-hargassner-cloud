
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity
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
    value_fn: Callable[[dict[str, Any]], Any] | None = None

# Default mappings into the widgets JSON
def get_nested(data, path: list[str], default=None):
    cur = data
    try:
        for p in path:
            if cur is None:
                return default
            cur = cur.get(p) if isinstance(cur, dict) else None
        return cur if cur is not None else default
    except Exception:
        return default

SENSOR_MAPPINGS: list[HargassnerSensorDescription] = [
    HargassnerSensorDescription(
        key="outdoor_temperature",
        name="Outdoor Temperature",
        unit="°C",
        device_class="temperature",
        value_fn=lambda root: get_nested(root, ["widgets", "Outdoor", "temperature_current"]),
    ),
    HargassnerSensorDescription(
        key="boiler_temperature",
        name="Boiler Temperature",
        unit="°C",
        device_class="temperature",
        value_fn=lambda root: get_nested(root, ["widgets", "HEATER", "heater_temperature_current"]),
    ),
    HargassnerSensorDescription(
        key="smoke_temperature",
        name="Smoke Temperature",
        unit="°C",
        device_class="temperature",
        value_fn=lambda root: get_nested(root, ["widgets", "HEATER", "smoke_temperature"]),
    ),
    HargassnerSensorDescription(
        key="buffer_top_temperature",
        name="Buffer Top Temperature",
        unit="°C",
        device_class="temperature",
        value_fn=lambda root: get_nested(root, ["widgets", "BUFFER", "buffer_top_temperature"]),
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

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            val = self.entity_description.value_fn(data) if self.entity_description.value_fn else None
            return float(val) if isinstance(val, (int, float, str)) and str(val).replace('.','',1).isdigit() else val
        except Exception:
            return None
