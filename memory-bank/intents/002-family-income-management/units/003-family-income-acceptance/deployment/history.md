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

Produkcja wymaga osobnego planu, identyfikacji aktualnych obrazów, kopii prywatnych danych, konkretnego rollbacku i checkpointu 3. Nie wykonano produkcji ani release; release wymaga `$realease_app`.
