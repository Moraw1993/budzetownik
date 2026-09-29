---
stage: test
bolt: 003-foundation-api
created: 2026-09-10T06:09:56.761Z
---
# Raport testów gospodarstw i dostępu

## Wynik
45/45 testów Django przeszło na PostgreSQL w Dockerze: 25 nowych testów gospodarstw i 20 dotychczasowych testów kont/runtime.
Coverage 7.10.7: 98% łącznego pokrycia instrukcji i gałęzi dla households oraz common (197 instrukcji, 2 niepokryte, 20 gałęzi, 3 niepokryte). Testy i migracje wyłączone z tego pomiaru. Raport lokalny: .runtime/households-coverage.json.
Nie jest to pokrycie całego projektu ani dowód ukończenia MVP.

## Kryteria
- 004-create-household: atomowe utworzenie gospodarstwa i Owner, PLN domyślnie, walidacja, wiele gospodarstw, odczyt po ponownym zalogowaniu, wycofanie przy błędzie członkostwa.
- 005-household-roles: macierz capability wszystkich czterech ról, operacje HTTP zmiany nazwy/roli, odebrania dostępu i przekazania własności. Ochrona ostatniego Owner: równoległe degradacje, usunięcia i wariant mieszany przez API. Przekazanie zachowuje konta; zasymulowany błąd drugiego zapisu wycofuje oba zapisy.
- 006-tenant-isolation: lista tylko własnych gospodarstw, obce identyfikatory gospodarstwa i członkostwa, identyczny 404 dla obcego/nieistniejącego gospodarstwa, odebranie dostępu i zmiana roli w istniejącej sesji, brak przenoszenia roli między gospodarstwami i brak obejścia przez superuser.
- Dodatkowo: ponowna kontrola roli po oczekiwaniu na blokadę, CSRF wszystkich zapisów, anonimowa odmowa wszystkich endpointów, unikalność członkostwa i poprawność roli w bazie, logi bez haseł i nazw danych, Cache-Control: no-store.

## Jakość i uruchomienie
Ruff format/check, Prettier, ESLint, Stylelint oraz TypeScript przeszły. Migracja households wygenerowana i sformatowana; makemigrations --check --dry-run: brak zmian.
Obraz backendu zbudowany i uruchomiony przez Compose; migracje wykonane przed uruchomieniem backendu.
Nie dodano kont ani przykładowych gospodarstw do bazy użytkownika; testy korzystają z osobnej bazy testowej.

## Zakres kolejnych testów
Polityka uprawnień jest gotowa dla zaproszeń, członków i dochodów; testy HTTP tych zasobów wymagają endpointów z boltów 004 i 005. To powiązane kryteria integracyjne story 005, pozostające w odbiorze tych boltów.
Przełączanie gospodarstwa przez UI i kompletna ścieżka użytkownika: bolty 006–008.
Nie mierzono P95 całego produktu ani nie wykonano odbioru całego MVP; pomiar z docelowymi danymi pozostaje w bolcie 008.
