<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Hargassner Cloud-logo" width="400">
</p>

<p align="center"><a href="README.de.md">Deutsch</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | Norsk bokmål | <a href="README.pl.md">Polski</a> | <a href="README.cs.md">Čeština</a></p>

# Hargassner Cloud for Home Assistant

Hargassner Cloud er en tilpasset Home Assistant-integrasjon som leser
varmedata fra Hargassners nettportal og viser dem som sensorer og binærsensorer.

> [!IMPORTANT]
> Dette uavhengige prosjektet er ikke tilknyttet eller godkjent av Hargassner.
> Det bruker et udokumentert sky-API som kan bli endret.

## Funksjoner

- Oppsett i brukergrensesnittet med e-postadressen og passordet til
  Hargassner-kontoen
- Automatisk oppdagelse og valg av installasjoner
- Ingen manuell uthenting av klient-ID eller klienthemmelighet
- Automatisk oppdatering av offentlige nettklientopplysninger
- Samordnet avspørring med `DataUpdateCoordinator`
- Home Assistant-reauthentisering når personlige opplysninger avvises
- Konfigurerbart intervall, foreslått område og felttilordninger
- Sladdede diagnoser og logger
- Ingen kunstig grense for nummererte beredere og varmekretser

## Testede systemer

- **NanoPK:** innlogging, installasjonsoppdagelse og widgethenting er testet mot
  den virkelige tjenesten
- **Neo-HV 20:** validert med ekte, sladdet Home Assistant-diagnostikk og en
  syntetisk regresjonstest av widgettopologien

Andre Hargassner-systemer kan fungere hvis de tilbyr kompatible skywidgeter, men
de er ennå ikke verifisert av dette prosjektet.

## Entiteter

Entitetene avhenger av widgetene installasjonen returnerer: varmeanlegg,
utetemperatur, buffer, beredere og varmekretser. Alle nummererte `BOILER`- og
`HEATING_CIRCUIT_*`-widgeter oppdages, sammen med temperaturer, pumper,
tvungen lading og driftsstatus.

Flere buffere opprettes ikke ennå fordi nummereringsmønsteret i API-et ikke er
kjent.

## Installasjon

### HACS

1. Åpne **HACS → Integrasjoner**.
1. Velg **Egendefinerte repositorier** i menyen med tre prikker.
1. Legg til `https://github.com/m4c3/hass-hargassner-cloud` som
   **Integrasjon**.
1. Installer **Hargassner Cloud** og start Home Assistant på nytt.
1. Åpne **Innstillinger → Enheter og tjenester → Legg til integrasjon**.

### Manuell installasjon

Kopier `custom_components/hargassner_cloud` til Home Assistants
`custom_components`-mappe, start Home Assistant på nytt og legg til
integrasjonen fra brukergrensesnittet.

## Konfigurasjon og alternativer

Oppsettet ber om e-postadressen og passordet til Hargassner-kontoen. Standard
URL er `https://web.hargassner.at`. Hvis kontoen har flere installasjoner,
vises et valg.

Alternativene omfatter oppdateringsintervall (standard 300 sekunder, minst 30),
foreslått område og JSON-baserte felttilordninger. Lagring laster integrasjonen
på nytt automatisk.

## Autentisering

Integrasjonen henter offentlige nettklientopplysninger fra Hargassners aktuelle
påloggingsside. Ingen offentlig klienthemmelighet er innebygd i repositoriet.
Passordet sendes bare til den konfigurerte Hargassner-URL-en.

Et avvist passord starter vanlig reauthentisering. En inkompatibel portalendring
oppretter i stedet et reparasjonsvarsel.

## Diagnostikk og personvern

Diagnosen inneholder bare widget- og feltnavn, datatyper og en sladdet
API-status. Passord, tokens, installasjons-ID-er, driftsverdier og ressurs-URL-er
er fjernet. Kontroller likevel filen før publisering.

## Feilsøking

- **Pålogging mislyktes:** kontroller kontoen på
  [`web.hargassner.at`](https://web.hargassner.at).
- **Ingen forbindelse:** kontroller HTTPS-tilgang og mulig portalvedlikehold.
- **Manglende entiteter:** last ned diagnosen og kontroller widget- og feltnavn;
  en JSON-tilordning kan tilpasse dem.

## Lisens

Kildekoden og prosjektets originale grafikk er lisensiert under MIT-lisensen.
Se [LICENSE](LICENSE). Hargassner er et varemerke som tilhører sin eier.
