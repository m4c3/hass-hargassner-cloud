from __future__ import annotations

from scripts.live_device_probe import safe_version_candidates, version_field_types


def test_probe_reports_only_safe_version_candidates_and_field_types() -> None:
    payload = {
        "data": {
            "name": "Private installation",
            "serial_number": "private-serial",
            "devices": [
                {
                    "software": {
                        "version_code": "V1.2.3",
                        "download_url": "https://private.example.test/file",
                    },
                    "gateway": {
                        "software": {"version_code": "GW 4.5"},
                        "serial_number": "private-gateway",
                    },
                    "firmware_revision": None,
                }
            ],
        }
    }

    candidates = safe_version_candidates(payload)
    fields = version_field_types(payload)
    rendered = repr((candidates, fields))

    assert candidates == [
        "response.data.devices[1].software.version_code: V1.2.3",
        "response.data.devices[1].gateway.software.version_code: GW 4.5",
    ]
    assert "response.data.devices[].firmware_revision: null" in fields
    assert "response.data.devices[].software: dict" in fields
    assert "Private installation" not in rendered
    assert "private-serial" not in rendered
    assert "private-gateway" not in rendered
    assert "private.example.test" not in rendered


def test_probe_rejects_suspicious_version_values() -> None:
    payload = {
        "version_code": "user@example.test",
        "nested": {"version_code": "safe-2.0"},
    }

    assert safe_version_candidates(payload) == [
        "response.nested.version_code: safe-2.0"
    ]
