---
stage: design
bolt: 002-foundation-api
created: 2026-09-10T05:46:12.392Z
---
# Projekt kont i sesji

## Stos i podział
Django REST Framework 3.18.1: serializery, APIView i standardowe błędy.
accounts/models.py — User(AbstractUser) i licznik prób.
accounts/services.py — przypadki użycia.
accounts/throttling.py — współdzielony między procesami limit w PostgreSQL.
accounts/serializers.py — walidacja wejścia i bezpieczna odpowiedź.
accounts/views.py — cienka warstwa HTTP.
accounts/management/commands/recover_account.py — interaktywna lokalna zmiana hasła.

## Kontrakty API
- GET /api/auth/setup/: {setup_required: boolean}; ustawia token CSRF.
- POST /api/auth/setup/: {username, password}; 201 i {id, username}; 409 gdy konfiguracja zamknięta.
- POST /api/auth/login/: {username, password}; 200 {id, username}, 401 przy złych danych, 429 po przekroczeniu limitu.
- POST /api/auth/logout/: 204, wymaga sesji i CSRF.
- GET /api/auth/me/: {id, username}; bez sesji 403 zgodnie z SessionAuthentication.
POST logowania i konfiguracji muszą wymagać CSRF także dla anonimowego użytkownika — SessionAuthentication samo tego nie zapewnia.
Odpowiedzi kont bez cache; endpointy zwracają JSON. Sesja HttpOnly, Secure, SameSite=Lax; czas sesji 12 godzin.

## Baza i współbieżność
User od początku jako AUTH_USER_MODEL, przed pierwszą migracją auth.
Konfiguracja: PostgreSQL advisory transaction lock i sprawdzenie istnienia użytkownika w tej samej transakcji.
Limity: okno 15 minut, 5 prób dla loginu i 30 dla źródła; liczniki aktualizowane atomowo pod blokadą wiersza.
Klucze liczników to HMAC, nie jawne loginy; bez zaufania do dowolnego nagłówka klienta.
Udane logowanie zeruje licznik loginu, licznik źródła ogranicza łączną liczbę żądań. Wygasłe okno resetuje licznik.

## Hasła i odzyskiwanie
Walidatory Django: podobieństwo, hasła popularne/liczbowe, minimum 12 znaków, maksymalnie 128 znaków wejścia.
recover_account przyjmuje login, dwukrotnie pyta o hasło bez echa. Nie ma endpointu odzyskiwania ani SMTP.
Django weryfikuje hash sesji i unieważnia wcześniejsze sesje po zmianie hasła.
Testy obejmują bezpieczeństwo, CSRF, współbieżne tworzenie pierwszego konta i limity.

## Źródła
- https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication
- https://docs.djangoproject.com/en/5.2/topics/auth/customizing/
- https://docs.djangoproject.com/en/5.2/topics/auth/default/#session-invalidation-on-password-change
