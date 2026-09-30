---
stage: implement
bolt: 012-family-income-acceptance
created: 2026-09-30T06:29:08Z
---

# Implementation Walkthrough: 003-family-income-acceptance

## Summary

Przygotowano odbiór rzeczywistej lokalnej instalacji rodziny i źródeł na syntetycznych danych. Narzędzia tworzą dane na historycznym schemacie, weryfikują migrację, sprawdzają role i izolację oraz porównują stan API i bazy po restarcie. Scenariusze przeglądarkowe korzystają z istniejącego jasnego UI; nie dodano nowych ekranów ani zmian do kodu aplikacji.

## Structure Overview

Runner na komputerze korzysta ze wspólnej konfiguracji izolowanych runów, sesji HTTPS i Compose z bolta 008. Osobny moduł uruchamiany w kontenerze Django przygotowuje historyczne dane i porównuje pełne rekordy bazy. Playwright odczytuje manifest tego samego runu i kieruje przeglądarkę do jego portu.

## Completed Work

- [x] `scripts/family_acceptance.py` — przygotowanie instalacji, kontrola ról i powiązań między gospodarstwami, checkpoint i restart.
- [x] `scripts/family_acceptance_data.py` — syntetyczne dane na schemacie 0003, porównanie wszystkich wcześniejszych pól źródeł i audytu po migracji oraz snapshot wszystkich tabel domeny households.
- [x] `frontend/tests/family-acceptance.spec.ts` — pięć scenariuszy rzeczywistego UI: Owner na 1440 px, Administrator na 390 px, Member, Viewer i jawna konwersja historycznego wynagrodzenia.

## Key Decisions

- **Wyłącznie izolowany run**: wszystkie operacje Compose używają zweryfikowanego manifestu z własnym projektem i konfiguracją. Seed wymaga bazy bez jakichkolwiek migracji; ponowne przygotowanie istniejącej fixture jest odrzucane.
- **Porównanie pełnej historii**: wynik migracji porównuje wszystkie stare pola rekordów, również wartości i daty niewystępujące na listach UI.
- **Osobne dane kontroli HTTP**: odrzucane próby zapisu i konwersji korzystają ze źródła niezależnego od wynagrodzenia przekształcanego później w UI.
- **Stan obcego gospodarstwa**: checkpoint porównuje gospodarstwo B ze stanem po kontroli dostępu, a restart porównuje oba gospodarstwa przez API i wszystkie tabele households w bazie.
- **Jawne opt-in E2E**: nowe testy są pomijane bez identyfikatora runu; nigdy nie kierują się domyślnie do prywatnej instalacji localhost:8443.
- **Bez nowego UI**: bramka ui-design-review nie wymaga ponownej akceptacji historycznych ekranów. Testy używają wersji jasnego designu zaakceptowanej w bolcie 011.

## Deviations from Plan

Dodano osobny plik testów rodziny zamiast zmieniać stare live-records.spec.ts. Stary plik nadal wymaga osobnego LIVE_E2E i nie jest częścią nowego odbioru.

W kontrolnej próbie seed użył pustej kwoty obcego źródła, której schemat 0003 nie dopuszcza. Fixture poprawiono, nieudany run 1618c3fd zatrzymano, a poprawny seed i migrację sprawdzono na świeżym runie 1e365076.

Pierwsza kontrola HTTP i próba E2E zostały uruchomione równolegle, co naruszyło punkt odniesienia porównania stanu. Nie stanowi to dowodu naruszenia uprawnień API. W odbiorze wymagane jest sekwencyjne wykonanie kontroli HTTP, E2E, checkpointu i restartu.

## Dependencies Added

Nie dodano zależności. Użyto istniejących narzędzi Django, PostgreSQL, Docker Compose, HTTPS/CSRF oraz Playwright z Microsoft Edge.

## Developer Notes

Kolejność odbioru: utworzenie świeżego runu przez acceptance_stack, przygotowanie przez family_acceptance, kontrola access, testy family-acceptance z FAMILY_ACCEPTANCE_RUN_ID, checkpoint, restart, zatrzymanie izolowanej instalacji. Kontrola access i E2E nie mogą wykonywać się równolegle. Kolejny pełny odbiór należy wykonać na świeżym runie, ponieważ scenariusze zapisują dane, a konwersja jest jednokrotna.

Hasła syntetyczne pozostają w ignorowanej konfiguracji runu i są przekazywane do procesu danych przez zmienną środowiskową. Nie zapisuje się ich w dokumentacji ani komunikatach błędów poleceń.

W bieżącym modelu nie istnieje tabela miesięcznych przychodów. Snapshot dokumentuje faktyczny zakres tabel domeny; raport nie może deklarować przetestowania nieistniejącego przyszłego modułu.

## Implementation Validation

- Kontrola jakości projektu: Ruff 0.16.6, Prettier, ESLint, Stylelint i TypeScript — przeszła.
- Build produkcyjnego frontendu w izolowanym Compose — przeszedł.
- Seed starego schematu i migracja: 3 źródła oraz 1 wpis audytu zachowane, 0 domyślnie utworzonych umów.
- Próba E2E: 5/5 przeszło w 8,9 s; bez identyfikatora runu wszystkie 5 zostało prawidłowo pominięte.
- Sekwencyjna kontrola HTTP po rozdzieleniu danych — przeszła; odrzucone zapisy i obce powiązania nie zmieniły danych ani audytu obu gospodarstw.
- Checkpoint i restart — przeszły; stan API i wszystkie 9 tabel domeny households pozostały identyczne po restarcie usług bez usuwania wolumenów. Kontrolny checkpoint wykonano po próbie E2E i powtórzonej kontroli HTTP; dowód izolacji całego przepływu UI przed/po musi zostać powtórzony we właściwej kolejności na świeżym runie w etapie Test.
- Zrzuty kontrolne są w ignorowanym katalogu `.runtime/acceptance/1e365076/ui/`. Sprawdzono desktopową i mobilną listę umów: jasne tło, dopasowany układ, tabela przewijana lokalnie.

Implementacja została zatwierdzona przez użytkownika. Pełną regresję i odbiór na świeżym runie opisuje [raport testów](test-walkthrough.md).
