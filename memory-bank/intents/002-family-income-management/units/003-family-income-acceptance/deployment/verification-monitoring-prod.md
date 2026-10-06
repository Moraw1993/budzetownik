---
environment: prod
verified: '2026-10-06T19:35:44Z'
status: passed
scope: logging-rotation
---

# Weryfikacja rotacji logów w prywatnej instalacji

## Kopia i rollback

- Kopia znajduje się poza repozytorium: `C:/Users/Arek/MyHomeBudgetBackups/monitoring-20261006T193230Z`.
- Dump PostgreSQL przeszedł `pg_restore --list`; SHA256: `950E0DB7D8957E317A0E5811F96DE3793A312C1FBEDFFC89882367ABCE37C63F`.
- Skopiowano konfigurację `.env`, oba warianty Compose, Caddyfile i katalog media (0 plików). Prywatna kopia nie była odtwarzana testowo.
- Obecne obrazy backendu i frontendu zachowano jako `myhomebudget-backend:monitoring-rollback-20261006` i `myhomebudget-frontend:monitoring-rollback-20261006`. Identyfikatory obrazów przed i po zmianie są zgodne.
- Obrazy: backend `sha256:4c1d5994ac39cd55e715e63208abc12c02ce9db12acb062cd69473c27b4b2fd2`, frontend `sha256:7cd7996998587a76b6a2ab23c91800b3536f08a65ba68fcf745e849ebeecc35d`, PostgreSQL `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`, Caddy `sha256:5f5c8640aae01df9654968d946d8f1a56c497f1dd5c5cda4cf95ab7c14d58648`.
- Wdrożenie i konfiguracja rollbacku przeszły `docker compose config --quiet`.

## Wynik

- Wszystkie usługi `db`, `migrate`, `backend`, `frontend`, `proxy` używają `json-file`, `max-size=10m`, `max-file=3`.
- Migrator zakończył się kodem 0. Baza, backend i frontend były healthy, proxy działał. Liczniki restartów wyniosły 0.
- `GET https://localhost:8443/api/health/` i `GET https://localhost:8443/` zwróciły HTTP 200.
- Liczby rekordów we wszystkich 19 tabelach publicznych były zgodne z odczytem sprzed wdrożenia; wolumen bazy zachował tę samą nazwę. Katalog media pozostał pusty.
- Chwilowa próbka `docker stats` po wdrożeniu: baza 0.01% CPU / 24.02 MiB, backend 0.01% / 105.1 MiB, frontend 0.02% / 36.64 MiB, proxy 0.00% / 13.48 MiB.

Odtworzenie kontenerów spowodowało krótką przerwę w dostępie; ciągłej dostępności nie mierzono. Próbka zasobów nie jest pomiarem trendu ani SLO. Prywatną kopię pozostawiono poza repozytorium i nie ujawniono jej zawartości.

## Zakres monitoringu

Skonfigurowano ograniczoną rotację lokalnych logów i udokumentowano ręczne runbooki. Nie skonfigurowano ciągłych metryk RED, dashboardów, automatycznych alertów, zewnętrznej agregacji logów ani SLO.
