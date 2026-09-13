<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Hargassner Cloud logo" width="400">
</p>

# Hargassner Cloud for Home Assistant

Hargassner Cloud is a custom Home Assistant integration that reads heating data
from the Hargassner web portal and exposes it as sensors and binary sensors.

> [!IMPORTANT]
> This project is not affiliated with or endorsed by Hargassner. It uses an
> undocumented cloud API and may require updates when the portal changes.

## Features

- UI-based setup with your Hargassner email and password
- Automatic installation discovery and selection
- No manual client ID or client secret lookup
- Automatic recovery when Hargassner rotates its public web-client credentials
- Central polling through Home Assistant's `DataUpdateCoordinator`
- Automatic reauthentication when credentials are rejected
- Configurable polling interval, suggested area, and field mappings
- Redacted diagnostics and log messages
- German and English translations

## Entities

Entities are created according to the widget groups returned by your
installation. Depending on the boiler and portal configuration, not every entity
listed below will be available.

### Sensors

| Group | Values |
| --- | --- |
| Heater | State, program, heater temperature, flue-gas temperature, efficiency |
| Outdoor | Current and average outdoor temperature |
| Buffer | State, charge, top/centre/bottom temperatures |
| Boiler | Boiler 1 temperature and charge |
| Heating circuit 1 | Current/target flow and room temperatures |
| Heating circuit 2 | Current/target flow and room temperatures |

### Binary sensors

- Cloud connectivity
- Heater power state and exhaust guard
- Buffer pump and forced charging
- Boiler 1 pump and forced charging
- Heating circuit 1 and 2 activity and pump state

## Installation

### HACS

1. Open **HACS → Integrations**.
1. Open the three-dot menu and select **Custom repositories**.
1. Add `https://github.com/m4c3/hass-hargassner-cloud` as an **Integration**.
1. Install **Hargassner Cloud** and restart Home Assistant.
1. Open **Settings → Devices & services → Add integration** and select
   **Hargassner Cloud**.

### Manual installation

1. Copy `custom_components/hargassner_cloud` into the `custom_components`
   directory of your Home Assistant configuration.
1. Restart Home Assistant.
1. Open **Settings → Devices & services → Add integration** and select
   **Hargassner Cloud**.

## Configuration

The setup dialog asks for:

| Field | Description |
| --- | --- |
| Email | Email address used for the Hargassner web portal |
| Password | Hargassner account password |
| Base URL | Optional; defaults to `https://web.hargassner.at` |
| Area | Optional suggested Home Assistant area |

After login, the integration discovers installations available to your account.
A single installation is selected automatically; when multiple installations
are available, Home Assistant displays a selection step.

The integration uses the public client credentials shipped with the Hargassner
web application. If those credentials are rejected, it downloads the current
login page and JavaScript bundle once, extracts the rotated values, and retries
the login. Your Hargassner password is never sent anywhere except the configured
Hargassner base URL.

Existing entries that contain manually configured client credentials remain
supported.

## Options

Open **Settings → Devices & services → Hargassner Cloud → Configure** to change:

- Polling interval in seconds; the default is 300 seconds
- Suggested area
- Mapping overrides as JSON

Saving options automatically reloads the integration.

### Mapping overrides

Mapping overrides allow an entity to read a different widget field without a
code change. Each top-level key is an entity description key. `widget` and
`field` are required for an override to take effect; `number` is optional.

```json
{
  "heater_temp_current": {
    "widget": "HEATER",
    "field": "heater_temperature_current"
  },
  "hc1_room_temp_current": {
    "widget": "HEATING_CIRCUIT_RADIATOR",
    "field": "room_temperature_current",
    "number": "1"
  }
}
```

Invalid JSON is rejected by the options dialog. Unknown entity keys are ignored.
Overrides work for sensors and binary sensors.

## Authentication and reauthentication

The integration obtains a bearer token from the Hargassner login endpoint. A
rejected login or expired authorization starts Home Assistant's standard
reauthentication flow. Temporary network and server failures are reported as
update failures and do not ask you to re-enter your password.

## Diagnostics and privacy

Download diagnostics from **Settings → Devices & services → Hargassner Cloud**.
Passwords, usernames, installation IDs, client credentials, authorization
tokens, names, serial numbers, and common location fields are redacted.

Before sharing diagnostics, review the generated file because the undocumented
API may introduce new fields in the future.

## Development

Create a virtual environment and install the development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install homeassistant pytest ruff mypy
```

Run the checks:

```bash
python -m compileall custom_components tests
pytest
ruff format --check custom_components tests
ruff check custom_components tests
mypy custom_components tests
```

The test suite covers value conversion, widget lookup, mapping overrides,
authentication failures, web-client credential rotation, same-endpoint retries,
and diagnostics redaction.

## Troubleshooting

### Authentication failed

Verify the email and password by signing in at
[`web.hargassner.at`](https://web.hargassner.at). You no longer need to retrieve
a client secret from the browser developer tools.

### Cannot connect

Verify that Home Assistant can reach the configured base URL over HTTPS. Portal
maintenance and rate limiting can also cause temporary update failures.

### Missing entities

The integration only creates sensor groups present in the API response. If your
boiler uses different widget or field names, download diagnostics and configure
a mapping override.

## License

See [LICENSE](LICENSE).
