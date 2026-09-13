from __future__ import annotations

from custom_components.hargassner_cloud.helpers import (
    apply_overrides,
    find_widget,
    first_of,
    value_at,
    widgets,
)

PAYLOAD = {
    "data": [
        {"widget": "HEATER", "values": {"state": "STATE_ON"}},
        {
            "widget": "BOILER",
            "number": 1,
            "values": {"temperature": 55},
        },
    ]
}


def test_widget_lookup() -> None:
    assert len(widgets(PAYLOAD)) == 2
    assert find_widget(PAYLOAD, "BOILER", "1") == PAYLOAD["data"][1]
    assert find_widget(PAYLOAD, "MISSING") is None
    assert value_at(PAYLOAD, "HEATER", "state") == "STATE_ON"
    assert value_at(PAYLOAD, "BOILER", "temperature", "1") == 55
    assert value_at(PAYLOAD, "BOILER", "missing", "1") is None


def test_first_of_keeps_falsey_values() -> None:
    assert first_of(None, 0, 1) == 0
    assert first_of(None, False, True) is False
    assert first_of(None, None) is None


def test_apply_overrides_only_accepts_mapping_fields() -> None:
    defaults = {"sensor": {"widget": "HEATER", "field": "old", "number": "1"}}
    result = apply_overrides(
        defaults,
        {"sensor": {"field": "new", "ignored": "value"}, "invalid": "value"},
    )

    assert result == {"sensor": {"widget": "HEATER", "field": "new", "number": "1"}}
    assert result is not defaults
