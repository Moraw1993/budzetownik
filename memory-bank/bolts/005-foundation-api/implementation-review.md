---
bolt: 005-foundation-api
stage: implement
created: 2026-09-18T08:07:00+02:00
status: ready-for-review
---

# Implementacja członków, źródeł dochodu i audytu

Zrealizowano modele, migrację 0003, serializatory, transakcyjne usługi i API
dla stories 009–013. Wspólna polityka `locked_access` sprawdza aktualną rolę
po uzyskaniu blokady gospodarstwa. Zapis źródła i audytu jest atomowy.
Istniejące logowanie zdarzeń kont pozostaje niezależne od wyboru gospodarstwa.

## Wykonana weryfikacja

- Pełna regresja Django na PostgreSQL: **64/64**, 4,497 s.
- 13 nowych testów: 11 testów API/integralności i 2 współbieżności.
- Sprawdzono role, anonimowy dostęp, CSRF, obce identyfikatory, unikalność
  powiązania konta, kwoty dziesiętne, błędne dane, trwałość historii, paginację,
  odczyt audytu oraz rollback przy awarii tworzenia wpisu audytowego.
- Równoległe przypisanie konta tworzy jednego członka; równoległe zmiany
  źródła pozostawiają ciągły łańcuch stanów przed/po.
- `scripts/quality.ps1`: Ruff, Prettier, ESLint, Stylelint, TypeScript — OK.
  Po dopisaniu dwóch testów współbieżności wykonano ponownie Ruff dla tego pliku.
- `makemigrations --check --dry-run`: brak zmian.
- Lokalny backend zbudowany i uruchomiony; migracja 0003 zastosowana.
- Backend, frontend i PostgreSQL: healthy; `/api/health/`: `{"status":"ok"}`.

## Zakres dalszego odbioru

Nie wykonano pomiaru coverage ani P95. Formalny raport etapu testów i jego
odbiór pozostają do wykonania. Pomiar P95 całego MVP jest zaplanowany w bolcie 008.
Frontend tego bolta nie obejmuje formularzy — powstaną w boltach 006–007.
Bolt 005 pozostaje w toku; stories nie zostały oznaczone jako ukończone.
