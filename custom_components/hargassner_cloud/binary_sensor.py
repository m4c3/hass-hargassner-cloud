from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .adapters import as_bool
from .const import (
    CONF_AREA,
    CONF_BASE_URL,
    CONF_INSTALLATION,
    CONF_MAPPING_OVERRIDES_JSON,
    DOMAIN,
)
from .helpers import value_at


@dataclass(frozen=True, kw_only=True)
class HargassnerBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None] | None = None


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


def descriptions_for_boiler(num: int) -> list[HargassnerBinaryDescription]:
    """Build binary sensor descriptions for a numbered boiler."""
    number = str(num)
    return [
        HargassnerBinaryDescription(
            key=f"boiler{num}_pump_active",
            translation_key="boiler_pump_active",
            translation_placeholders={"number": number},
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda root: as_bool(
                value_at(root, "BOILER", "pump_active", number=number)
            ),
        ),
        HargassnerBinaryDescription(
            key=f"boiler{num}_force_charging_active",
            translation_key="boiler_force_charging_active",
            translation_placeholders={"number": number},
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda root: as_bool(
                value_at(root, "BOILER", "force_charging_active", number=number)
            ),
        ),
    ]


def descriptions_for_hc(widget: str, num: int) -> list[HargassnerBinaryDescription]:
    """Build binary sensor descriptions for a numbered heating circuit."""
    number = str(num)
    return [
        HargassnerBinaryDescription(
            key=f"hc{num}_pump_active",
            translation_key="hc_pump_active",
            translation_placeholders={"number": number},
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda root: as_bool(
                value_at(root, widget, "pump_active", number=number)
            ),
        ),
        HargassnerBinaryDescription(
            key=f"hc{num}_active",
            translation_key="hc_active",
            translation_placeholders={"number": number},
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda root: as_bool(
                value_at(root, widget, "active", number=number)
            ),
        ),
    ]


def build_descriptions(root: dict[str, Any]) -> list[HargassnerBinaryDescription]:
    """Build descriptions from widgets actually returned by the API."""
    desc: list[HargassnerBinaryDescription] = []

    # Meta connectivity (Diagnose)
    desc.append(
        HargassnerBinaryDescription(
            key="online",
            translation_key="online",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda root: as_bool((root.get("meta") or {}).get("online_state")),
        )
    )

    # HEATER
    desc.append(
        HargassnerBinaryDescription(
            key="heater_on",
            translation_key="heater_on",
            device_class=BinarySensorDeviceClass.POWER,
            value_fn=lambda r: (
                None
                if value_at(r, "HEATER", "state") is None
                else (value_at(r, "HEATER", "state") != "STATE_OFF")
            ),
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="heater_exhaust_guard",
            translation_key="heater_exhaust_guard",
            device_class=BinarySensorDeviceClass.SAFETY,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda r: as_bool(value_at(r, "HEATER", "heater_exhaust_guard")),
        )
    )

    # BUFFER
    desc.append(
        HargassnerBinaryDescription(
            key="buffer_pump_active",
            translation_key="buffer_pump_active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: as_bool(value_at(r, "BUFFER", "pump_active")),
        )
    )
    desc.append(
        HargassnerBinaryDescription(
            key="buffer_force_charging_active",
            translation_key="buffer_force_charging_active",
            device_class=BinarySensorDeviceClass.RUNNING,
            value_fn=lambda r: as_bool(value_at(r, "BUFFER", "force_charging_active")),
        )
    )

    boiler_numbers: set[int] = set()
    heating_circuit_numbers: set[int] = set()
    for widget_data in root.get("data") or []:
        widget = widget_data.get("widget")
        if widget == "BOILER":
            number = _positive_number(widget_data.get("number"), default=1)
            if number is not None and number not in boiler_numbers:
                boiler_numbers.add(number)
                desc.extend(descriptions_for_boiler(number))
        elif isinstance(widget, str) and widget.startswith("HEATING_CIRCUIT_"):
            number = _positive_number(widget_data.get("number"))
            if number is not None and number not in heating_circuit_numbers:
                heating_circuit_numbers.add(number)
                desc.extend(descriptions_for_hc(widget, number))

    return desc


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    coordinator = entry.runtime_data.coordinator
    try:
        overrides = json.loads(entry.options.get(CONF_MAPPING_OVERRIDES_JSON) or "{}")
    except (TypeError, ValueError):
        overrides = {}

    entities: list[BinarySensorEntity] = [
        HargassnerBinarySensor(
            coordinator, entry, description, overrides.get(description.key)
        )
        for description in build_descriptions(coordinator.data or {})
    ]
    async_add_entities(entities)


class HargassnerBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: HargassnerBinaryDescription,
        override: dict[str, str] | None,
    ):
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._description = description
        self._mapping_override = override
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

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
        root = self.coordinator.data or {}
        meta = (root.get("meta") or {}).copy()
        allowed = {"online_state", "refreshed", "timestamp", "source"}
        return {k: v for k, v in meta.items() if k in allowed}

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        if self._mapping_override:
            widget = self._mapping_override.get("widget")
            field = self._mapping_override.get("field")
            if widget and field:
                return as_bool(
                    value_at(data, widget, field, self._mapping_override.get("number"))
                )
        if not self._description.value_fn:
            return None
        return self._description.value_fn(data)
