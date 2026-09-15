<p align="center">
  <img src="https://github.com/m4c3/hass-hargassner-cloud/raw/main/brands_assets/logo-crop.jpg" alt="Logo Hargassner Cloud" width="400">
</p>

<p align="center"><a href="README.de.md">Deutsch</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.nb.md">Norsk bokmål</a> | Polski | <a href="README.cs.md">Čeština</a></p>

# Hargassner Cloud dla Home Assistant

Hargassner Cloud to niestandardowa integracja Home Assistant. Odczytuje dane
grzewcze z portalu Hargassner i udostępnia je jako sensory oraz sensory binarne.

> [!IMPORTANT]
> Ten niezależny projekt nie jest powiązany ani wspierany przez firmę
> Hargassner. Korzysta z nieudokumentowanego API, które może się zmienić.

## Funkcje

- Konfiguracja w interfejsie przy użyciu adresu e-mail i hasła konta Hargassner
- Automatyczne wykrywanie i wybór instalacji
- Brak ręcznego wyszukiwania identyfikatora i sekretu klienta
- Automatyczne aktualizowanie publicznych danych klienta webowego
- Wspólne odpytywanie przez `DataUpdateCoordinator`
- Ponowne uwierzytelnianie po odrzuceniu danych użytkownika
- Konfigurowalny interwał, sugerowany obszar i mapowania pól
- Oczyszczone diagnostyki i logi
- Wyświetlanie wersji oprogramowania urządzenia udostępnionej przez API chmurowe
- Brak sztucznego limitu numerowanych bojlerów i obiegów grzewczych

## Przetestowane systemy

- **NanoPK:** logowanie, wykrywanie instalacji i pobieranie widżetów przetestowano
  z rzeczywistą usługą
- **Neo-HV 20:** zweryfikowano przy użyciu rzeczywistych, zredagowanych danych
  diagnostycznych Home Assistant oraz syntetycznego testu regresji topologii widżetów

Inne systemy Hargassner mogą działać, jeśli udostępniają zgodne widżety chmurowe,
ale nie zostały jeszcze zweryfikowane przez ten projekt.

## Encje

Encje zależą od widżetów zwróconych przez instalację: ogrzewania, temperatury
zewnętrznej, bufora, bojlerów i obiegów. Wykrywane są wszystkie numerowane
widżety `BOILER` i `HEATING_CIRCUIT_*` wraz z temperaturami, pompami,
wymuszonym ładowaniem i stanami pracy.

Obsługiwane są również temperatury bieżące/docelowe ogrzewania i bojlerów oraz,
jeśli są dostępne, temperatury źródła i zapotrzebowania regulatora Neo-HV.
Opcjonalne kanały historii (tlen, powrót, ciśnienie, zapas pelletu i wilgotność)
nie są jeszcze tworzone jako encje.
Wyświetlane są także stan bojlera, stan i tryb obiegu oraz pojemność bufora
(jednostka nie jest jeszcze znana).

Wiele buforów nie jest jeszcze tworzonych, ponieważ nie znamy ich schematu
numerowania w API.

## Instalacja

### HACS

1. Otwórz **HACS → Integracje**.
1. W menu z trzema kropkami wybierz **Niestandardowe repozytoria**.
1. Dodaj `https://github.com/m4c3/hass-hargassner-cloud` jako **Integrację**.
1. Zainstaluj **Hargassner Cloud** i uruchom ponownie Home Assistant.
1. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację**.

### Instalacja ręczna

Skopiuj `custom_components/hargassner_cloud` do katalogu `custom_components`,
uruchom ponownie Home Assistant i dodaj integrację z interfejsu.

## Konfiguracja i opcje

Konfiguracja wymaga adresu e-mail i hasła konta Hargassner. Domyślny adres to
`https://web.hargassner.at`. Jeśli konto ma kilka instalacji, pojawi się wybór.

Opcje pozwalają zmienić interwał aktualizacji (domyślnie 300 sekund, minimum
30), sugerowany obszar i mapowania JSON. Zapisanie automatycznie przeładowuje
integrację.

## Uwierzytelnianie

Integracja pobiera publiczne dane klienta webowego z aktualnej strony logowania
Hargassner. Repozytorium nie zawiera publicznego sekretu klienta. Hasło jest
wysyłane wyłącznie do skonfigurowanego adresu Hargassner.

Odrzucone hasło uruchamia standardowe ponowne uwierzytelnienie. Niezgodna zmiana
portalu tworzy zamiast tego zgłoszenie w panelu Naprawy.

## Diagnostyka i prywatność

Diagnostyka zawiera tylko nazwy widżetów i pól, typy danych oraz oczyszczony stan
API. Hasła, tokeny, identyfikatory instalacji, wartości robocze i adresy zasobów
są usuwane. Mimo to sprawdź plik przed publikacją.

## Rozwiązywanie problemów

- **Błąd logowania:** sprawdź konto na
  [`web.hargassner.at`](https://web.hargassner.at).
- **Brak połączenia:** sprawdź HTTPS i ewentualną konserwację portalu.
- **Brakujące encje:** pobierz diagnostykę i sprawdź nazwy widżetów oraz pól;
  mapowanie JSON może je dostosować.

## Licencja

Kod źródłowy i oryginalne grafiki projektu są objęte licencją MIT. Zobacz
[LICENSE](LICENSE). Hargassner jest znakiem towarowym odpowiedniego właściciela.
