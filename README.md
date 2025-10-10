<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo.png" alt="Hargassner Cloud Logo" width="400">
</p>

# Home Assistant · Hargassner Cloud 

Diese Custom-Integration nutzt die **PyPI‑Bibliothek [`hargassner`](https://pypi.org/project/hargassner/)**,
um Werte aus der Hargassner Web‑API auszulesen und als Entities in Home Assistant bereitzustellen.

**Features**
- Login über UI (Benutzer, Passwort, Client Secret, Installation‑ID)
- Zentrales Polling via DataUpdateCoordinator
- Sensors für typische Größen (Außen‑/Kessel‑/Abgas‑/Puffer‑Temperatur)
- Reauth‑Flow bei Token‑Fehlern

## HACS-Installation (als Custom Repository)
1. In Home Assistant → **HACS → Integrations → Custom repositories (oben rechts) → Add**  
   - **Repository**: https://github.com/m4c3/hass-hargassner-cloud
   - **Category**: Integration  
   - **Add**
2. Danach taucht **Hargassner Cloud** in HACS auf → **Installieren** → HA neu starten.
3. Integration über **Einstellungen → Geräte & Dienste → Integration hinzufügen** konfigurieren.


**Manuelle Installation**
1. Ordner `custom_components/hargassner_cloud/` aus diesem Repo in deinen HA‑`config/`‑Pfad kopieren.
2. HA neu starten.
3. In Home Assistant: **Einstellungen → Geräte & Dienste → Integration hinzufügen → „Hargassner Cloud“**.
4. Zugangsdaten eingeben:
   - **E‑Mail** (Portal‑Login)
   - **Passwort**
   - **Client Secret** (aus Browser‑Netzwerk‑Tab beim Login ins Hargassner‑Portal)
   - **Installation‑ID** (deine Heizanlage)
5. Nach dem Speichern erscheinen die Sensoren nach kurzer Zeit.

**Hinweis zu Feldern/Widgets**
Je nach Portal/Firmware können Felder leicht variieren. Die Integration mappt standardmäßig:
- `Outdoor.temperature_current` → sensor.outdoor_temperature
- `HEATER.heater_temperature_current` → sensor.boiler_temperature
- `HEATER.smoke_temperature` → sensor.smoke_temperature
- `BUFFER.buffer_top_temperature` → sensor.buffer_top_temperature

Wenn dein JSON abweicht, kannst du in `sensor.py` die **`SENSOR_MAPPINGS`** anpassen.