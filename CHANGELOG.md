# Changelog

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
