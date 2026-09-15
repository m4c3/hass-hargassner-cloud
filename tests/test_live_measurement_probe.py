from __future__ import annotations

from scripts.live_measurement_probe import REDACTED, sanitize_measurement_payload


def test_measurement_probe_keeps_measurements_and_units() -> None:
    payload = {
        "data": [
            {
                "name": "Flow temperature",
                "key": "flow_temperature",
                "value": 42.7,
                "unit": "°C",
                "active": True,
            }
        ]
    }

    assert sanitize_measurement_payload(payload) == payload


def test_measurement_probe_redacts_credentials_and_identifiers() -> None:
    payload = {
        "access_token": "private-token",
        "device_id": "device-123",
        "installationId": "installation-456",
        "serial_number": "serial-789",
        "owner": "user@example.test",
        "nested": [{"gateway_id": 123, "value": 21.5}],
    }

    sanitized = sanitize_measurement_payload(payload)

    assert sanitized == {
        "access_token": REDACTED,
        "device_id": REDACTED,
        "installationId": REDACTED,
        "serial_number": REDACTED,
        "owner": REDACTED,
        "nested": [{"gateway_id": REDACTED, "value": 21.5}],
    }
    assert "private-token" not in repr(sanitized)
    assert "device-123" not in repr(sanitized)
    assert "user@example.test" not in repr(sanitized)
