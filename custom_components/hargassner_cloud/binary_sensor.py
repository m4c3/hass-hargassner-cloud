from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_INSTALLATION, CONF_BASE_URL, CONF_AREA


@dataclass
class HargassnerBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None] | None = None


def _widgets(root: dict[str, Any]) -> list[dict[str, Any]]:
    return (root or {}).get("data") or []


def _find(root: dict[str, Any], widget: str, number: str | None = None) -> dict[str, Any] | None:
    for w in _widgets(root):
        if w.get("widget") != widget:
            continue
        if number is not None and str(w.get("number")) != str(number):
            continue
        return w
    return None


def _val(root: dict[str, Any], widget: str, field: str, number: str | None = None):
    w = _find(root, widget, number)
    return (w.get("values") or {}).get(field) if w else None


def _is_true(x) -> bool | None:
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)
    if isinstance(x, str):
        return x.lower() in ("true", "on", "1", "yes")
    return None


def build_descriptions() -> list[HargassnerBinaryDescription]:
    desc: list[HargassnerBinaryDescription] = []

    # Meta connectivity
    desc.append(
        HargassnerBinaryDescription(
            key="online",
            name="Online",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            value_fn=lambda root: _is_true((root.get("meta") or {}).get("online_state")),
        )
    )

    # HEATER
    desc.append(
        HargassnerBinaryDescription(
            key="heater_on",
            name="Heater On",
            device_class=BinarySensorDeviceClass.POWER,
            value_fn=lambda r: None if _val(r, "HEATER", "state") is None else _val(r, "HEATER", "state") != "STATE_OFF",
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="heater_exhaust_guard",
            name="Exhaust Guard",
            device_class=BinarySensorDeviceClass.SAFETY,
            value_fn=lambda r: _is_true(_val(r, "HEATER", "heater_exhaust_guard")),
        )
    )

    # BUFFER
    desc.append(
        HargassnerBinaryDescription(
            key="buffer_pump_active",
            name="Buffer Pump Active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "BUFFER", "pump_active")),
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="buffer_force_charging_active",
            name="Buffer Force Charging",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "BUFFER", "force_charging_active")),
        )
    )

    # BOILER #1
    desc.append(
        HargassnerBinaryDescription(
            key="boiler1_pump_active",
            name="Boiler 1 Pump Active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "BOILER", "pump_active", number="1")),
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="boiler1_force_charging_active",
            name="Boiler 1 Force Charging",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "BOILER", "force_charging_active", number="1")),
        )
    )

    # HEATING CIRCUITS
    desc.append(
        HargassnerBinaryDescription(
            key="hc1_pump_active",
            name="HC1 Pump Active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "HEATING_CIRCUIT_RADIATOR", "pump_active", number="1")),
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="hc1_active",
            name="HC1 Active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "HEATING_CIRCUIT_RADIATOR", "active", number="1")),
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="hc2_pump_active",
            name="HC2 Pump Active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "HEATING_CIRCUIT_FLOOR", "pump_active", number="2")),
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="hc2_active",
            name="HC2 Active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: _is_true(_val(r, "HEATING_CIRCUIT_FLOOR", "active", number="2")),
        )
    )

    return desc


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities: list[BinarySensorEntity] = [HargassnerBinarySensor(coordinator, entry, d) for d in build_descriptions()]
    async_add_entities(entities)


class HargassnerBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, description: HargassnerBinaryDescription):
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name

        # ---- Device (gemeinsam, Name "NanoPK") ----
        root = coordinator.data or {}
        heater = next((w for w in ((root.get("data") or [])) if w.get("widget") == "HEATER"), None)
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
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        try:
            if not self.entity_description.value_fn:
                return None
            return self.entity_description.value_fn(data)
        except Exception:
            return None
