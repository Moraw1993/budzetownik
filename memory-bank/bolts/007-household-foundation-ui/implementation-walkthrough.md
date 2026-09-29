---
stage: implement
bolt: 007-household-foundation-ui
status: accepted
created: 2026-09-21T20:01:04Z
---

# Raport implementacji: członkowie, relacje i źródła dochodu

## Wynik

Zaimplementowano interfejs stories 004–005 bez zmian backendu i schematu bazy. Aktywne gospodarstwo ma trzy sekcje: Dostępy, Członkowie i Dochody. Owner oraz Administrator otrzymują formularze zapisu, a Member i Viewer widzą te same dane w trybie odczytu. Wszystkie operacje korzystają z istniejącej autoryzacji API.

Etap implementacji nie zamyka bolta. Nowe scenariusze funkcjonalne i pełny przepływ z rzeczywistą bazą należą do etapu testów po zatwierdzeniu tego raportu.

## Zmienione pliki

- [x] `frontend/app/lib/api.ts` — typy członków, relacji, dochodów i odpowiedzi stronicowanej; bezpieczne mapowanie błędów pól; pobieranie wszystkich stron danych referencyjnych.
- [x] `frontend/app/lib/money.ts` — normalizacja i prezentacja kwot dziesiętnych jako tekst, bez konwersji całej wartości do `number`.
- [x] `frontend/app/components/ui.tsx` — współdzielone pola select i textarea oraz dostępna paginacja.
- [x] `frontend/app/components/members-panel.tsx` — lista i formularze członków oraz relacji, powiązanie konta, archiwalne stany, paginacja i potwierdzona dezaktywacja.
- [x] `frontend/app/components/income-panel.tsx` — lista i pełny formularz FR-08, przypisanie do gospodarstwa lub członka, precyzyjna kwota, częstotliwość, daty, opis, edycja i dezaktywacja.
- [x] `frontend/app/components/household-shell.tsx` — nawigacja między sekcjami aktywnego gospodarstwa i reset sekcji przy zmianie kontekstu.
- [x] `frontend/app/globals.css` — responsywna nawigacja, formularze, tabele, statusy, listy rekordów i paginacja zgodne z istniejącym systemem projektowym.
- [x] `README.md` — aktualny zakres interfejsu oraz zasady endpointów członków, relacji i dochodów.

## Zachowanie interfejsu

- Osoba gospodarstwa pozostaje odrębna od konta aplikacji. Formularz pozwala wybrać „Bez konta”, aktywne konto z dostępem oraz opcjonalną relację.
- Relacje rodzinne mają własną listę i formularz. Archiwalne relacje pozostają widoczne, a formularz ostrzega, gdy edytowany członek wskazuje nieaktywną relację.
- Źródło dochodu może dotyczyć całego gospodarstwa albo aktywnej osoby. Formularz zawiera wszystkie pola API, w tym płatnika, zakres dat, kwotę, walutę, częstotliwość, regularność i opis.
- Kwota domyślna jest opisana jako wartość planistyczna, a nie rzeczywista transakcja. Formatowanie grupuje cyfry i dodaje walutę bez obliczeń zmiennoprzecinkowych.
- Dane referencyjne są pobierane ze wszystkich stron API. Główne listy zachowują paginację po 50 rekordów z przyciskami Poprzednia/Następna.
- Zmiana sekcji odmontowuje poprzedni panel, a zmiana gospodarstwa resetuje sekcję do Dostępów. Trwające odczyty są anulowane przez `AbortController`, więc nie zapisują danych starego kontekstu.
- Rekordy nieaktywne są oznaczone jako archiwalne i nie mają aktywnych kontrolek edycji. Dezaktywacja wymaga jawnego potwierdzenia i wyjaśnia zachowanie historii.
- Odpowiedź 401/403 uruchamia odświeżenie sesji i roli. Sukces pojawia się dopiero po odpowiedzi API oraz ponownym pobraniu danych.

## Weryfikacja etapu implementacji

- [x] Prettier uruchomiony bezpośrednio po każdej zmianie TS/TSX/CSS.
- [x] ESLint uruchomiony dla każdego zmienionego pliku TypeScript/TSX.
- [x] Stylelint uruchomiony dla zmienionego CSS; wykryta kolejność selektora została poprawiona bez wyłączania reguły.
- [x] `scripts/quality.ps1` zakończony powodzeniem: Ruff format/check, Prettier, ESLint, Stylelint i TypeScript.
- [x] Produkcyjny build Next.js zakończony powodzeniem.
- [x] Dotychczasowe izolowane testy UI: 17/17 przeszło; test live pozostał świadomie pominięty bez flagi `LIVE_E2E=1`.
- [x] Frontend przebudowany w Compose; db, backend i frontend są healthy, migracje zakończyły się kodem 0, proxy działa.
- [x] Sprawdzono nowe selektory i odpowiedzialności komponentów; nie znaleziono niezamierzonego powielenia nazw ani logiki domenowej backendu.

Pierwsze uruchomienie testów UI w ogólnym obrazie Node nie miało binariów Chromium. Testy powtórzono w oficjalnym obrazie Playwright zgodnym z wersją 1.63.0 i uzyskano wynik 17/17. Nie jest to błąd aplikacji.

## Pozostały etap

Po zatwierdzeniu raportu etap testów doda scenariusze dla członków, relacji i dochodów, sprawdzi role Owner/Administrator/Member/Viewer, paginację, błędy i wyścigi kontekstu oraz wykona pełny przepływ przez rzeczywiste HTTPS, API i PostgreSQL z posprzątaniem danych testowych.

Raport zatwierdzony przez użytkownika. Etap testów rozpoczęto 2026-09-21T20:01:04Z.
