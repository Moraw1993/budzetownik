---
stage: plan
bolt: 012-family-income-acceptance
created: 2026-09-29T21:07:18Z
---

# Implementation Plan: 003-family-income-acceptance

## Objective

Potwierdzić kryteria obu stories na odrębnej lokalnej instalacji z PostgreSQL i rzeczywistym API. Odbiór obejmuje aktualny jasny design v3. Wyniki testów z mockami z bolta 011 są regresją, nie dowodem odbioru rzeczywistego stosu.

## Deliverables

- Powtarzalny scenariusz tworzący syntetyczne dane na schemacie households 0003 i migracji do aktualnego schematu.
- Testy HTTP uwierzytelnionych użytkowników Owner, Administrator, Member i Viewer oraz dwóch gospodarstw.
- Scenariusz E2E konfiguracji rodziny, firmy, dwóch umów i innego źródła gospodarstwa, z edycją, archiwizacją i jawną konwersją starego źródła.
- Porównanie trwałych danych przed restartem i po restarcie usług z zachowaniem wolumenów.
- Dowody dla szerokiego i mobilnego ekranu oraz obsługi klawiaturą, raport implementacji i raport testów z przypisaniem wyników do kryteriów stories.

## Dependencies

- Ukończone bolty 010 i 011: API, migracja 0004, aktualny UI i testy regresji.
- Bolt 008: istniejące narzędzia izolowanego odbioru i konfiguracja Compose.
- Docker Compose, PostgreSQL, lokalna przeglądarka Edge oraz zależności Playwright.
- Branch `feat/bolt-012-family-income-acceptance` wyprowadzony z `d9ff45d` bolta 011 po pobraniu referencji. Wynik zależności 011 nie znajduje się jeszcze w `origin/develop`; nie wykonujemy integracji ani publikacji w tym etapie.

## Technical Approach

### Instalacja i dane

Wykorzystać `scripts/acceptance_common.py`, `scripts/acceptance_stack.py` i `compose.acceptance.yaml`. Każdy run ma własną nazwę projektu, port localhost, konfigurację w ignorowanym `.runtime/acceptance` i trwałe wolumeny testowe. Wszystkie operacje Docker muszą wskazywać jawnie ten projekt. Dane ani konfiguracja prywatnej instalacji nie są źródłem scenariusza.

Przed migracją uruchomić tylko testową bazę i jednorazowy proces przygotowania danych na starym schemacie. Użyć historycznych modeli Django, zgodnie z istniejącym `test_family_income_migration.py`. Dopiero po zapisaniu punktu odniesienia uruchomić migrację i usługi aktualnej aplikacji. Nie cofać schematu bazy użytkownika.

Dane obejmują aktywne stare „Wynagrodzenie” przypisane do członka, archiwalne źródło, wartości dziesiętne, waluty, daty, statusy i audyt. Dwa gospodarstwa mają różne firmy, członków i źródła. Po migracji źródła zachowują UUID i wszystkie wcześniejsze wartości; pozostają `other` bez automatycznie utworzonych umów. Jawna konwersja jest osobnym późniejszym krokiem.

### Ponowne użycie testów

Rozszerzyć istniejące narzędzia HTTP i wspólne mechanizmy odbioru zamiast powielać obsługę konfiguracji, sesji i CSRF. Dodać testy rzeczywistego przepływu rodziny z jawnym identyfikatorem izolowanego runu. `live-records.spec.ts` ma stare selektory i domyślne polecenia Compose, dlatego nie będzie uruchamiany w obecnej postaci na instalacji użytkownika. Nowy lub dostosowany scenariusz musi kierować przygotowanie danych i przeglądarkę do tego samego izolowanego projektu.

W scenariuszu UI Owner i Administrator konfigurują członka, firmę i dwie umowy z różnymi podstawami kwoty, a następnie inne źródło gospodarstwa bez kwoty domyślnej. Sprawdzić właścicieli na listach, dokładne wartości brutto, zachowanie formularza po dodaniu firmy, edycję i archiwizację. Member i Viewer odczytują dane bez akcji zapisu.

Bezpośrednie żądania API mają potwierdzić odrzucenie odczytu obcych obiektów, powiązań z obcą firmą/członkiem/źródłem oraz zapisów Member i Viewer. Stan danych i audytu porównać przed odrzuconymi operacjami i po nich.

### Restart, regresja i dowody

Zapisać stan firm, umów, źródeł i audytu, zrestartować wyłącznie izolowane usługi bez usuwania wolumenów i odczytać ten sam stan przez API oraz bazę. Testową instalację zatrzymać po odbiorze; zachować dowody w ignorowanym katalogu lokalnym.

Uruchomić odpowiednie testy Django, pełną regresję UI z bolta 011, build i `scripts/quality.ps1`. E2E odbiorowe wykonać na szerokim ekranie 1440 px i mobilnym 390 px, z klawiaturą: przejścia po zakładkach, formularze, modal firmy i powrót fokusu. Zrzuty i wyniki opisać bez deklarowania pełnego audytu WCAG.

Model miesięcznych przychodów nie jest jeszcze zaimplementowany. Dowód braku ich tworzenia ma wskazać istniejące modele/tabele oraz zakres zapisów operacji; brak tabeli opisać jawnie, bez przedstawiania go jako testu przyszłego modułu.

## Acceptance Criteria

- [x] Migracja danych faktycznie utworzonych na schemacie 0003 zachowuje UUID, kwoty, powiązania, status i audyt aktywnego oraz archiwalnego źródła.
- [x] Stare „Wynagrodzenie” pozostaje innym źródłem do jawnej konwersji; migracja nie tworzy umów ani zdarzeń miesięcznych przychodów.
- [x] API odrzuca obce odczyty i powiązania oraz zapisy Member/Viewer bez zmian danych i audytu.
- [x] Restart usług z zachowaniem wolumenów zachowuje firmy, umowy i źródła.
- [x] Rzeczywisty UI pozwala dodać członka, firmę, dwie umowy członka i źródło gospodarstwa oraz pokazuje właściwych właścicieli.
- [x] Umowy pokazują brutto i różne podstawy kwoty; inne źródło może nie mieć kwoty domyślnej.
- [x] Edycja i archiwizacja nie zmieniają obcego gospodarstwa ani nie tworzą miesięcznych przychodów.
- [x] Scenariusz działa klawiaturą i na szerokim oraz mobilnym ekranie w jasnym designie; jakość, build i właściwe testy przechodzą.

## Stage Checkpoints

Plan zatwierdzony przez użytkownika: 2026-09-30T06:10:26Z. Implementacja narzędzi i scenariuszy rozpoczyna się po zatwierdzeniu planu; wykonanie pełnego odbioru następuje po osobnym zatwierdzeniu implementacji. Zamknięcie bolta wymaga zatwierdzonego raportu i obowiązkowego skryptu `bolt-complete.cjs`.
