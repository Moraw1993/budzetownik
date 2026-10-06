# Runbook: prywatna instalacja jest niedostępna

Dotyczy lokalnego Compose projektu `myhomebudget` dostępnego pod `https://localhost:8443`.

## Diagnoza

1. W katalogu projektu uruchom `docker compose ps -a` i sprawdź `db`, `migrate`, `backend`, `frontend` oraz `proxy`.
2. Dla usługi, która nie działa poprawnie, odczytaj ostatnie logi: `docker compose logs --tail 100 <usługa>`. Nie kopiuj do zgłoszeń logów zawierających prywatne dane lub sekrety.
3. Sprawdź healthcheck bazy oraz endpoint `https://localhost:8443/api/health/`. Endpoint może zgłosić problem bazy lub migracji; brak oddzielnego `/ready` jest stanem obecnej aplikacji.
4. Sprawdź `docker inspect` dla kontenera usługi pod kątem liczby restartów i stanu health. Zapisz czas obserwacji oraz używane obrazy; nie uruchamiaj `docker compose up --build` jako działania naprawczego.

## Przywrócenie

1. Jeśli awaria nastąpiła po zmianie wersji aplikacji, skorzystaj z przypiętych obrazów i procedury z [planu produkcyjnego](../production-plan.md), wykonując rollback kodu bez przywracania bazy.
2. Jeśli to pojedyncza awaria kontenera bez błędów danych lub migracji, uruchom tylko usługi projektu: `docker compose up -d db migrate backend frontend proxy --no-build --pull never --wait`.
3. Potwierdź healthchecki, endpoint HTTPS i brak wzrostu liczby restartów. Wykonaj tylko odczytowe sprawdzenie aplikacji; nie twórz fikcyjnych rekordów na prywatnych danych.
4. Jeśli usługa nadal nie działa, zatrzymaj dalsze próby, zachowaj potrzebne logi w zabezpieczonym miejscu i ustal przyczynę przed kolejną zmianą.

## Bezpieczeństwo danych

Nie używaj `docker compose down -v`, `docker volume rm`, `docker system prune` ani `pg_restore --clean` w ramach rutynowej naprawy. Odtwarzanie prywatnej bazy wykonuj wyłącznie po potwierdzonej utracie danych, z właściwej kopii i po osobnej analizie.
