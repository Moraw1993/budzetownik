# Domowe Finanse

Lokalny fundament aplikacji: Django, Next.js, PostgreSQL i Docker Compose.
Gotowe: lokalny runtime oraz interfejs kont, sesji, gospodarstw, ról, zaproszeń, członków, relacji i źródeł dochodu.

## Uruchomienie na Windows

Wymagany działający Docker Desktop z kontenerami Linux i Docker Compose v2.

Z folderu projektu:
```powershell
powershell -File scripts/configure.ps1
docker compose up --build -d
docker compose ps -a
```
Skrypt tworzy lokalny plik .env z losowymi sekretami; nie nadpisuje istniejącego.
Baza i aplikacja muszą być healthy, migrate ma zakończyć się kodem 0.
Pierwsze budowanie pobiera obrazy i zależności z internetu.

Otwórz https://localhost:8443. HTTP http://localhost:8080 przekierowuje na HTTPS.
Baza nie publikuje portu. Aplikacja jest dostępna wyłącznie z tego komputera.

## Lokalny certyfikat HTTPS

Caddy tworzy własny urząd certyfikacji i zapisuje go w trwałym wolumenie.
Kontener nie instaluje zaufania w Windows automatycznie.

Wyeksportuj publiczny certyfikat:
```powershell
New-Item -ItemType Directory -Path .runtime -Force
docker compose cp proxy:/data/caddy/pki/authorities/local/root.crt .runtime/localhost-root.crt
```
Po sprawdzeniu pochodzenia certyfikatu możesz świadomie zaufać mu dla bieżącego użytkownika:
```powershell
Import-Certificate -FilePath .runtime/localhost-root.crt -CertStoreLocation Cert:\CurrentUser\Root
```
Ta operacja zmienia magazyn zaufania Windows. Nie jest wykonywana przez skrypt konfiguracji.
Przeglądarki z własnym magazynem certyfikatów mogą wymagać osobnego importu.
Usunięcie wolumenu Caddy zmieni urząd CA i wymaga ponownej konfiguracji zaufania.

## Codzienna obsługa

```powershell
docker compose logs --tail 50 backend migrate
docker compose stop
docker compose up --build -d
```
Zatrzymanie lub odtworzenie kontenerów zachowuje dane w wolumenach.
Nie używaj docker compose down -v, jeśli chcesz zachować dane: usuwa wolumeny.
Nie zmieniaj hasła PostgreSQL w .env dla istniejącej bazy bez zmiany hasła w samej bazie.
Wolumen nie zastępuje kopii zapasowej. [Procedura kopii i odtworzenia](memory-bank/operations/backup-restore.md) opisuje bazę, załączniki, konfigurację i sprawdzenie odtworzonej instalacji.

Migracje uruchamia osobna usługa migrate, po gotowości bazy i przed startem Django.
Blokada w PostgreSQL zabezpiecza równoległe uruchomienia migracji.
API konfiguracji pierwszego konta: /api/auth/setup/. Wymaga CSRF uzyskanego przez GET tego endpointu. API sesji: /api/auth/login/, /api/auth/logout/, /api/auth/me/. Interfejs przeglądarkowy obsługuje te operacje.

## Sprawdzenie

```powershell
docker compose config --quiet
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test households accounts runtime
cd frontend
npm run test:ui
```
Nie wyświetlaj pełnego docker compose config w udostępnianych logach: zawiera wartości środowiska.
Sprawdzenie API: https://localhost:8443/api/health/ (200 oznacza gotową bazę i aktualne migracje).

## Dokumentacja
Plan: memory-bank/intents/001-household-foundation/review.md.
Implementacja runtime: memory-bank/bolts/001-local-runtime/.

## Jakość kodu

Po każdej zmianie kodu używaj właściwego formattera. Pełne sprawdzenie z poziomu PowerShell:
    
    ./scripts/quality.ps1

Automatyczne poprawki i ponowne sprawdzenie:

    ./scripts/quality.ps1 -Fix

Narzędzia działają w Dockerze. Zależności narzędzi frontendowych używają osobnego wolumenu, aby nie przenosić tysięcy plików na Windows.
Prettier formatuje TS/TSX/JS/JSON/YAML/CSS, Ruff Python; ESLint i Stylelint sprawdzają błędy oraz duplikaty deklaracji.
Przegląd odpowiedzialności funkcji i współdzielenia logiki pozostaje wymagany; automatyczne narzędzia nie wykrywają wszystkich duplikatów semantycznych.
Zasady trwałe: AGENTS.md i memory-bank/standards/coding-standards.md; agent Construction specs.md ma tę samą instrukcję.

## Odzyskiwanie konta

Operator instalacji wykonuje:

    docker compose exec backend python manage.py recover_account LOGIN

Polecenie dwukrotnie pyta o nowe hasło bez jego wyświetlania. Zmiana unieważnia poprzednie sesje; nie tworzy brakującego konta i nie zmienia ról.

## Test trwałości runtime

    python scripts/verify_runtime.py

Wymaga Python 3.12+ na hoście. Test odtwarza kontenery i na krótko zatrzymuje bazę MyHomeBudget; zachowuje wolumeny i sprząta tylko własne znaczniki.
## Gospodarstwa i role (backend)

GET/POST /api/households/ obsługuje listę własnych gospodarstw i tworzenie nowego.
GET/PATCH /api/households/{id}/ odczytuje gospodarstwo lub zmienia jego nazwę.
GET /api/households/{id}/memberships/ pokazuje konta z dostępem.
PATCH/DELETE /api/households/{id}/memberships/{membership_id}/ zmienia rolę lub odbiera dostęp.
POST /api/households/{id}/transfer-ownership/ z membership_id przekazuje własność istniejącemu członkostwu; dotychczasowy właściciel zostaje Administrator.

Każdy adres wymaga zalogowania, zapisy wymagają CSRF. Twórca gospodarstwa zostaje Owner; tylko Owner zarządza rolami i dostępem.
Usunięcie ostatniego Owner jest blokowane. Odebranie członkostwa nie usuwa konta.
Wybrane gospodarstwo wskazuje identyfikator w adresie; każda operacja ponownie sprawdza członkostwo.
Zaproszenia są tworzone przez Ownera i przyjmowane z jednorazowego lokalnego linku. Osoby w rodzinie są odrębne od kont aplikacji i mogą być z nimi opcjonalnie powiązane.
Interfejs obsługi kont, gospodarstw, ról i zaproszeń znajduje się w bolcie 006. Członkowie, relacje i źródła dochodu są realizowane w bolcie 007.
Stronicowane endpointy `/members/`, `/relation-types/` i `/income-sources/` działają w kontekście wybranego gospodarstwa. Owner i Administrator zapisują dane; Member i Viewer mają odczyt. Dezaktywacja zachowuje historię i powiązania.
Projekt API: memory-bank/bolts/003-foundation-api/. Raporty interfejsu: memory-bank/bolts/006-household-foundation-ui/ i memory-bank/bolts/007-household-foundation-ui/.
