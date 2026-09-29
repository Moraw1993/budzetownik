---
stage: adr
bolt: 002-foundation-api
status: accepted
created: 2026-09-10T05:46:12.392Z
---
# ADR-001: Sesje Django i jawna ochrona CSRF

Lokalny frontend i API mają wspólny origin. Sesje Django zapewniają wylogowanie i unieważnienie dostępu po zmianie hasła bez tokenów w localStorage.
Wybrano Django REST Framework do walidacji wejścia i warstwy HTTP.
Login i konfiguracja anonimowa otrzymują jawną ochronę CSRF; domyślna autoryzacja API wymaga sesji.
Limity prób są w PostgreSQL, ponieważ lokalny cache pojedynczego procesu nie jest wspólny dla workerów Gunicorn.
Decyzja wykonawcza w zakresie zatwierdzonych wymagań.
