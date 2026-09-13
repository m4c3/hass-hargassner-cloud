from __future__ import annotations

import json
from pathlib import Path

from custom_components.hargassner_cloud.binary_sensor import build_descriptions
from custom_components.hargassner_cloud.sensor import (
    descriptions_for_boiler_1,
    descriptions_for_buffer,
    descriptions_for_hc,
    descriptions_for_heater,
)


def test_entity_names_are_provided_by_translations() -> None:
    sensor_descriptions = [
        *descriptions_for_heater(),
        *descriptions_for_buffer(),
        *descriptions_for_boiler_1(),
        *descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1, "HC1"),
        *descriptions_for_hc("HEATING_CIRCUIT_FLOOR", 2, "HC2"),
    ]

    assert all(
        not isinstance(description.name, str) for description in sensor_descriptions
    )
    assert all(description.translation_key for description in sensor_descriptions)
    assert all(
        not isinstance(description.name, str) for description in build_descriptions()
    )
    assert all(description.translation_key for description in build_descriptions())


def test_heating_circuit_translation_keys_preserve_legacy_unique_ids() -> None:
    hc1 = descriptions_for_hc("HEATING_CIRCUIT_RADIATOR", 1, "HC1")
    hc2 = descriptions_for_hc("HEATING_CIRCUIT_FLOOR", 2, "HC2")

    assert hc1[0].key == "hc1_flow_temp_current"
    assert hc1[0].translation_key == "hc1_flow_temp_current"
    assert hc1[0].legacy_unique_id_key == "HC11_flow_temp_current"
    assert hc2[0].key == "hc2_flow_temp_current"
    assert hc2[0].translation_key == "hc2_flow_temp_current"
    assert hc2[0].legacy_unique_id_key == "HC22_flow_temp_current"


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
