# Lokalne wdrożenie MVP

Status: wymagania wdrożenia; pliki Docker i aplikacja nie zostały jeszcze zaimplementowane.
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
Wymaganie HTTPS z PRD pozostaje aktualne; sposób obsługi lokalnego certyfikatu zostanie określony w projekcie wdrożenia.
