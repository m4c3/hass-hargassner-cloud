<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Hargassner Cloud logo" width="400">
</p>

<p align="center"><a href="README.de.md">Deutsch</a> | English | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.nb.md">Norsk bokmål</a> | <a href="README.pl.md">Polski</a> | <a href="README.cs.md">Čeština</a></p>

# Hargassner Cloud for Home Assistant

Hargassner Cloud is a custom Home Assistant integration that reads heating data
from the Hargassner web portal and exposes it as sensors and binary sensors.

> [!IMPORTANT]
> This project is not affiliated with or endorsed by Hargassner. It uses an
> undocumented cloud API and may require updates when the portal changes.

## Features

- UI-based setup with the email address and password of your Hargassner account
- Automatic installation discovery and selection
- No manual client ID or client secret lookup
- Automatic recovery when Hargassner rotates its public web-client credentials
- Central polling through Home Assistant's `DataUpdateCoordinator`
- Automatic reauthentication when credentials are rejected
- Configurable polling interval, suggested area, and field mappings
- Redacted diagnostics and log messages
- Device software version display when provided by the cloud API
- Czech, English, French, German, Norwegian Bokmål, Polish, and Spanish entity translations

## Tested systems

- **NanoPK:** live-tested login, installation discovery, and widget retrieval
- **Neo-HV 20:** validated with real redacted Home Assistant diagnostics and a
  synthetic regression test for its widget topology

Other Hargassner systems may work when they expose compatible cloud widgets, but
have not yet been verified by this project.

## Entities

Entities are created according to the widget groups returned by your
installation. Depending on the boiler and portal configuration, not every entity
listed below will be available.

### Sensors

| Group | Values |
| --- | --- |
| Heater | State, program, current/target temperature, flue-gas temperature, efficiency |
| Outdoor | Current and average outdoor temperature |
| Buffer | State, charge, capacity (unit unspecified), top/centre/bottom temperatures |
| Boilers | State, current/target temperature and charge for every numbered boiler |
| Heating circuits | State, mode, current/target flow and room temperatures for every numbered circuit |
| Heating controller | Heat-source and requested temperature, when exposed (for example Neo-HV) |

### Binary sensors

- Cloud connectivity
- Heater power state and exhaust guard
- Buffer pump and forced charging
- Pump and forced charging for every numbered boiler
- Activity and pump state for every numbered heating circuit

Numbered boilers and all `HEATING_CIRCUIT_*` widget types are discovered from
the API without an artificial upper limit. Multiple buffer widgets are not yet
created because their numbering scheme has not been observed.

Real NanoPK and Neo-HV measurements also showed optional cloud measurement
channels for oxygen content, return temperatures, heat demand, system pressure,
pellet inventory, humidity and additional buffer positions. These are not yet
entities: they are available only through the separate measurement-history API,
not the more reliable widget response used for regular updates. A direct pellet
consumption channel was not observed.

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

The integration downloads the current Hargassner login page and JavaScript
bundle and extracts the public web-client credentials before logging in. No
public client secret is embedded in this repository. Your Hargassner password is
never sent anywhere except the configured Hargassner base URL.

Existing entries that contain manually configured client credentials remain
supported.

## Options

Open **Settings → Devices & services → Hargassner Cloud → Configure** to change:

- Polling interval in seconds; the default is 300 seconds
- Suggested area
- Mapping overrides as JSON

Saving options automatically reloads the integration.
The minimum polling interval is 30 seconds.

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
update failures and do not ask you to re-enter your password. If Hargassner
changes its web client and the public client credentials can no longer be
discovered, Home Assistant creates a repair issue instead of incorrectly asking
you to change your personal password.

## Diagnostics and privacy

Download diagnostics from **Settings → Devices & services → Hargassner Cloud**.
Passwords, usernames, installation IDs, client credentials, authorization
tokens, names, serial numbers, and common location fields are redacted. API
widgets are reduced to field names and value types; operational values and
resource URLs are not included. A sanitized API status identifies the latest
request phase, outcome, HTTP status, and credential source.

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

The source code and original project artwork are licensed under the MIT License.
See [LICENSE](LICENSE).

The artwork included in this repository is original project artwork and is not a
copy of Hargassner's official logo. Hargassner is a trademark of its respective
owner. This independent project is not affiliated with or endorsed by Hargassner.
