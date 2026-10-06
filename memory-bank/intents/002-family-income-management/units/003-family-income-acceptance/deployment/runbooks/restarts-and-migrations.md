# Runbook: powtarzające się restarty lub błąd migracji

Dotyczy lokalnych usług Compose `myhomebudget`.

## Powtarzające się restarty

1. Uruchom `docker compose ps -a` i zanotuj usługę, stan health oraz liczbę restartów.
2. Sprawdź `docker compose logs --tail 100 <usługa>` i czas ostatniego restartu. Nie publikuj logów z danymi użytkownika ani konfiguracją środowiska.
3. Zweryfikuj ID obrazów przez `docker inspect` i porównaj je z oczekiwaną wersją wdrożenia. Nie przebudowuj obrazu w celu „naprawy” prywatnej instalacji.
4. Jeśli problem zaczął się po aktualizacji kodu, zastosuj rollback przypiętych obrazów według [planu produkcyjnego](../production-plan.md). Zachowaj bieżącą bazę.
5. Jeśli restart nadal występuje na poprzednim obrazie, wstrzymaj kolejne restarty i zdiagnozuj zasoby, połączenie z bazą oraz logi.

## Błąd usługi `migrate`

1. Sprawdź `docker compose ps -a` oraz `docker compose logs --tail 150 migrate db`.
2. Nie uruchamiaj migracji ręcznie na prywatnej bazie i nie usuwaj wolumenów. Zachowaj komunikat błędu bez ujawniania zmiennych środowiskowych.
3. Jeśli nie rozpoczęto jeszcze wdrożenia nowej wersji, przywróć poprzednie obrazy. Jeżeli migracja zmieniła schemat lub nie wiadomo, czy zatwierdziła część zmian, zatrzymaj się i oceń stan bazy przed rollbackiem.
4. Po naprawie ponownie sprawdź stan migracji, health endpoint i podstawowe odczyty aplikacji. Zapisz wersje obrazów, czas i wynik w historii operacji.

Nie wykonuj `docker compose down -v`, ręcznego `DROP`, `flush` ani odtwarzania kopii z opcją `--clean` jako standardowej reakcji na błąd migracji.
