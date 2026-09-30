---
stage: test
bolt: 012-family-income-acceptance
created: 2026-09-30T06:45:15Z
status: approved
approved: 2026-09-30T07:30:17Z
---

# Test Report: 003-family-income-acceptance

## Summary

Końcowy odbiór na świeżym syntetycznym runie `17d4acaa` przeszedł. Sekwencja: dane na starym schemacie → migracja → kontrola HTTPS API → rzeczywiste E2E → porównanie obcego gospodarstwa i checkpoint → restart → porównanie API oraz bazy.

- **Django**: 83/83, 6,346 s; osobna baza testowa, następnie automatycznie usunięta.
- **Regresja UI**: 42/42 uruchomione, 25,2 s; 8 jawnych pominięć testów wymagających opt-in.
- **Rzeczywiste E2E rodziny**: 5/5, 7,4 s, bez retry; wykonane osobno po zakończeniu kontroli HTTP.
- **Migracja**: 3/3 źródła i 1/1 wpis audytu zachowane; brak automatycznie utworzonych firm i umów.
- **Role i izolacja API, checkpoint i restart**: przeszły.
- **Build i quality.ps1**: przeszły; Ruff 0.16.6, Prettier, ESLint, Stylelint, TypeScript.
- **Kryteria stories**: 8/8 sprawdzonych w zakresie obecnego modelu. Pokrycia linii kodu nie mierzono.

Raport zatwierdzony przez użytkownika poleceniem Continue. Formalne zakończenie zapisano obowiązkowym skryptem synchronizacji statusów.

## Installation and Method

Projekt Compose `myhomebudget-acceptance-17d4acaa-source`, HTTPS `https://localhost:58609`, własna baza PostgreSQL i trwałe wolumeny. Syntetyczne dane, konfiguracja i dowody znajdują się w ignorowanym `.runtime/acceptance/17d4acaa`. Nie użyto prywatnej instalacji ani danych użytkownika.

Seed historycznych modeli Django wykonano na nowej bazie bez migracji, do schematu households 0003. Dopiero potem uruchomiono aktualne migracje i produkcyjne kontenery aplikacji. Snapshot sprzed migracji porównano pole po polu z nowymi rekordami. Odbiór używa rzeczywistych sesji, CSRF, zaufanego certyfikatu lokalnego i API; scenariusze UI z mockami stanowią osobną regresję.

Pełna regresja UI i Django nie zapisują do danych odbiorowych. Testy Django korzystają z odrębnej bazy testowej. Zapisujące E2E rozpoczęto dopiero po zakończeniu kontroli HTTP. Checkpoint po E2E potwierdził identyczny stan gospodarstwa B względem punktu odniesienia sprzed zapisów UI.

## Test Files

- [x] `scripts/family_acceptance_data.py` — pełne porównanie historycznych źródeł i audytu, wszystkich tabel households po restarcie.
- [x] `scripts/family_acceptance.py` — sesje HTTPS, role, obce odczyty i powiązania, brak zmian po odrzuconych operacjach oraz trwałość.
- [x] `frontend/tests/family-acceptance.spec.ts` — rzeczywista konfiguracja rodziny przez Ownera i Administratora, odczyt Member/Viewer, jawna konwersja.
- [x] `frontend/tests/family.spec.ts`, `records.spec.ts`, `foundation.spec.ts` — pełna regresja zachowania UI z mockami.
- [x] Pełny zestaw Django, w tym `backend/households/tests/test_family_income_migration.py`, `test_family_income_api.py` i `test_family_income_concurrency.py` — migracja, reguły domenowe, autoryzacja i współbieżność.

## Acceptance Criteria Validation

| Story / kryterium | Wynik i dowód |
|---|---|
| 001 / migracja zachowuje dane | ✅ Trzy źródła, w tym aktywne „Wynagrodzenie” z kwotą 1234,56 PLN oraz archiwalny najem z kwotą 99,00 EUR. Wszystkie wcześniejsze pola, UUID, członkowie, gospodarstwa, statusy, daty i pełny audyt identyczne po migracji. |
| 001 / brak automatycznej konwersji i przychodów | ✅ Po migracji wszystkie źródła `other`, bez firm i umów. Dopiero jawna konwersja UI zachowała UUID `a5ebee87-af64-443c-b947-d3e1b08332df`, zwiększyła wersję do 2 i zapisała brutto 1234,56 PLN. Ograniczenie dotyczące nieistniejącego modelu miesięcznych przychodów opisano poniżej. |
| 001 / role i izolacja | ✅ Member/Viewer odczytują własne dane; tworzenie, edycja, archiwizacja i konwersja są odrzucane. Obce UUID w URL oraz obcy członek/firma w payloadzie nie przechodzą. Dane i audyt obu gospodarstw identyczne przed i po odrzuconych zapisach. |
| 001 / restart | ✅ Po restarcie db/backend/frontend/proxy bez usuwania wolumenów stan obu gospodarstw przez API i pełne rekordy wszystkich 9 tabel households identyczne. |
| 002 / konfiguracja rodziny | ✅ Owner na 1440 px i Administrator na 390 px dodali członka, firmę w modalu, dwie umowy tej osoby i źródło gospodarstwa. Listy pokazują właściwego członka i firmę; źródło trafia do sekcji całego gospodarstwa. |
| 002 / brutto, podstawa i opcjonalna kwota | ✅ Każda osoba ma 8500,25 PLN miesięcznie i 123,45 PLN za godzinę. Dodane źródła gospodarstwa mają pustą kwotę domyślną i komunikat „Brak podpowiedzi”. Weryfikacja w rzeczywistym UI i snapshotach. |
| 002 / edycja i archiwizacja | ✅ Oba źródła UI zmieniono i zarchiwizowano; w bazie `other`, `is_active=false`, wersja 3 i kwota domyślna null. Gospodarstwo B identyczne przed/po całym przepływie UI. Zakres modeli przychodów opisano poniżej. |
| 002 / klawiatura, ekrany i jakość | ✅ Aktywowanie akcji Enter, nawigacja zakładek End/ArrowLeft, fokus pól, Escape w modalu i powrót do wyboru firmy; desktop 1440 i mobile 390 bez poziomego przepełnienia dokumentu. Regresja dodatkowo sprawdza 1024 px i przewijanie lokalne tabel. Build, jakość i wszystkie uruchomione testy przeszły. |

## Persistence Evidence

Przed restartem: 2 gospodarstwa, 5 przypisań użytkowników, 4 członków, 4 firmy, 12 źródeł, 7 umów, 19 wpisów audytu; brak zaproszeń i relacji. Umowy: 5 z podstawą miesięczną i 2 godzinowe. Audyt: 14 utworzeń, 2 edycje, 2 dezaktywacje i 1 konwersja. Po restarcie porównanie obejmuje wszystkie wartości rekordów, a nie tylko liczebności.

## Evidence and Logs

- [Log przygotowania i buildu](../../../.runtime/acceptance/17d4acaa/prepare.log), [wynik migracji](../../../.runtime/acceptance/17d4acaa/family-migration-result.json), [historyczne rekordy](../../../.runtime/acceptance/17d4acaa/family-legacy.json).
- [Log kontroli HTTP](../../../.runtime/acceptance/17d4acaa/access.log), [wynik kontroli i punkt odniesienia obcego gospodarstwa](../../../.runtime/acceptance/17d4acaa/family-access-result.json).
- [Django](../../../.runtime/acceptance/17d4acaa/django-tests.log), [regresja UI](../../../.runtime/acceptance/17d4acaa/ui-regression.log), [rzeczywiste E2E](../../../.runtime/acceptance/17d4acaa/family-e2e.log).
- [Checkpoint](../../../.runtime/acceptance/17d4acaa/checkpoint.log), [snapshot API](../../../.runtime/acceptance/17d4acaa/family-api-snapshot.json), [snapshot bazy](../../../.runtime/acceptance/17d4acaa/family-db-snapshot.json), [restart i zgodność danych](../../../.runtime/acceptance/17d4acaa/restart.log).
- [Umowy desktop](../../../.runtime/acceptance/17d4acaa/ui/contracts-1440.png), [umowy mobile](../../../.runtime/acceptance/17d4acaa/ui/contracts-390.png), [źródła desktop](../../../.runtime/acceptance/17d4acaa/ui/sources-1440.png), [źródła mobile](../../../.runtime/acceptance/17d4acaa/ui/sources-390.png).

Obejrzano zrzuty rzeczywistego desktopu i mobile: zgodne jasne tło, białe panele, zielone akcje, czytelne przypisania. Szerokie tabele na mobile są przewijane lokalnie. Dodatkowe 12 zrzutów regresji zapisano w `.runtime/acceptance/17d4acaa/regression-ui`.

## Issues Found

Nie wykryto błędu aplikacji ani nie zmieniono kodu źródłowego w etapie Test. Poprzednie problemy przygotowania fixture i równoległego wykonania opisane w raporcie implementacji nie powtórzyły się w końcowym odbiorze. Wszystkie kroki końcowej sekwencji zakończyły się kodem 0.

## Notes and Limits

Osiem pominięć w domyślnym suite to pięć nowych E2E rodziny (później uruchomione osobno 5/5) oraz trzy starsze scenariusze acceptance/live-foundation/live-records wymagające własnych parametrów. Te starsze testy nie były uruchamiane na prywatnej instalacji. Ich zakres rodziny potwierdzono nowym odbiorem; nie deklarujemy ich indywidualnego przejścia.

W bieżącej aplikacji nie istnieje model ani tabela miesięcznych przychodów. Istnieją źródła, umowy i ich audyt; kwoty brutto i podpowiedzi nie zapisują odrębnego zdarzenia miesięcznego. Snapshot zawiera wszystkie istniejące tabele domeny. To potwierdza obecny zakres, lecz nie zastępuje testów przyszłego modułu miesięcznych przychodów.

Nie mierzono wydajności API ani pełnej zgodności WCAG. Zrzuty i testy klawiatury potwierdzają opisane przepływy, nie kompleksowy audyt dostępności. Dowody lokalne są ignorowane przez Git; repozytorium zawiera raport i powtarzalne scenariusze. Instalację testową zatrzymano z zachowaniem wolumenów i dowodów.

Po zatwierdzeniu raportu wykonano obowiązkowy `bolt-complete.cjs` i zweryfikowano kaskadę statusów.
