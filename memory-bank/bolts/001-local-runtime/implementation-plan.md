---
stage: plan
bolt: 001-local-runtime
created: 2026-09-09T22:32:57.931Z
---
# Plan implementacji środowiska lokalnego

## Zakres
Compose: PostgreSQL 17, Django 5.2 LTS na Python 3.13, Next.js 16 na Node 22, Caddy 2 dla HTTPS localhost.
Minimalny szkielet aplikacji i endpoint gotowości; logowanie i domeny następnych boltów nie są implementowane tutaj.
Konfiguracja generowana lokalnie; hasła nie trafiają do repozytorium. Kontenery z trwałymi wolumenami.

## Wyniki
compose.yaml, obrazy backendu i frontendu, lokalny proxy HTTPS, .env.example, skrypt konfiguracji, instrukcja startu i test trwałości.
Backend: Django, psycopg, Gunicorn; bez zainstalowanego auth/modelu użytkownika do czasu bolta 002, aby nie utrwalić niewłaściwego modelu.
Migracje osobną usługą przed backendem; blokada PostgreSQL chroni przed współbieżnym uruchomieniem.
Healthcheck bazy i backendu kontroluje kolejność uruchamiania.

## Kryteria
- Compose buduje i uruchamia usługi oraz kończy migracje powodzeniem.
- Lokalny HTTPS odpowiada; aplikacja i baza gotowe.
- Odtworzenie kontenerów zachowuje testowy rekord i plik wolumenu.
- Brak wymaganej konfiguracji powoduje czytelny błąd bez sekretów.
- Sprawdzenie uruchomienia przy chwilowo niedostępnej bazie.
- Instalowanie lokalnego CA do zaufanych certyfikatów wymaga świadomej decyzji użytkownika; testy mogą używać wyeksportowanego CA bez zmiany magazynu zaufania.

## Źródła decyzji
- https://docs.djangoproject.com/en/5.2/releases/5.2/
- https://docs.docker.com/compose/how-tos/startup-order/
- https://nextjs.org/docs/app/getting-started/installation
- https://caddyserver.com/docs/automatic-https