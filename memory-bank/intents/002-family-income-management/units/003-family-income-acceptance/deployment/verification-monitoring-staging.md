---
environment: staging
verified: '2026-10-06T19:28:40Z'
status: passed
scope: logging-rotation
---

# Weryfikacja rotacji logów na stagingu

## Wynik

- Wszystkie pięć usług używa `json-file` z `max-size=10m` i `max-file=3`: `db`, `migrate`, `backend`, `frontend`, `proxy`.
- Backend i frontend pozostały na przypiętych obrazach d670985: `a6d056105804` i `706851a34cdc`. PostgreSQL i Caddy nie uległy zmianie.
- Migracja zakończyła się kodem 0. Baza, backend i frontend były healthy; proxy działał. Liczniki restartów wszystkich kontenerów wynosiły 0.
- `GET https://localhost:58610/api/health/` zwrócił HTTP 200.
- Liczby rekordów we wszystkich 19 tabelach publicznych zgadzały się z odczytem sprzed zmiany:

| Tabela | Rekordy |
| --- | ---: |
| accounts_loginthrottle | 8 |
| accounts_user | 4 |
| accounts_user_groups | 0 |
| accounts_user_user_permissions | 0 |
| auth_group | 0 |
| auth_group_permissions | 0 |
| auth_permission | 60 |
| django_content_type | 15 |
| django_migrations | 20 |
| django_session | 22 |
| households_auditlog | 22 |
| households_company | 5 |
| households_contract | 7 |
| households_household | 2 |
| households_householdmember | 4 |
| households_incomesource | 12 |
| households_invitation | 0 |
| households_membership | 5 |
| households_relationtype | 0 |

## Próbka zasobów

Jedna próbka `docker stats` krótko po uruchomieniu: baza 0.00% CPU / 25.44 MiB, backend 27.15% / 105.4 MiB, frontend 0.00% / 38.7 MiB, proxy 0.01% / 14.45 MiB. To chwilowy odczyt po starcie, nie pomiar trendu, obciążenia ani SLO.

Nie skonfigurowano dashboardów, alertów ani ciągłych metryk. Staging został odtworzony z istniejącymi wolumenami, bez build i pull. Przed zmianą prywatnej instalacji wymagana jest aktualna kopia oraz zapis obrazu i wolumenów do procedury rollbacku.
