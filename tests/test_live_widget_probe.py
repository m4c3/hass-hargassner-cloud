from __future__ import annotations

from scripts.live_widget_probe import REDACTED, sanitize_widget_payload


def test_widget_probe_keeps_operating_values_and_modes() -> None:
    payload = {
        "widget": "HEATING_CIRCUIT_RADIATOR",
        "number": 1,
        "values": {
            "state": "STATE_HEATING",
            "flow_temperature_target": 35.5,
            "room_temperature_current": None,
        },
        "parameters": {"mode": {"value": "MODE_AUTOMATIC"}},
    }

    assert sanitize_widget_payload(payload) == payload


def test_widget_probe_redacts_names_credentials_and_identifiers() -> None:
    payload = {
        "id": "installation-123",
        "installationId": "installation-123",
        "access_token": "private-token",
        "email": "user@example.test",
        "values": {"name": "My heating", "serial_number": "serial-123"},
        "parameters": {"name": {"value": "Living room"}},
    }

    sanitized = sanitize_widget_payload(payload)

    assert sanitized == {
        "id": REDACTED,
        "installationId": REDACTED,
        "access_token": REDACTED,
        "email": REDACTED,
        "values": {"name": REDACTED, "serial_number": REDACTED},
        "parameters": {"name": REDACTED},
    }
    assert "installation-123" not in repr(sanitized)
    assert "private-token" not in repr(sanitized)
    assert "Living room" not in repr(sanitized)
