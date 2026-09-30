# Lokalne wdrożenie MVP

Status: lokalny runtime Docker i aplikacja są zaimplementowane; odbiór rodziny zakończono w bolcie 012. Formalny stan Operations opisuje [raport domknięcia](post-bolt-012.md).
Źródło: decyzja użytkownika o lokalnym MVP przez Docker oraz wymagania PRD.

## Uruchamianie MVP

MVP działa lokalnie na komputerze użytkownika, w kontenerach Docker zarządzanych przez Docker Compose.
Frontend React/TypeScript, backend Django i PostgreSQL są uruchamiane jako usługi jednego projektu Compose.
Dostęp do aplikacji odbywa się z przeglądarki na tym samym komputerze przez localhost. Opublikowane porty aplikacji należy wiązać z 127.0.0.1; baza danych działa w wewnętrznej sieci kontenerów.
Dane PostgreSQL i załączniki muszą korzystać z trwałych wolumenów, zachowujących zawartość po restarcie i odtworzeniu kontenerów. Trwały wolumen nie zastępuje kopii zapasowej.
Załączniki MVP są przechowywane w filesystemie na trwałym wolumenie; metadane pozostają w PostgreSQL.
Docelowy sposób uruchomienia: docker compose up --build. Instrukcja wdrożenia musi obejmować konfigurację, migracje Django, utworzenie pierwszego użytkownika oraz wykonanie i odtworzenie kopii danych i załączników.
Konfiguracja lokalna i sekrety są przekazywane przez zmienne środowiskowe; repozytorium zawiera jedynie przykładowe wartości.
Hosting publiczny i dostęp z sieci domowej pozostają poza zakresem lokalnego MVP.
HTTPS obsługuje Caddy z lokalnym urzędem certyfikacji i trwałymi wolumenami. Instrukcja uruchomienia, pierwszego konta i świadomego dodania zaufania do certyfikatu znajduje się w [README](../../README.md). Procedura kopii i odtworzenia znajduje się w [backup-restore.md](backup-restore.md).
