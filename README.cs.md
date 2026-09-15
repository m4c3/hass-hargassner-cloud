<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Logo Hargassner Cloud" width="400">
</p>

<p align="center"><a href="README.de.md">Deutsch</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.nb.md">Norsk bokmål</a> | <a href="README.pl.md">Polski</a> | Čeština</p>

# Hargassner Cloud pro Home Assistant

Hargassner Cloud je vlastní integrace pro Home Assistant. Čte data vytápění z
webového portálu Hargassner a zpřístupňuje je jako senzory a binární senzory.

> [!IMPORTANT]
> Tento nezávislý projekt není spojen se společností Hargassner ani jí není
> podporován. Používá nedokumentované cloudové API, které se může změnit.

## Funkce

- Nastavení v uživatelském rozhraní pomocí e-mailu a hesla účtu Hargassner
- Automatické nalezení a výběr instalací
- Není nutné ručně hledat ID klienta ani tajný klíč
- Automatická aktualizace veřejných údajů webového klienta
- Koordinované dotazování pomocí `DataUpdateCoordinator`
- Opětovné ověření v Home Assistantu při odmítnutí osobních údajů
- Nastavitelný interval, navržená oblast a mapování polí
- Redigované diagnostické údaje a protokoly
- Zobrazení verze softwaru zařízení, pokud ji poskytuje cloudové API
- Bez umělého omezení počtu číslovaných bojlerů a topných okruhů

## Testované systémy

- **NanoPK:** přihlášení, vyhledání instalací a načítání widgetů bylo otestováno
  proti skutečné službě
- **Neo-HV 20:** ověřeno pomocí skutečných redigovaných diagnostických dat Home
  Assistant a syntetického regresního testu topologie widgetů

Další systémy Hargassner mohou fungovat, pokud poskytují kompatibilní cloudové
widgety, ale tento projekt je zatím neověřil.

## Entity

Entity závisí na widgetech vrácených instalací: vytápění, venkovní teplota,
akumulační nádrž, bojlery a topné okruhy. Rozpoznají se všechny číslované
widgety `BOILER` a `HEATING_CIRCUIT_*`, včetně teplot, čerpadel, vynuceného
nabíjení a provozních stavů.

Více akumulačních nádrží se zatím nevytváří, protože jejich způsob číslování v
API nebyl pozorován.

## Instalace

### HACS

1. Otevřete **HACS → Integrace**.
1. V nabídce se třemi tečkami vyberte **Vlastní repozitáře**.
1. Přidejte `https://github.com/m4c3/hass-hargassner-cloud` jako **Integraci**.
1. Nainstalujte **Hargassner Cloud** a restartujte Home Assistant.
1. Otevřete **Nastavení → Zařízení a služby → Přidat integraci**.

### Ruční instalace

Zkopírujte `custom_components/hargassner_cloud` do adresáře
`custom_components`, restartujte Home Assistant a přidejte integraci z
uživatelského rozhraní.

## Konfigurace a možnosti

Nastavení požaduje e-mail a heslo účtu Hargassner. Výchozí URL je
`https://web.hargassner.at`. Pokud účet obsahuje více instalací, zobrazí se
jejich výběr.

Možnosti umožňují změnit interval aktualizace (výchozí 300 sekund, minimum 30),
navrženou oblast a mapování polí ve formátu JSON. Uložení integraci automaticky
znovu načte.

## Ověřování

Integrace získává veřejné údaje webového klienta z aktuální přihlašovací stránky
Hargassner. Repozitář neobsahuje žádný veřejný tajný klíč klienta. Heslo se
odesílá pouze na nakonfigurovanou URL Hargassner.

Odmítnuté heslo spustí standardní opětovné ověření. Nekompatibilní změna portálu
místo toho vytvoří upozornění v Opravách.

## Diagnostika a soukromí

Diagnostika obsahuje pouze názvy widgetů a polí, datové typy a redigovaný stav
API. Hesla, tokeny, ID instalací, provozní hodnoty a URL prostředků jsou
odstraněny. Přesto soubor před zveřejněním zkontrolujte.

## Řešení problémů

- **Přihlášení selhalo:** ověřte účet na
  [`web.hargassner.at`](https://web.hargassner.at).
- **Nelze se připojit:** zkontrolujte HTTPS a případnou údržbu portálu.
- **Chybějící entity:** stáhněte diagnostiku a zkontrolujte názvy widgetů a polí;
  mapování JSON je může přizpůsobit.

## Licence

Zdrojový kód a původní grafika projektu jsou licencovány pod licencí MIT. Viz
[LICENSE](LICENSE). Hargassner je ochranná známka příslušného vlastníka.
