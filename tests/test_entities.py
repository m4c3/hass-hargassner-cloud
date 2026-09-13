from __future__ import annotations

import json
from pathlib import Path

from custom_components.hargassner_cloud import binary_sensor as binary_sensor_platform
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

    assert hc1[0].key == "hc1_flow_temp_current"
    assert hc1[0].translation_key == "hc_flow_temp_current"
    assert hc1[0].legacy_unique_id_key == "HC11_flow_temp_current"
    assert hc2[0].key == "hc2_flow_temp_current"
    assert hc2[0].translation_key == "hc_flow_temp_current"
    assert hc2[0].legacy_unique_id_key == "HC22_flow_temp_current"


def test_numbered_components_have_no_artificial_upper_limit() -> None:
    boiler = descriptions_for_boiler(12)
    heating_circuit = descriptions_for_hc("HEATING_CIRCUIT_CUSTOM", 27)
    binary_boiler = binary_sensor_platform.descriptions_for_boiler(12)
    binary_heating_circuit = binary_sensor_platform.descriptions_for_hc(
        "HEATING_CIRCUIT_CUSTOM", 27
    )

    assert boiler[0].key == "boiler12_temp_current"
    assert boiler[0].translation_placeholders == {"number": "12"}
    assert heating_circuit[0].key == "hc27_flow_temp_current"
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
