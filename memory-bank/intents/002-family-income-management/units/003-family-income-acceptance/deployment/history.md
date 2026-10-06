---
environment: staging
deployed: 2026-09-30T08:10:34Z
status: success
---

# Historia wdrożeń

Dev zweryfikowano przed stagingiem w `myhomebudget-acceptance-17d4acaa-source`, HTTPS 58609; [raport](../../../../../operations/post-bolt-012.md).

Użytkownik zatwierdził staging słowami „tak zatwierdzam”. Pierwsze wdrożenie kandydata d670985 do `myhomebudget-acceptance-17d4acaa-target`: osobne wolumeny, sieć i HTTPS 127.0.0.1:58610. Narzędzia acceptance_stack wykonały kopię syntetycznych danych, konfiguracji i media z dev, odtworzenie do target, migracje i start. Prywatnej instalacji i zaufania Windows nie zmieniono.

Kopia: ignorowane `.runtime/acceptance/17d4acaa/backup`, zawiera sekrety syntetycznej instalacji, pozostaje poza Git. Po odbiorze oba środowiska testowe zatrzymano z zachowaniem wolumenów i dowodów.

Rollback danych stagingu: `python scripts/acceptance_stack.py restore 17d4acaa`. Nadpisuje wyłącznie target zgodny ze strzeżonym manifestem kopią sprzed testów. Ponowne odtworzenie zostało wykonane i zweryfikowane. Stop: `python scripts/acceptance_stack.py stop 17d4acaa --role target`. Start: `python scripts/acceptance_stack.py up 17d4acaa --role target`.

Produkcję następnie zatwierdzono odpowiedzią „ok” i wdrożono po wykonaniu kopii prywatnych danych. [Raport produkcji](verification-d670985-prod.md) opisuje rzeczywiste wyniki i ograniczenia. Nie wykonano release; wymaga `$realease_app`. Monitoring pozostał osobnym checkpointem.

## Monitoring

2026-10-06: Zastosowano rotację logów na stagingu bez budowania lub pobierania obrazów. Backend i frontend pozostały na przypiętych obrazach d670985, migracje zakończyły się kodem 0, usługi healthy, HTTPS zwrócił 200, liczniki restartów wyniosły 0, a liczby rekordów tabel pozostały zgodne ze stanem sprzed zmiany. [Raport stagingu](verification-monitoring-staging.md).

2026-10-06: Po zweryfikowanej kopii i zachowaniu tagów rollback zastosowano tę samą konfigurację na prywatnej instalacji, bez zmiany obrazów aplikacji i wolumenów. Migracje zakończyły się kodem 0, backend/frontend były healthy, API i strona główna zwróciły 200, liczniki restartów wyniosły 0, liczebność wszystkich 19 tabel i zawartość pustego katalogu media pozostały bez zmian. [Raport produkcyjny](verification-monitoring-prod.md). Lokalny monitoring MVP zakończony; pełne metryki, dashboardy i alerty pozostają poza jego zakresem.
