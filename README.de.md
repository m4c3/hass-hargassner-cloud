<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Hargassner-Cloud-Logo" width="400">
</p>

<p align="center">Deutsch | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.nb.md">Norsk bokmål</a> | <a href="README.pl.md">Polski</a> | <a href="README.cs.md">Čeština</a></p>

# Hargassner Cloud für Home Assistant

Hargassner Cloud ist eine benutzerdefinierte Home-Assistant-Integration. Sie
liest Heizungsdaten aus dem Hargassner-Webportal und stellt sie als Sensoren und
Binärsensoren bereit.

> [!IMPORTANT]
> Dieses Projekt ist weder mit Hargassner verbunden noch von Hargassner
> unterstützt. Es verwendet eine undokumentierte Cloud-API und muss eventuell
> angepasst werden, wenn sich das Portal ändert.

## Funktionen

- Einrichtung über die Benutzeroberfläche mit E-Mail-Adresse und Passwort des
  Hargassner-Kontos
- Automatische Erkennung und Auswahl der verfügbaren Anlagen
- Kein manuelles Heraussuchen von Client-ID oder Client-Secret
- Automatische Aktualisierung rotierter öffentlicher Web-Client-Zugangsdaten
- Zentrale Abfragen über Home Assistants `DataUpdateCoordinator`
- Automatische erneute Authentifizierung bei abgelehnten Benutzerdaten
- Einstellbares Abfrageintervall, vorgeschlagener Bereich und Feld-Mappings
- Bereinigte Diagnose- und Protokolldaten
- Anzeige der Gerätesoftwareversion, wenn sie von der Cloud-API bereitgestellt wird
- Deutsche, englische, französische, spanische, norwegische, polnische und
  tschechische Entitätsübersetzungen

## Getestete Anlagen

- **NanoPK:** Anmeldung, Anlagenerkennung und Widget-Abruf wurden live getestet
- **Neo-HV 20:** Anmeldung, Anlagenerkennung und Widget-Abruf wurden live getestet;
  die Widget-Topologie ist zusätzlich durch einen synthetischen Regressionstest abgedeckt

Weitere Hargassner-Anlagen können funktionieren, wenn sie kompatible
Cloud-Widgets bereitstellen, wurden von diesem Projekt aber noch nicht geprüft.

## Entitäten

Die Entitäten werden entsprechend den Widget-Gruppen der Anlage erstellt. Je
nach Kessel und Portalkonfiguration sind möglicherweise nicht alle nachfolgend
genannten Entitäten vorhanden.

### Sensoren

| Gruppe | Werte |
| --- | --- |
| Heizung | Status, Programm, Kessel-Ist-/Solltemperatur, Rauchgastemperatur, Effizienz |
| Außenbereich | Aktuelle und durchschnittliche Außentemperatur |
| Pufferspeicher | Status, Ladung, Kapazität (Einheit unbekannt), Temperatur oben/Mitte/unten |
| Boiler | Status, Ist-/Solltemperatur und Ladung aller nummerierten Boiler |
| Heizkreise | Status, Modus sowie aktuelle und gewünschte Vorlauf- und Raumtemperatur |
| Heizkreisregler | Wärmequellen- und Anforderungstemperatur, falls vorhanden (z. B. Neo-HV) |

### Binärsensoren

- Cloud-Verbindung
- Kesselbetrieb und Abgasüberwachung
- Pufferpumpe und Zwangsladung
- Pumpe und Zwangsladung aller nummerierten Boiler
- Aktivität und Pumpenstatus aller nummerierten Heizkreise

Nummerierte Boiler und alle Widget-Typen nach dem Muster
`HEATING_CIRCUIT_*` werden ohne künstliche Obergrenze aus der API erkannt.
Mehrere Pufferspeicher werden noch nicht erzeugt, weil ihr Nummerierungsschema
bisher nicht beobachtet wurde.

Reale Messdaten von NanoPK und Neo-HV zeigen außerdem optionale Kanäle für
Sauerstoffgehalt, Rücklauftemperaturen, Wärmeanforderung, Systemdruck,
Pellet-Lagerstand, Luftfeuchtigkeit und weitere Pufferpositionen. Diese sind
noch keine Entitäten: Sie stehen nur über die separate Messwerthistorie zur
Verfügung, nicht über die zuverlässigere Widget-Antwort der regulären
Aktualisierung. Ein direkter Kanal für den Pelletverbrauch wurde nicht gefunden.

## Installation

### HACS

1. **HACS → Integrationen** öffnen.
1. Im Drei-Punkte-Menü **Benutzerdefinierte Repositories** auswählen.
1. `https://github.com/m4c3/hass-hargassner-cloud` als **Integration**
   hinzufügen.
1. **Hargassner Cloud** installieren und Home Assistant neu starten.
1. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen und
   **Hargassner Cloud** auswählen.

### Manuelle Installation

1. `custom_components/hargassner_cloud` in das Verzeichnis
   `custom_components` der Home-Assistant-Konfiguration kopieren.
1. Home Assistant neu starten.
1. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen und
   **Hargassner Cloud** auswählen.

## Konfiguration

Der Einrichtungsdialog fragt folgende Angaben ab:

| Feld | Beschreibung |
| --- | --- |
| E-Mail | E-Mail-Adresse für das Hargassner-Webportal |
| Passwort | Passwort des Hargassner-Kontos |
| Basis-URL | Optional; Standard ist `https://web.hargassner.at` |
| Bereich | Optional vorgeschlagener Home-Assistant-Bereich |

Nach der Anmeldung ermittelt die Integration alle Anlagen des Kontos. Eine
einzelne Anlage wird automatisch ausgewählt. Bei mehreren Anlagen erscheint
eine Auswahlliste.

Vor der Anmeldung lädt die Integration die aktuelle Hargassner-Anmeldeseite und
deren JavaScript-Bundle. Daraus liest sie die öffentlichen
Web-Client-Zugangsdaten. In diesem Repository ist kein öffentliches
Client-Secret eingebettet. Das Hargassner-Passwort wird ausschließlich an die
konfigurierte Hargassner-Basis-URL gesendet.

Bestehende Einträge mit früher manuell gespeicherten Client-Zugangsdaten werden
weiterhin unterstützt.

## Optionen

Unter **Einstellungen → Geräte & Dienste → Hargassner Cloud → Konfigurieren**
können folgende Werte geändert werden:

- Abfrageintervall in Sekunden; Standard sind 300, Minimum sind 30 Sekunden
- Vorgeschlagener Bereich
- Mapping-Overrides als JSON

Nach dem Speichern wird die Integration automatisch neu geladen.

### Mapping-Overrides

Mit Mapping-Overrides kann eine Entität ohne Codeänderung ein anderes
Widget-Feld lesen. Damit eine Anpassung wirksam wird, sind `widget` und `field`
erforderlich; `number` ist optional.

```json
{
  "heater_temp_current": {
    "widget": "HEATER",
    "field": "heater_temperature_current"
  },
  "hc1_room_temp_current": {
    "widget": "HEATING_CIRCUIT_RADIATOR",
    "field": "room_temperature_current",
    "number": "1"
  }
}
```

Ungültiges JSON wird im Optionsdialog abgelehnt. Unbekannte Entitätsschlüssel
werden ignoriert. Overrides funktionieren für Sensoren und Binärsensoren.

## Anmeldung und erneute Authentifizierung

Die Integration bezieht ein Bearer-Token vom Hargassner-Anmeldeendpunkt. Werden
die persönlichen Zugangsdaten abgelehnt oder läuft die Autorisierung ab, startet
Home Assistant den üblichen Reauthentifizierungsdialog. Vorübergehende Netzwerk-
und Serverfehler werden erneut versucht und verlangen keine erneute
Passworteingabe.

Kann die Integration nach einer Portaländerung die öffentlichen
Web-Client-Zugangsdaten nicht mehr ermitteln, erstellt Home Assistant stattdessen
einen Reparaturhinweis. Dadurch wird nicht fälschlich eine Änderung des
persönlichen Passworts verlangt.

## Diagnose und Datenschutz

Diagnosedaten können unter **Einstellungen → Geräte & Dienste → Hargassner
Cloud** heruntergeladen werden. Passwörter, Benutzernamen, Anlagen-IDs,
Client-Zugangsdaten, Autorisierungstoken, Namen, Seriennummern und übliche
Ortsfelder werden entfernt. API-Widgets werden auf Feldnamen und Datentypen
reduziert; Betriebswerte und Ressourcen-URLs sind nicht enthalten. Ein
bereinigter API-Status nennt die letzte Anfragephase, deren Ergebnis, den
HTTP-Status und die Art der verwendeten Client-Zugangsdaten.

Bitte die erzeugte Datei trotzdem vor dem Teilen prüfen, da die undokumentierte
API künftig neue Felder liefern könnte.

## Entwicklung

Eine virtuelle Umgebung erstellen und die Entwicklungswerkzeuge installieren:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install homeassistant pytest ruff mypy
```

Prüfungen ausführen:

```bash
python -m compileall custom_components tests
pytest
ruff format --check custom_components tests
ruff check custom_components tests
mypy custom_components tests
```

Die Tests decken Wertkonvertierung, Widget-Suche, Mapping-Overrides,
Authentifizierungsfehler, Rotation der Web-Client-Zugangsdaten, erneute Abfragen
desselben Endpunkts und die Bereinigung von Diagnosedaten ab.

## Fehlerbehebung

### Anmeldung fehlgeschlagen

E-Mail und Passwort durch eine Anmeldung bei
[`web.hargassner.at`](https://web.hargassner.at) prüfen. Ein Client-Secret muss
nicht mehr über die Entwicklerwerkzeuge des Browsers ermittelt werden.

### Verbindung nicht möglich

Prüfen, ob Home Assistant die konfigurierte Basis-URL über HTTPS erreichen kann.
Auch Wartungsarbeiten am Portal oder eine Begrenzung der Anfragen können
vorübergehende Fehler verursachen.

### Entitäten fehlen

Die Integration erstellt nur Sensorgruppen, die in der API-Antwort vorhanden
sind. Verwendet der Kessel andere Widget- oder Feldnamen, können Diagnosedaten
heruntergeladen und Mapping-Overrides eingerichtet werden.

## Lizenz

Quellcode und originale Projektgrafiken stehen unter der MIT-Lizenz. Siehe
[LICENSE](LICENSE).

Die Grafiken in diesem Repository wurden eigens für dieses Projekt erstellt und
sind keine Kopie des offiziellen Hargassner-Logos. Hargassner ist eine Marke des
jeweiligen Inhabers. Dieses unabhängige Projekt ist weder mit Hargassner
verbunden noch von Hargassner unterstützt.
