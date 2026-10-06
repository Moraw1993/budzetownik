# Monitoring projektu lokalnego — do akceptacji

Status: propozycja. Konfiguracja nie została zastosowana; trwa oczekiwanie na checkpoint 4 Operations.

## Zakres proponowanej konfiguracji

- Pozostawić istniejące healthchecki PostgreSQL, backendu i frontendu oraz politykę `restart: unless-stopped` usług długowiecznych.
- Ustawić rotację `json-file` dla usług `db`, `migrate`, `backend`, `frontend` i `proxy`: `max-size: 10m`, `max-file: "3"`.
- Przygotować [runbook niedostępności](runbooks/service-unavailable.md) i [runbook restartów oraz migracji](runbooks/restarts-and-migrations.md).
- Podczas odbioru sprawdzić konfigurację Compose, status health, liczbę restartów, dostępność HTTPS oraz krótką próbkę zużycia CPU i pamięci.

## Wdrożenie po akceptacji

1. Najpierw zastosować zmianę na stagingu i potwierdzić healthchecki oraz zachowanie danych syntetycznych.
2. Po pozytywnym stagingu zastosować tę samą konfigurację do prywatnej instalacji `myhomebudget` przez odtworzenie kontenerów bez przebudowy i pobierania obrazów. Wolumeny, obrazy aplikacji, baza, sekrety, porty i certyfikaty pozostają bez zmian.
3. Wykonać kopię zgodnie z procedurą [kopii i odtworzenia](../../../../../operations/backup-restore.md), zweryfikować HTTPS, obrazy, healthchecki, restarty i trwałość istniejących danych, a wynik zapisać w historii wdrożeń.

Odtworzenie kontenerów może spowodować krótką przerwę w lokalnym dostępie. Jeśli staging, kopia lub dowolna weryfikacja zawiedzie, nie kontynuować na prywatnej instalacji. W razie problemu po zastosowaniu konfiguracji przywrócić poprzednie obrazy i konfigurację Compose, nie odtwarzając automatycznie bazy.

## Ograniczenia

Ta konfiguracja ogranicza rozmiar lokalnych plików logów i ułatwia ręczną diagnostykę. Nie zapewnia ciągłego monitoringu, zbierania metryk RED, dashboardów, automatycznych alertów, dyżurów ani SLO dostępności. Nie wysyła logów poza komputer. Cele 99,9% dostępności i P95 poniżej 200 ms z ogólnego szablonu Operations nie są potwierdzone dla tej instalacji.

## Checkpoint 4

Przed zmianą konfiguracji Compose i odtworzeniem kontenerów wymagane jest jawne zatwierdzenie użytkownika dla powyższego zakresu: rotacja logów na stagingu, następnie — po pozytywnej weryfikacji stagingu — na prywatnej instalacji, wraz z runbookami i kontrolą po wdrożeniu.
