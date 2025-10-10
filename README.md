
# Home Assistant · Hargassner Cloud (Custom Integration ohne MQTT)

Diese Custom-Integration nutzt die **PyPI‑Bibliothek [`hargassner`](https://pypi.org/project/hargassner/)**,
um Werte aus der Hargassner Web‑API auszulesen und als **Entities** in Home Assistant bereitzustellen.
Kein MQTT, keine REST‑YAML‑Bastelei – alles per **Config‑Flow** in der UI.

**Features**
- Login über UI (Benutzer, Passwort, Client Secret, Installation‑ID)
- Zentrales Polling via DataUpdateCoordinator
- Sensors für typische Größen (Außen‑/Kessel‑/Abgas‑/Puffer‑Temperatur)
- Reauth‑Flow bei Token‑Fehlern
- Übersetzungen (de/en)

**Installation**
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

**Lizenz**
MIT


---

## HACS-Installation (als Custom Repository)
1. **Repository veröffentlichen** (GitHub) und die URL merken (z. B. `https://github.com/DEIN_USER/hass-hargassner-cloud`).
2. In Home Assistant → **HACS → Integrations → Custom repositories (oben rechts) → Add**  
   - **Repository**: deine GitHub-URL  
   - **Category**: Integration  
   - **Add**.
3. Danach taucht **Hargassner Cloud** in HACS auf → **Installieren** → HA neu starten.
4. Integration über **Einstellungen → Geräte & Dienste → Integration hinzufügen** konfigurieren.

> Alternativ: Ohne HACS einfach den Ordner `custom_components/hargassner_cloud/` manuell in `config/` kopieren.


---

## Repo-Setup (Remote & Push)
```bash
git init
git add .
git commit -m "chore: init HACS-ready 0.1.2"
git branch -M main
git remote add origin git@github.com:m4c3/hass-hargassner-cloud.git   # SSH
# oder per HTTPS:
# git remote add origin https://github.com/m4c3/hass-hargassner-cloud.git
git push -u origin main
git tag v0.1.2
git push origin v0.1.2
```

## HACS: Custom Repository hinzufügen
- Repository URL: https://github.com/m4c3/hass-hargassner-cloud
- Category: Integration

## Brands-PR (optional, für Store-Logos)
Lege in `home-assistant/brands` einen Ordner an:
`custom_integrations/hargassner_cloud/` mit `icon.png` und `logo.png` (siehe `brands_assets/` als Platzhalter).
