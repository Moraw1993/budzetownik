# Plan realizacji MVP 1 — do przeglądu

Wymagania zatwierdzone przez użytkownika. Po korekcie plan obejmuje 4 jednostki, 24 scenariusze i 9 boltów.
Construction trwa. Plan bolta 009, dodanego po przeglądzie gęstości UI, oczekuje na akceptację.

## Kontekst
Lokalna przeglądarka → frontend React/TypeScript → modularny monolit Django → PostgreSQL.
Docker Compose, trwałe wolumeny, lokalny HTTPS. Bez SMTP i usług bankowych.
Operator obsługuje instalację; Owner role i zaproszenia; Administrator członków i dochody; Member/Viewer mają odczyt.

## Kolejność prac
| Etap | Wynik | Stories | Typ |
|---|---|---:|---|
| 1 | [Docker, konfiguracja i trwałość](../../bolts/001-local-runtime/bolt.md) | 2 | Simple |
| 2 | [Konta, sesje i odzyskanie dostępu](../../bolts/002-foundation-api/bolt.md) | 3 | DDD |
| 3 | [Gospodarstwa, role i izolacja](../../bolts/003-foundation-api/bolt.md) | 3 | DDD |
| 4 | [Zaproszenia bez e-maili](../../bolts/004-foundation-api/bolt.md) | 2 | DDD |
| 5 | [Członkowie, dochody i audyt](../../bolts/005-foundation-api/bolt.md) | 5 | DDD |
| 6 | [Interfejs kont, gospodarstw i zaproszeń](../../bolts/006-household-foundation-ui/bolt.md) | 3 | Simple |
| 7 | [Interfejs członków i dochodów](../../bolts/007-household-foundation-ui/bolt.md) | 2 | Simple |
| 8 | [Gęstość i responsywność ekranów gospodarstwa](../../bolts/009-household-foundation-ui/bolt.md) | 1 | Simple |
| 9 | [Odbiór, kopie i wydajność](../../bolts/008-local-acceptance/bolt.md) | 3 | Simple |

## Odbiór
Pierwsze konto, dwa gospodarstwa, członek bez konta, źródła dochodu, zaproszenie, role i izolacja.
Sprawdzenie restartu, odtworzenia kontenerów i kopii w osobnej instalacji testowej.
Pomiar celu API P95 <500 ms z opisem sprzętu, danych i obciążenia.
Dane syntetyczne; prywatne arkusze nie są automatycznie importowane.

## Doprecyzowanie modelu do przeglądu
Konto jest powiązane najwyżej z jednym członkiem w danym gospodarstwie; w innym gospodarstwie może mieć osobne powiązanie.

## Decyzje techniczne w pierwszych boltach
Wersje, biblioteka API Django, sesje, narzędzia jakości, lokalny HTTPS i kontrakty API zostaną dobrane i udokumentowane podczas projektowania.
Frontend utrzymuje preferowany w PRD Next.js. Zależności należy zweryfikować przed instalacją.
Nie ma jeszcze konfiguracji uruchomieniowej ani przetestowanej aplikacji.

## Dokumenty
- [Kontekst](system-context.md)
- [Jednostki](units.md)
- [Pokrycie wymagań](traceability.md)
- [Indeks scenariuszy](../../story-index.md)
