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

## Dependency pull requests

- Review Dependabot pull requests individually; do not merge them solely because
  their existing checks are green.
- Confirm the changed dependency names and versions, inspect upstream release notes
  for compatibility or security concerns, and ensure the pull request is current
  with `main` before merging.
- Run or verify the complete validation suite on the final merge commit. Dependency
  updates normally do not require an integration release unless they affect shipped
  code, compatibility, or users.
- Do not merge, close, rebase, or otherwise modify a pull request without explicit
  user authorization.

## Release process

Only push commits, create tags, or publish a GitHub release when the user explicitly
requests it. Use the following sequence for a release:

1. Confirm that `main` contains only the intended changes and that no relevant open
   pull request should be included first.
1. Select the next semantic version. Move the current `Unreleased` changelog notes
   to a heading for that version and update `version` in
   `custom_components/hargassner_cloud/manifest.json`.
1. Run the complete local validation suite documented above. The opt-in live API
   test is required only when the release changes authentication or cloud API
   behavior and credentials are available; state clearly when it was not run.
1. Commit the metadata as `Prepare release X.Y.Z` and create an annotated
   `vX.Y.Z` tag on that exact commit.
1. Build the HACS/manual-installation archive from the tagged integration tree, not
   from uncommitted files:

   ```bash
   git archive --format=zip \
     --prefix=hargassner_cloud/ \
     --output=.dist/hargassner_cloud-X.Y.Z.zip \
     vX.Y.Z:custom_components/hargassner_cloud
   ```

1. Test the ZIP with `unzip -t`, read its embedded `manifest.json` to confirm the
   version, and calculate its SHA-256 checksum.
1. Push `main` and the release tag. Wait for the `tests`, `hassfest`, and `hacs`
   GitHub Actions jobs for the tagged commit to succeed.
1. Publish a non-draft, non-prerelease GitHub release for the tag. Use concise notes
   derived from the changelog and attach the verified ZIP.
1. Verify the published tag, release metadata, downloadable asset, and clean local
   branch. Report the release URL, commit, asset name, checksum, and CI result.
1. Add a new `Unreleased` section when the first subsequent change is made.

## Before handing off

Confirm that no merge-conflict markers remain, the complete validation suite passes,
and `git status` contains only intentional changes. Report any test that could not be
run, especially the opt-in live API test.
