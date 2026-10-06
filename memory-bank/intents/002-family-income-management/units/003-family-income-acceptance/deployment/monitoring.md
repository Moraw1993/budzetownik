# Monitoring projektu lokalnego — do akceptacji

Status: lokalny monitoring MVP skonfigurowany i zweryfikowany 2026-10-06. Raporty: [staging](verification-monitoring-staging.md), [prywatna instalacja](verification-monitoring-prod.md).

## Zakres proponowanej konfiguracji

- Pozostawić istniejące healthchecki PostgreSQL, backendu i frontendu oraz politykę `restart: unless-stopped` usług długowiecznych.
- Ustawić rotację `json-file` dla usług `db`, `migrate`, `backend`, `frontend` i `proxy`: `max-size: 10m`, `max-file: "3"`.
- Przygotować [runbook niedostępności](runbooks/service-unavailable.md) i [runbook restartów oraz migracji](runbooks/restarts-and-migrations.md).
- Podczas odbioru sprawdzić konfigurację Compose, status health, liczbę restartów, dostępność HTTPS oraz krótką próbkę zużycia CPU i pamięci.

## Wdrożenie po akceptacji

1. ✅ Zastosowano zmianę na stagingu d670985 i potwierdzono healthchecki oraz zachowanie danych syntetycznych.
2. ✅ Przed zmianą prywatnej instalacji wykonano i zweryfikowano kopię. Zachowano aktualne obrazy kontenerów jako rollback.
3. ✅ Zastosowano tę samą konfigurację do prywatnej instalacji `myhomebudget` bez przebudowy i pobierania obrazów. Wolumeny, obrazy aplikacji, baza, sekrety, porty i certyfikaty pozostały bez zmian.
4. ✅ Zweryfikowano HTTPS, obrazy, healthchecki, restarty i liczebność danych; wyniki zapisano w historii wdrożeń.

Odtworzenie kontenerów może spowodować krótką przerwę w lokalnym dostępie. Jeśli staging, kopia lub dowolna weryfikacja zawiedzie, nie kontynuować na prywatnej instalacji. W razie problemu po zastosowaniu konfiguracji przywrócić poprzednie obrazy i konfigurację Compose, nie odtwarzając automatycznie bazy.

## Ograniczenia

Ta konfiguracja ogranicza rozmiar lokalnych plików logów i ułatwia ręczną diagnostykę. Nie zapewnia ciągłego monitoringu, zbierania metryk RED, dashboardów, automatycznych alertów, dyżurów ani SLO dostępności. Nie wysyła logów poza komputer. Cele 99,9% dostępności i P95 poniżej 200 ms z ogólnego szablonu Operations nie są potwierdzone dla tej instalacji.

## Checkpoint 4

Checkpoint 4 został zatwierdzony i wykonany. Jednostka przeszła monitorowanie MVP w zakresie opisanym powyżej.
