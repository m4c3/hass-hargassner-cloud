# AGENTS.md

This file provides working conventions for automated coding agents contributing to
this repository.

## Project scope

This repository contains the `hargassner_cloud` custom integration for Home
Assistant. Keep changes focused on compatibility, correctness, security, and the
existing Hargassner Cloud functionality. Avoid unrelated refactoring.

The integration source is located in:

```text
custom_components/hargassner_cloud/
```

## Development rules

- Preserve the existing entity names, unique IDs, mappings, and configuration data
  unless a migration is provided.
- Use current Home Assistant config-entry APIs and store runtime state in
  `ConfigEntry.runtime_data`.
- Treat authentication failures as `ConfigEntryAuthFailed` where Home Assistant
  should initiate reauthentication.
- Keep options in `entry.options` and configuration credentials in `entry.data`.
- Let `OptionsFlowWithReload` reload the entry after accepted option changes.
- Do not catch `Exception` broadly around entity updates or API parsing. Catch the
  expected exceptions and preserve useful error context.
- Retry the same API endpoint after renewing authentication. Do not silently advance
  to a fallback endpoint following a 401 or 403 response.
- Distinguish personal authentication failures, public web-client credential
  changes, scheduled Hargassner maintenance, and general connection failures. Do
  not create a credential repair issue for a temporary maintenance outage.
- Keep Hargassner API behavior changes minimal and cover them with tests.
- Do not assume that every installation exposes `HEATER` or `BUFFER`. Discover
  optional and numbered widgets from the returned payload. Preserve compatibility
  with the observed NanoPK and Neo-HV widget schemas using synthetic tests.

## Credentials and privacy

- Never commit usernames, passwords, tokens, installation IDs, captured API
  responses, or private diagnostics.
- Public OAuth web-client credentials may be discovered from the official
  Hargassner frontend. Do not log their values.
- Redact credentials and installation-specific data from diagnostics and logs.
- Diagnostics may expose explicitly allowlisted, non-sensitive model information,
  such as `device_type`, but must not expose user-defined device names, serial
  numbers, locations, measurements, operating values, or parameter values.
- Keep locally supplied diagnostic files under `.private/`; derive only synthetic,
  non-identifying fixtures or tests from their structure.
- Do not add real credentials to fixtures, snapshots, `.env` files, or CI secrets.
- Use the interactive smoke test or environment variables for live validation.

## Tests and validation

Run the complete local validation suite after substantive changes:

```bash
.venv/bin/pytest -q
.venv/bin/ruff format --check custom_components tests scripts
.venv/bin/ruff check custom_components tests scripts
.venv/bin/mypy custom_components tests scripts
python -m compileall -f custom_components tests scripts
mdl README*.md CHANGELOG.md CONTRIBUTING.md info.md AGENTS.md
git diff --check
```

Add or update tests for behavioral changes. Tests must not require network access by
default.

The real cloud test is explicitly opt-in and must remain skipped when credentials
are absent:

```bash
read -r -p "Hargassner email: " HARGASSNER_USERNAME
read -r -s -p "Hargassner password: " HARGASSNER_PASSWORD
echo
export HARGASSNER_USERNAME HARGASSNER_PASSWORD
.venv/bin/pytest -m live -q
unset HARGASSNER_USERNAME HARGASSNER_PASSWORD
```

Do not enable the live test in public CI.

## Documentation and metadata

- Keep all `README*.md` files, translations, `manifest.json`, `hacs.json`, and
  `CHANGELOG.md` aligned with user-visible changes.
- The supported locales are English (`en`), German (`de`), French (`fr`), Spanish
  (`es`), Norwegian Bokmål (`nb`), Polish (`pl`), and Czech (`cs`). Update the
  relevant sections in every supported translation file when changing user-facing
  text or entity state translations, and keep their translation keys aligned.
- Keep `strings.json` aligned with the English and German flow text used by Home
  Assistant.
- Keep `README.md`, `README.de.md`, `README.fr.md`, `README.es.md`, `README.nb.md`,
  `README.pl.md`, and `README.cs.md` aligned when documentation changes apply to all
  users.
- Keep JSON files valid and preserve the minimum supported Home Assistant version.
- Add changes made after a release under an `Unreleased` changelog section until
  the next version is prepared.
- Use focused commits with concise imperative messages.

## Before handing off

Confirm that no merge-conflict markers remain, the complete validation suite passes,
and `git status` contains only intentional changes. Report any test that could not be
run, especially the opt-in live API test.
