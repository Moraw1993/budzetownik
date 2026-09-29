---
stage: implement
bolt: 008-local-acceptance
status: approved
validated: 2026-09-23T20:52:30Z
created: 2026-09-23T20:48:13Z
---

# Implementacja odbioru lokalnego

## Podsumowanie

Przygotowano powtarzalny odbiór na dwóch odizolowanych instalacjach Docker Compose. Narzędzia tworzą syntetyczne konta i dane, sprawdzają role oraz izolację API, zapisują kopię bazy i załączników, odtwarzają ją w drugim projekcie i mierzą P95 podstawowych operacji. Instrukcja operatora opisuje kopię rzeczywistej instalacji bez ujawniania sekretów w repozytorium.

## Struktura

Wspólna obsługa izolowanego projektu Compose i sesji HTTPS jest oddzielona od scenariusza funkcjonalnego, cyklu kopii oraz pomiaru wydajności. Dane wygenerowane przez testy pozostają w ignorowanym folderze `.runtime/acceptance/` i mają osobne projekty, porty oraz wolumeny.

## Ukończone prace

- [x] `compose.acceptance.yaml` — osobny port HTTPS i adres CSRF dla instalacji odbiorowej.
- [x] `backend/config/settings.py` — możliwość dodania zaufanego adresu CSRF przez zmienną środowiskową przy zachowaniu obecnego adresu lokalnego.
- [x] `scripts/acceptance_common.py` — weryfikacja identyfikatorów testu i kierowanie poleceń wyłącznie do jego projektów Compose.
- [x] `scripts/acceptance_stack.py` — tworzenie dwóch instalacji, kopia bazy, załączników i konfiguracji, odtworzenie oraz odtworzenie kontenerów.
- [x] `scripts/acceptance_http.py` — sesja HTTPS z lokalnym certyfikatem, ciasteczkami i ochroną CSRF.
- [x] `scripts/acceptance_flow.py` — sześć kroków na danych syntetycznych, role, odmowy, izolacja, audyt i porównanie danych po odtworzeniu.
- [x] `scripts/acceptance_perf.py` — rozgrzewka, pomiary przy równoległości 1 i 5, P95 oraz zapis warunków pomiaru.
- [x] `frontend/tests/acceptance.spec.ts` — kontrola rozdzielenia członków i dochodów w przeglądarce.
- [x] `memory-bank/operations/backup-restore.md` i `README.md` — procedura kopii, odtworzenia, odzyskiwania konta i uruchomienia próby odbiorowej.

## Decyzje

- **Oddzielne projekty Compose:** źródło i cel mają własne wolumeny, porty i pliki środowiska. Przed każdym poleceniem skrypt sprawdza identyfikator projektu, aby nie skierować operacji odtworzenia do bieżącej instalacji użytkownika.
- **Spójna kopia:** aplikacja testowa jest zatrzymywana na czas dumpu bazy i archiwizacji załączników. Odtworzenie wykonuje się tylko w docelowym projekcie testowym.
- **Pomiar po odtworzeniu:** test wydajności dodaje dane, dlatego jest uruchamiany po porównaniu kopii z oryginałem.

## Odchylenia od planu

Nie dodano zewnętrznych zależności. Test przeglądarkowy wykorzystuje istniejący Playwright, a skrypty Python korzystają z biblioteki standardowej.

## Weryfikacja implementacji

- Produkcyjny build uruchomionej instalacji testowej przeszedł; baza, backend i frontend osiągnęły stan zdrowy. Odczyt konfiguracji pierwszego konta przez HTTPS z zaufanym lokalnym CA zwrócił oczekiwany stan pustej instalacji.
- 68 istniejących testów Django przeszło w izolowanym projekcie.
- `scripts/quality.ps1` przeszedł po zmianach: Ruff, Prettier, ESLint, Stylelint i TypeScript.
- Pełny scenariusz sześciu kroków, kopia i odtworzenie oraz pomiar P95 należą do następnego etapu testów; nie są jeszcze oznaczone jako wykonane.

## Uwagi dla etapu testów

Uruchomić kroki z instrukcji kopii i odtworzenia, zapisać rzeczywiste wyniki oraz sprawdzić kryteria trzech stories. Po testach zatrzymać oba projekty odbiorowe; wolumeny i dowody zachować do czasu przeglądu raportu.
