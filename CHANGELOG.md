# Changelog

## 0.5.6

- Documented successful live API validation with a Neo-HV 20 system

## 0.5.5

- Documented validation against NanoPK and Neo-HV 20 systems
- Added a privacy-safe live probe for device and firmware metadata
- Added a private live probe for discovering heating measurements and values
- Displayed the cloud-provided device software version in Home Assistant
- Added heater/boiler target and Neo-HV controller temperature sensors
- Read outdoor temperatures from Neo-HV controller widgets without a heater widget
- Added boiler/heating-circuit status, heating-circuit mode, and buffer capacity sensors
- Documented current entities and additional observed measurement channels

## 0.5.4

- Distinguished scheduled Hargassner maintenance from web-client credential changes
- Avoided creating heater and buffer binary sensors when their widgets are absent

## 0.5.3

- Added the non-sensitive heater device type to sanitized diagnostics
- Added localized on/off states for heater and buffer status sensors

## 0.5.2

- Distinguished Hargassner web-client changes from personal authentication errors
- Added a translated repair issue for web-client credential failures
- Added config-entry context to the data update coordinator
- Enforced a minimum polling interval of 30 seconds
- Added integration system-health information
- Replaced raw API diagnostics and debug responses with sanitized structural data
- Enabled localized entity names and fixed duplicated heating-circuit display numbers
- Added French, Spanish, Norwegian Bokmål, Polish, and Czech entity translations
- Discover any number of numbered boilers and heating circuits from API widgets
- Added French, Spanish, Norwegian Bokmål, Polish, and Czech README files
- Added a German README
- Removed the unnecessary integration logger declaration from the manifest

## 0.5.1

- Removed the embedded public web-client credential
- Discover web-client credentials before authentication
- Added a security policy and safer public issue guidance
- Added monthly Dependabot updates
- Pinned GitHub Actions to immutable commit SHAs
- Documented project artwork licensing

## 0.5.0

- Modernized config and options flows for current Home Assistant releases
- Added automatic installation discovery and selection
- Removed manual client ID and client secret setup
- Added automatic recovery when public web-client credentials rotate
- Added Home Assistant reauthentication support
- Migrated runtime state to `ConfigEntry.runtime_data`
- Fixed same-endpoint retry after an expired token
- Applied mapping overrides to sensors and binary sensors
- Redacted API diagnostics and improved error visibility
- Added automated tests, Ruff, Mypy, and Markdown validation
- Increased the default polling interval from 30 to 300 seconds

## 0.1.1

- Added HACS metadata (`hacs.json`) and `info.md`
- Added HACS and Hassfest validation workflows

## 0.1.0

- Initial config flow and `DataUpdateCoordinator` implementation
- Added outdoor, boiler, flue-gas, and buffer temperature sensors
