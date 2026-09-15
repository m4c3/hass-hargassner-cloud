from __future__ import annotations

import json
from pathlib import Path

from custom_components.hargassner_cloud import binary_sensor as binary_sensor_platform
from custom_components.hargassner_cloud import sensor as sensor_platform
from custom_components.hargassner_cloud.sensor import (
    descriptions_for_boiler,
    descriptions_for_buffer,
    descriptions_for_hc,
    descriptions_for_heater,
)


def test_entity_names_are_provided_by_translations() -> None:
    sensor_descriptions = [
        *descriptions_for_heater(),
        *descriptions_for_buffer(),
        *descriptions_for_boiler(1),
        *descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1),
        *descriptions_for_hc("HEATING_CIRCUIT_FLOOR", 2),
    ]

    assert all(
        not isinstance(description.name, str) for description in sensor_descriptions
    )
    assert all(description.translation_key for description in sensor_descriptions)
    assert all(
        not isinstance(description.name, str)
        for description in binary_sensor_platform.build_descriptions({})
    )
    assert all(
        description.translation_key
        for description in binary_sensor_platform.build_descriptions({})
    )


def test_heating_circuit_translation_keys_preserve_legacy_unique_ids() -> None:
    hc1 = descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1)
    hc2 = descriptions_for_hc("HEATING_CIRCUIT_FLOOR", 2)

    hc1_flow = next(item for item in hc1 if item.key == "hc1_flow_temp_current")
    hc2_flow = next(item for item in hc2 if item.key == "hc2_flow_temp_current")
    assert hc1_flow.translation_key == "hc_flow_temp_current"
    assert hc1_flow.legacy_unique_id_key == "HC11_flow_temp_current"
    assert hc2_flow.translation_key == "hc_flow_temp_current"
    assert hc2_flow.legacy_unique_id_key == "HC22_flow_temp_current"


def test_numbered_components_have_no_artificial_upper_limit() -> None:
    boiler = descriptions_for_boiler(12)
    heating_circuit = descriptions_for_hc("HEATING_CIRCUIT_CUSTOM", 27)
    binary_boiler = binary_sensor_platform.descriptions_for_boiler(12)
    binary_heating_circuit = binary_sensor_platform.descriptions_for_hc(
        "HEATING_CIRCUIT_CUSTOM", 27
    )

    assert boiler[0].key == "boiler12_state"
    assert boiler[0].translation_placeholders == {"number": "12"}
    assert heating_circuit[0].key == "hc27_state"
    assert heating_circuit[0].translation_placeholders == {"number": "27"}
    assert binary_boiler[0].key == "boiler12_pump_active"
    assert binary_heating_circuit[0].key == "hc27_pump_active"


def test_binary_descriptions_follow_api_widgets_and_deduplicate_numbers() -> None:
    payload = {
        "data": [
            {"widget": "BOILER", "number": "8"},
            {"widget": "BOILER", "number": 8},
            {"widget": "HEATING_CIRCUIT_CUSTOM", "number": "11"},
            {"widget": "HEATING_CIRCUIT_FLOOR", "number": 11},
        ]
    }

    keys = [
        description.key
        for description in binary_sensor_platform.build_descriptions(payload)
    ]
    assert keys.count("boiler8_pump_active") == 1
    assert keys.count("hc11_pump_active") == 1
    assert "heater_on" not in keys
    assert "buffer_pump_active" not in keys


def test_heater_program_reads_and_normalizes_parameter_value() -> None:
    program = next(
        description
        for description in descriptions_for_heater()
        if description.key == "heater_program"
    )
    payload = {
        "data": [
            {
                "widget": "HEATER",
                "parameters": {"program": {"value": "PROGRAM_AUTOMATIC"}},
            }
        ]
    }

    assert program.value_fn is not None
    assert program.value_fn(payload) == "automatic"


def test_heater_and_buffer_states_are_normalized_for_translation() -> None:
    heater_state = next(
        description
        for description in descriptions_for_heater()
        if description.key == "heater_state"
    )
    buffer_state = next(
        description
        for description in descriptions_for_buffer()
        if description.key == "buffer_state"
    )
    payload = {
        "data": [
            {"widget": "HEATER", "values": {"state": "STATE_OFF"}},
            {"widget": "BUFFER", "values": {"state": "STATE_ON"}},
        ]
    }

    assert heater_state.options == ["off", "on"]
    assert buffer_state.options == ["off", "on"]
    assert heater_state.value_fn is not None
    assert buffer_state.value_fn is not None
    assert heater_state.value_fn(payload) == "off"
    assert buffer_state.value_fn(payload) == "on"


def test_nanopk_widget_schema_is_supported() -> None:
    """Exercise the widget shape observed in sanitized NanoPK diagnostics."""
    payload = {
        "data": [
            {
                "widget": "HEATER",
                "values": {
                    "state": "STATE_ON",
                    "smoke_temperature": 101.5,
                    "heater_temperature_current": 72.0,
                    "heater_exhaust_guard": True,
                    "outdoor_temperature": 8.5,
                    "outdoor_temperature_average": 7.0,
                    "efficiency": 91,
                },
                "parameters": {"program": {"value": "PROGRAM_AUTOMATIC"}},
            },
            {
                "widget": "BUFFER",
                "values": {
                    "state": "STATE_ON",
                    "buffer_charge": 64,
                    "buffer_temperature_top": 55,
                    "buffer_temperature_center": 48.5,
                    "buffer_temperature_bottom": 42.0,
                    "pump_active": True,
                },
            },
            {
                "widget": "HEATING_CIRCUIT_RADIATOR",
                "number": "1",
                "values": {
                    "flow_temperature_target": None,
                    "flow_temperature_current": 31.5,
                    "room_temperature_target": 20,
                    "room_temperature_current": None,
                    "pump_active": False,
                    "active": True,
                },
            },
            {
                "widget": "HEATING_CIRCUIT_FLOOR",
                "number": "2",
                "values": {
                    "flow_temperature_target": None,
                    "flow_temperature_current": 27.0,
                    "room_temperature_target": 21,
                    "room_temperature_current": None,
                    "state": "STATE_ON",
                    "pump_active": True,
                    "active": True,
                },
                "parameters": {"mode": {"value": "MODE_AUTOMATIC"}},
            },
            {
                "widget": "BOILER",
                "number": "1",
                "values": {
                    "boiler_temperature_target": None,
                    "boiler_temperature_current": 54.5,
                    "boiler_charge": 82.0,
                    "pump_active": False,
                },
            },
        ],
        "meta": {"online_state": True},
    }

    sensor_descriptions = [
        *descriptions_for_heater(),
        *descriptions_for_buffer(),
        *descriptions_for_boiler(1),
        *descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1),
        *descriptions_for_hc("HEATING_CIRCUIT_FLOOR", 2),
    ]
    sensor_values = {
        description.key: description.value_fn(payload)
        for description in sensor_descriptions
        if description.value_fn is not None
    }
    binary_values = {
        description.key: description.value_fn(payload)
        for description in binary_sensor_platform.build_descriptions(payload)
        if description.value_fn is not None
    }

    assert sensor_values["heater_program"] == "automatic"
    assert sensor_values["heater_state"] == "on"
    assert sensor_values["heater_smoke_temp"] == 101.5
    assert sensor_values["buffer_charge"] == 64.0
    assert sensor_values["buffer_state"] == "on"
    assert sensor_values["hc1_flow_temp_target"] is None
    assert sensor_values["hc2_flow_temp_current"] == 27.0
    assert sensor_values["boiler1_temp_current"] == 54.5
    assert binary_values["online"] is True
    assert binary_values["heater_exhaust_guard"] is True
    assert binary_values["hc1_pump_active"] is False
    assert binary_values["hc2_pump_active"] is True
    assert binary_values["boiler1_pump_active"] is False


def test_neo_hv_widget_schema_is_supported_without_phantom_components() -> None:
    """Exercise the widget shape observed in sanitized Neo-HV diagnostics."""
    payload = {
        "data": [
            {
                "widget": "HEATING_CIRCUIT_CONTROLLER",
                "values": {
                    "source_temperature": 65,
                    "request_temperature": None,
                    "outdoor_temperature": 8.5,
                    "outdoor_temperature_average": 7.0,
                },
                "parameters": {"program": {"value": "synthetic"}},
            },
            {
                "widget": "HEATING_CIRCUIT_RADIATOR",
                "number": "1",
                "values": {
                    "flow_temperature_target": None,
                    "flow_temperature_current": 31,
                    "room_temperature_target": 20,
                    "room_temperature_current": None,
                    "state": "STATE_ON",
                    "pump_active": True,
                    "active": True,
                },
                "parameters": {"mode": {"value": "MODE_AUTOMATIC"}},
            },
            {
                "widget": "BOILER",
                "number": "1",
                "values": {
                    "boiler_temperature_target": None,
                    "boiler_temperature_current": 54.5,
                    "boiler_charge": 82,
                    "state": "STATE_ON",
                    "pump_active": False,
                    "force_charging_active": False,
                },
            },
        ],
        "meta": {"online_state": True},
    }

    hc_values = {
        description.key: description.value_fn(payload)
        for description in descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1)
        if description.value_fn is not None
    }
    boiler_values = {
        description.key: description.value_fn(payload)
        for description in descriptions_for_boiler(1)
        if description.value_fn is not None
    }
    controller_values = {
        description.key: description.value_fn(payload)
        for description in sensor_platform.descriptions_for_heating_controller(
            include_outdoor=True
        )
        if description.value_fn is not None
    }
    binary_descriptions = binary_sensor_platform.build_descriptions(payload)
    binary_keys = {description.key for description in binary_descriptions}

    assert hc_values["hc1_flow_temp_current"] == 31.0
    assert hc_values["hc1_state"] == "on"
    assert hc_values["hc1_mode"] == "MODE_AUTOMATIC"
    assert boiler_values["boiler1_charge"] == 82.0
    assert boiler_values["boiler1_state"] == "on"
    assert boiler_values["boiler1_temp_target"] is None
    assert controller_values == {
        "controller_request_temp": None,
        "controller_source_temp": 65.0,
        "outdoor_temp": 8.5,
        "outdoor_temp_avg": 7.0,
    }
    assert binary_keys == {
        "online",
        "hc1_pump_active",
        "hc1_active",
        "boiler1_pump_active",
        "boiler1_force_charging_active",
    }


def test_entity_translation_keys_match_for_all_languages() -> None:
    translation_dir = Path("custom_components/hargassner_cloud/translations")
    reference = json.loads((translation_dir / "en.json").read_text())["entity"]

    def keys(value: object, prefix: str = "") -> set[str]:
        if not isinstance(value, dict):
            return set()
        result: set[str] = set()
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            result.add(path)
            result.update(keys(child, path))
        return result

    expected = keys(reference)
    for language in ("cs", "de", "es", "fr", "nb", "pl"):
        translated = json.loads((translation_dir / f"{language}.json").read_text())
        assert keys(translated["entity"]) == expected
