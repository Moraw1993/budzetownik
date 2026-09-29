---
unit: 002-foundation-api
bolt: 004-foundation-api
stage: test
status: complete
updated: 2026-09-11T19:37:09+02:00
---

# Raport testów — zaproszenia

## Podsumowanie

| Zakres | Wynik | Uwagi |
| --- | --- | --- |
| Testy zaproszeń API | 5/5 | Wystawienie, uprawnienia, utworzenie konta, istniejące członkostwo, token odwołany/wygasły/zużyty. |
| Test współbieżności | 1/1 | Dwa równoległe przyjęcia tworzą najwyżej jedno nowe członkostwo. |
| Testy `households` | 31/31 | W tym istniejące testy ról, izolacji i blokad. |
| Pełny backend | 51/51 | Uruchomione w kontenerze PostgreSQL. |
| Kontrola jakości | poprawna | Ruff, Prettier, ESLint, Stylelint i TypeScript. |

Pokrycie kodu nie zostało zmierzone, ponieważ projekt nie ma skonfigurowanego narzędzia coverage. Cel P95 pozostaje zakresem bolta 008 i nie był mierzony w tym bolcie.

## Walidacja kryteriów akceptacji

| Story | Kryterium | Wynik |
| --- | --- | --- |
| 007-issue-invitation | Owner wystawia link z rolą i ważnością siedmiu dni. | ✅ |
| 007-issue-invitation | Tylko Owner listuje i odwołuje własne zaproszenia; obce gospodarstwo pozostaje ukryte. | ✅ |
| 007-issue-invitation | Token nie pojawia się w modelu, odpowiedzi listy ani zdarzeniach bezpieczeństwa. | ✅ |
| 008-accept-invitation | Ważny link tworzy konto i członkostwo albo dołącza zalogowane konto. | ✅ |
| 008-accept-invitation | Link odwołany, wygasły albo zużyty nie tworzy konta ani członkostwa. | ✅ |
| 008-accept-invitation | Równoległe przyjęcia nie zużywają zaproszenia dwukrotnie, a istniejące członkostwo nie jest duplikowane ani zmieniane. | ✅ |

## Testy bezpieczeństwa

- Endpointy zarządzania zaproszeniami wymagają aktualnej roli Owner i CSRF.
- Odczyt obcego gospodarstwa zwraca `404` bez ujawnienia jego danych.
- Token jest przekazywany przez fragment URL i treść POST; baza przechowuje wyłącznie HMAC-SHA-256.
- Zdarzenia bezpieczeństwa nie zawierają tokenu ani nazwy gospodarstwa.

## Wykonane polecenia

- `docker compose exec -T backend python manage.py makemigrations --check --dry-run` — brak oczekujących migracji.
- `docker compose exec -T backend python manage.py test households` — 31 testów poprawnych.
- `docker compose exec -T backend python manage.py test` — 51 testów poprawnych.
- `scripts/quality.ps1` — kontrola jakości poprawna.

## Otwarte elementy

- Brak otwartych błędów krytycznych lub wysokiego priorytetu.
- Konfigurację coverage i pomiar P95 należy rozstrzygnąć w odpowiednich późniejszych boltach; nie blokują one kryteriów stories 007–008.
