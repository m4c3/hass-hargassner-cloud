# Contributing

Thanks for contributing to **Hargassner Cloud**!

## 🧪 Local development

1. Run Home Assistant locally (e.g., via [Devcontainer](https://developers.home-assistant.io/docs/development_environment/) or a test instance).
1. Copy this repository to your HA `config/` path under
   `custom_components/hargassner_cloud/`.
1. Restart Home Assistant and add the integration through the UI.

## 🧹 Code style & structure

* Use **Python 3.14**
* Follow the official [Home Assistant developer guidelines](https://developers.home-assistant.io/docs/integration_fetching_data/)
* Keep setup and coordinator code in `__init__.py`
* Keep entity definitions in their platform modules
* Keep UI configuration in `config_flow.py` and `options_flow.py`
* Keep diagnostics export in `diagnostics.py`
* Never hardcode user credentials or tokens.

## 🧾 Versioning & releases

1. Increase the version in
   `custom_components/hargassner_cloud/manifest.json`

1. Update the **CHANGELOG.md** with your changes.

1. Create a Git tag following semantic versioning, e.g.:

   ```bash
   git tag v0.2.1
   git push origin v0.2.1
   ```

1. HACS will automatically detect new tagged releases.

## 🧮 Testing

* Run the automated checks:

  ```bash
  python -m compileall custom_components tests
  pytest
  ruff format --check custom_components tests
  ruff check custom_components tests
  mypy custom_components tests
  mdl README*.md CHANGELOG.md CONTRIBUTING.md info.md
  ```

* Test login and sensor updates against a real installation before release.

To inspect read-only device and firmware metadata without printing installation
IDs, names, serial numbers, tokens, or full API responses, run:

```bash
.venv/bin/python -m scripts.live_device_probe
```

Review the output before sharing it publicly. The probe prints only allowlisted
version-code values plus the paths and types of device fields; all other values
are omitted.

To inspect the available heating measurements, their units, and their current
values, run the separate private probe:

```bash
.venv/bin/python -m scripts.live_measurement_probe
```

Its output intentionally contains real operating values. Keep it under `.private/`
and do not attach it to a public issue without reviewing it first. Authentication
data and stable installation/device identifiers are automatically redacted.

## 🐞 Issues & pull requests

When submitting issues:

* Include **steps to reproduce**
* Attach **logs or diagnostics JSON** if possible
* Specify **Home Assistant** and **integration version**

When submitting PRs:

* Keep changes atomic and well-described
* Link to any related issue numbers

---

💬 **Tip:** For general questions, use the [Discussions](https://github.com/m4c3/hass-hargassner-cloud/discussions) tab instead of creating issues.
