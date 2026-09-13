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
- Keep Hargassner API behavior changes minimal and cover them with tests.

## Credentials and privacy

- Never commit usernames, passwords, tokens, installation IDs, captured API
  responses, or private diagnostics.
- Public OAuth web-client credentials may be discovered from the official
  Hargassner frontend. Do not log their values.
- Redact credentials and installation-specific data from diagnostics and logs.
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
mdl README.md CHANGELOG.md CONTRIBUTING.md info.md AGENTS.md
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

- Keep `README.md`, translations, `manifest.json`, `hacs.json`, and `CHANGELOG.md`
  aligned with user-visible changes.
- Update both English and German translations when changing flow text.
- Keep JSON files valid and preserve the minimum supported Home Assistant version.
- Use focused commits with concise imperative messages.

## Before handing off

Confirm that no merge-conflict markers remain, the complete validation suite passes,
and `git status` contains only intentional changes. Report any test that could not be
run, especially the opt-in live API test.
