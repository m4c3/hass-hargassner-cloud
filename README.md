<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Hargassner Cloud Logo" width="400">
</p>

# Home Assistant · Hargassner Cloud

This custom integration connects directly to the **Hargassner Web API**  
to provide live heating data as entities in Home Assistant — without any extra dependencies.

---

### ✨ Features
- Simple login via UI (username, password, client secret, installation ID)
- Central polling using Home Assistant’s `DataUpdateCoordinator`
- Sensors for key metrics (outdoor, boiler, exhaust, buffer, and heating circuits)
- Automatic reauthentication when tokens expire
- Binary sensors for device states (online, pumps, charging, etc.)
- Options dialog for scan interval, area, and mapping overrides

---

## 🧰 Installation

### via HACS (recommended)
1. In Home Assistant → **HACS → Integrations → Custom repositories (top right) → Add**
   - **Repository**: https://github.com/m4c3/hass-hargassner-cloud  
   - **Category**: Integration
2. After adding, **Hargassner Cloud** will appear in HACS → install it and restart Home Assistant.
3. Add the integration via  
   **Settings → Devices & Services → Add Integration → “Hargassner Cloud”**

### Manual installation
1. Copy the folder `custom_components/hargassner_cloud/` into your Home Assistant `config/` directory.
2. Restart Home Assistant.
3. Add the integration in  
   **Settings → Devices & Services → Add Integration → “Hargassner Cloud”**
4. Enter your credentials:
   - **E-mail** (portal login)
   - **Password**
   - **Client Secret** (from browser network tab when logging into the Hargassner web portal)
   - **Installation ID** (your heating system ID)

After saving, the sensors will appear automatically within a short time.

---

## ⚙️ Default Field Mappings

Depending on your portal version or firmware, JSON field names may differ slightly.  
By default, the integration maps values like:

| API Field | Entity ID |
|------------|------------|
| `HEATER.heater_temperature_current` | `sensor.heater_temp_current` |
| `HEATER.smoke_temperature` | `sensor.heater_smoke_temp` |
| `BUFFER.buffer_temperature_top` | `sensor.buffer_temp_top` |
| `Outdoor.temperature_current` | `sensor.outdoor_temp` |

If your API delivers different field names, you can easily override them via the **Options dialog** (see below).

---

## 🧩 Advanced Configuration

In the integration’s **Options dialog**  
(Settings → Devices & Services → Hargassner Cloud → Configure)  
you can define **Mapping Overrides** as JSON (since version 0.4).

This allows you to remap data points from the Hargassner API to entities — **without editing any code**.

### Example

```json
{
  "heater_temp_current": { "widget": "HEATER", "field": "heater_temperature_current" },
  "hc1_room_temp_current": { "widget": "HEATING_CIRCUIT_RADIATOR", "field": "room_temperature_current", "number": "1" },
  "hc2_room_temp_current": { "widget": "HEATING_CIRCUIT_FLOOR", "field": "room_temperature_current", "number": "2" }
}
Notes
Keys ("heater_temp_current", "hc1_room_temp_current", etc.) correspond to your entity IDs
(e.g., sensor.heater_temp_current).

Fields "widget", "field", and "number" override the internal defaults.

Multiple overrides can be defined at once — unknown keys are ignored safely.

Make sure the JSON syntax is valid (you can check with any online JSON validator).

After saving, the changes take effect on the next update or after reloading the integration.

🧠 Diagnostics & Logging
A diagnostics file is available under
Settings → Devices & Services → Hargassner Cloud → Download diagnostics
Sensitive data like passwords, tokens, and secrets are automatically redacted in logs and diagnostics.
