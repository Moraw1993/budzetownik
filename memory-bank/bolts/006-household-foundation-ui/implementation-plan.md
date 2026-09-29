---
stage: plan
bolt: 006-household-foundation-ui
status: accepted
created: 2026-09-20T18:25:36Z
---

# Plan implementacji: konta, gospodarstwa i zaproszenia

## Cel i źródła

Zastąpić ekran gotowości środowiska działającym interfejsem stories 001–003 jednostki 003-household-foundation-ui. Backend bolta 005 ma status complete. Podstawą są product-requirements.md, wymagania FR-01–FR-05, design-system.md, coding-standards.md oraz ADR-001, ADR-002 i ADR-003. W repozytorium nie znaleziono osobnych plików design.md ani specs.md; ich rolę pełnią wskazany standard projektowy, bolt.md i stories.

Poza zakresem: członkowie rodziny i dochody (bolt 007), odbiór całego fundamentu (008), budżety, kredyty, oszczędności i analityka.

## Rezultaty

1. Konfiguracja pierwszego konta, logowanie, wylogowanie i informacja o lokalnej procedurze odzyskiwania dostępu.
2. Lista gospodarstw, tworzenie gospodarstwa z domyślną walutą PLN, wybór aktywnego gospodarstwa i widoczna rola użytkownika.
3. Lista dostępów użytkowników; Owner zmienia role, pozostali mają odczyt. Odmowa zmiany ostatniego Ownera pochodzi z API i nie powoduje pozornej aktualizacji widoku.
4. Owner wystawia zaproszenie z wybraną rolą, widzi termin ważności, kopiuje link i odwołuje zaproszenie po potwierdzeniu.
5. Strona /accept-invitation obsługuje utworzenie konta lub logowanie istniejącej osoby i jawne przyjęcie zaproszenia. Po sukcesie wybiera gospodarstwo wynikające z odświeżonej listy członkostw.
6. Raport implementacji i rzeczywistych testów, aktualizacja statusów dopiero po odpowiednich checkpointach.

## Architektura i istniejące elementy

- Zachować Next.js App Router i wspólny origin obsługiwany przez Caddy. Przeglądarka wywołuje względne ścieżki /api/; nie potrzebuje adresu kontenera backendu.
- Wydzielić klienta HTTP, typy odpowiedzi, obsługę sesji i kontekstu gospodarstwa oraz komponenty formularzy, dostępów i zaproszeń. Przed dodaniem każdego elementu wyszukać istniejący odpowiednik.
- Użyć istniejących endpointów auth/setup, login, logout, me; households i memberships; invitations oraz invitations/accept. Nie przenosić reguł domenowych do frontendu.
- Klient HTTP pobiera CSRF z GET /api/auth/setup/ i dołącza X-CSRFToken do zapisów. Po zalogowaniu lub utworzeniu konta odświeża token, ponieważ Django obraca sekret sesji. Dane sesji i zaproszeń nie trafiają do localStorage.
- GET setup rozstrzyga konfigurację pierwszego konta; GET me rozstrzyga aktywną sesję. Brak autoryzacji to stan logowania, błąd sieci to błąd z ponowieniem, a nie pusta instalacja.
- Wylogowanie usuwa chroniony stan; przywrócenie strony z historii wymaga ponownego sprawdzenia sesji przed ujawnieniem danych. Błąd wylogowania nie może być komunikowany jako zakończenie sesji.
- Zmiana gospodarstwa natychmiast usuwa jego poprzednie dane, komunikaty i wygenerowany link. Anulowanie odczytów oraz identyfikator generacji kontekstu chronią przed spóźnionymi odpowiedziami także po mutacji i wylogowaniu.
- Po 401/403 sprawdzić stan sesji i dostępu; nie traktować każdego 403 jako wygaśnięcia sesji. Brak dostępu do gospodarstwa usuwa jego chronione dane. 5xx i odpowiedzi nie-JSON mają bezpieczny komunikat bez treści serwera.
- Mutacje pokazują sukces dopiero po potwierdzeniu API. Blokada formularza zapobiega wielokrotnemu wysłaniu; niesekretne wartości pozostają po błędzie walidacji.

## Zaproszenia i role

- Token odczytywać wyłącznie po stronie klienta z fragmentu URL; usunąć fragment z bieżącego wpisu historii i utrzymywać token tylko w pamięci przepływu. Nie logować tokenu ani umieszczać go w query stringu.
- Logowanie istniejącego użytkownika odbywa się w tym samym przepływie, aby nie utracić tokenu. Przyjęcie wymaga świadomego wysłania formularza; wejście w link nie zużywa go automatycznie.
- Odpowiedź przyjęcia zawiera membership id, a nie household id. Powiązać ją z membership_id po ponownym pobraniu listy gospodarstw, bez zgadywania identyfikatora.
- Niepoprawny, wygasły, odwołany lub zużyty link pokazuje bezpieczny komunikat i wskazuje potrzebę nowego zaproszenia od Ownera.
- Lista zaproszeń jest pobierana tylko dla Ownera. Administrator, Member i Viewer mają odczyt listy dostępów, bez edycji ról i bez pobierania zaproszeń.
- Po wystawieniu link widoczny jest do skopiowania; błąd schowka pozwala skopiować tekst ręcznie. Lista nie odtwarza sekretnego linku z API. Pokazać lokalną datę ważności i tekst statusu.
- Wyjaśnić, że localhost działa na komputerze hostującym aplikację. Brak wysyłki wiadomości i e-maili.

## Interfejs i dostępność

- Zastosować tokeny granatowych powierzchni z design-system.md, neutralny niebieski dla akcji i tekstowe komunikaty statusu.
- Układ po logowaniu: sidebar, topbar z gospodarstwem i kontem oraz główna treść. Na wąskim ekranie zachować wszystkie akcje i czytelne listy; nie dodawać pustych modułów przyszłych MVP.
- Przy wdrażaniu komponentów uwzględnić zapisany stos Tailwind CSS, shadcn/ui i Lucide; istniejący bootstrap ma wyłącznie CSS Modules. Konfigurację zależności objąć formatterami, lintem i lockfile.
- Wybrać jeden lokalnie dostarczany krój z preferowanych w standardzie; bez pobierania fontów przez przeglądarkę z usług zewnętrznych.
- Każdy formularz: widoczne etykiety, właściwe autocomplete, błędy powiązane z polami, komunikat zbiorczy i focus na błędzie. Stany: spoczynek, hover, focus-visible, disabled, zapis, sukces i błąd.
- Każda lista: ładowanie, brak danych, błąd z ponowieniem i brak uprawnień. Komunikaty dynamiczne używają role=status lub role=alert.
- Potwierdzenie odwołania zaproszenia pozwala anulować operację klawiaturą i przywraca focus. Kontrast WCAG AA oraz obszary interakcji co najmniej 32 × 32 px.

## Plan weryfikacji

- Sprawdzić pustą instalację i istniejące konto; błędne hasło, niepoprawne pola, limit prób, ponowienie po błędzie sieci i równoległe zakończenie konfiguracji.
- Sprawdzić konfigurację, logowanie i akceptację z CSRF, odświeżenie tokenu po zalogowaniu oraz wylogowanie i powrót przez historię.
- Utworzyć dwa gospodarstwa; spowolnić odpowiedź pierwszego i przełączyć na drugie. Spóźniona odpowiedź nie może odtworzyć danych pierwszego. Powtórzyć dla trwającego zapisu.
- Sprawdzić role Owner/Administrator/Member/Viewer, odmowę API po zmianie uprawnień w innej sesji oraz ochronę ostatniego Ownera. Wykorzystać istniejące testy backendu.
- Sprawdzić nowego i istniejącego użytkownika zaproszenia, prawidłowy wybór gospodarstwa, kopiowanie i fallback schowka, odwołanie, wygaśnięcie i ponowne użycie.
- Zweryfikować klawiaturę, Enter/Escape, focus, etykiety, tekstowe statusy, responsywność i kontrast w rzeczywistym widoku.
- Po każdym pliku kodu wykonać właściwy formatter i lint, obejrzeć wynik oraz sprawdzić duplikacje i odpowiedzialności. Przed zamknięciem etapu uruchomić scripts/quality.ps1, build frontendu i właściwe testy integracyjne.
- Raport rozróżnia testy API, testy interfejsu z kontrolowanymi odpowiedziami oraz pełny przebieg z rzeczywistym backendem. Nie oznaczać bolta complete bez dowodów akceptacji.

## Stan środowiska i checkpoint

Podczas rozpoznania Docker nie udostępniał połączenia z daemonem; klient zgłosił też brak dostępu do konfiguracji w profilu użytkownika. Nie uruchomiono kontenerów ani testów. Przed implementacją sprawdzić dostępne lokalne narzędzia oraz możliwość uruchomienia środowiska bez naruszania danych.

Katalog projektu nie jest obecnie repozytorium Git. Przegląd zmian będzie oparty na zmienionych plikach; nie deklarować wyniku git diff.

Plan zatwierdzony przez użytkownika poleceniem „continue”; rozpoczęto implementację 2026-09-20T18:27:41Z. Prefiks endpointów kont skorygowano po weryfikacji backend/config/urls.py.
