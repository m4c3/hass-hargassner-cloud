
# Contributing

Danke für deinen Beitrag!

## Entwicklung lokal testen
1. Home Assistant im Dev-Container oder lokal starten.
2. Dieses Repo als `custom_components/hargassner_cloud` in den `config/` Pfad kopieren.
3. Neustarten und Integration über die UI hinzufügen.

## Code-Style
- Python 3.11+
- Befolge die Strukturen gängiger HA-Custom-Integrationen (Config-Flow, Coordinator, Entities).

## Releases
- Version in `custom_components/hargassner_cloud/manifest.json` erhöhen.
- `CHANGELOG.md` aktualisieren.
- Tag im Format `vX.Y.Z` erstellen und pushen (HACS liest Releases).

## Issues / PRs
- Bitte Steps zur Reproduktion + Logs (DEBUG) anhängen.
