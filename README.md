<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Hargassner Cloud Logo" width="400">
</p>

# Home Assistant · Hargassner Cloud

This custom integration uses the **PyPI library [`hargassner`](https://pypi.org/project/hargassner/)**  
to read data from the Hargassner Web-API and provide it as entities in Home Assistant.

**Features**
- Login via UI (username, password, client secret, installation ID)
- Central polling through a DataUpdateCoordinator
- Sensors for common metrics (outdoor / boiler / exhaust / buffer temperature)
- Automatic reauthentication when token errors occur

## HACS installation (as a Custom Repository)
1. In Home Assistant → **HACS → Integrations → Custom repositories (top right) → Add**  
   - **Repository**: https://github.com/m4c3/hass-hargassner-cloud  
   - **Category**: Integration  
   - **Add**
2. Afterwards, **Hargassner Cloud** will appear in HACS → **Install** → restart Home Assistant.
3. Add the integration in **Settings → Devices & Services → Add Integration → “Hargassner Cloud”**.

## Manual installation
1. Copy the folder `custom_components/hargassner_cloud/` from this repository into your HA `config/` directory.
2. Restart Home Assistant.
3. In Home Assistant: **Settings → Devices & Services → Add Integration → “Hargassner Cloud”**.
4. Enter your credentials:
   - **E-mail** (portal login)
   - **Password**
   - **Client Secret** (found via the browser’s network tab when logging into the Hargassner web portal)
   - **Installation ID** (your heating system ID)
5. After saving, the sensors will appear within a short time.

**Note about fields/widgets**
Depending on your portal version or firmware, JSON field names may differ slightly.  
The integration maps the following by default:
- `Outdoor.temperature_current` → `sensor.outdoor_temperature`
- `HEATER.heater_temperature_current` → `sensor.boiler_temperature`
- `HEATER.smoke_temperature` → `sensor.smoke_temperature`
- `BUFFER.buffer_top_temperature` → `sensor.buffer_top_temperature`

If your JSON structure differs, you can adjust the **`SENSOR_MAPPINGS`** section in `sensor.py`.
