# Contributing

Thanks for contributing to **Hargassner Cloud**!

## 🧪 Local development

1. Run Home Assistant locally (e.g., via [Devcontainer](https://developers.home-assistant.io/docs/development_environment/) or a test instance).
2. Copy this repository to your HA `config/` path under
   `custom_components/hargassner_cloud/`.
3. Restart Home Assistant and add the integration through the UI.

## 🧹 Code style & structure

* Use **Python 3.11+**
* Follow the official [Home Assistant developer guidelines](https://developers.home-assistant.io/docs/integration_fetching_data/)
* Keep the structure modular:

  * `__init__.py` → setup, coordinator
  * `sensor.py` → entity definitions
  * `config_flow.py` → UI config
  * `diagnostics.py` → diagnostics export
* Avoid hardcoding credentials or URLs.

## 🧾 Versioning & releases

1. Increase the version in
   `custom_components/hargassner_cloud/manifest.json`

2. Update the **CHANGELOG.md** with your changes.

3. Create a Git tag following semantic versioning, e.g.:

   ```bash
   git tag v0.2.1
   git push origin v0.2.1
   ```

4. HACS will automatically detect new tagged releases.

## 🧮 Testing

* Test login flow and sensor updates with real API responses.

* Validate the manifest with:

  ```bash
  pipx run homeassistant script.hassfest --action validate
  ```

* Check for YAML and Python syntax errors before committing.

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
