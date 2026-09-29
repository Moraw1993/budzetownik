# Implementacja lokalnego runtime

Dostarczono lokalny stos Django, Next.js i PostgreSQL z Caddy dla HTTPS. Konto i domeny biznesowe są przedmiotem kolejnych boltów.

## Gotowe elementy
- [x] compose.yaml — kolejność startu, healthchecki, wolumeny, porty wyłącznie localhost.
- [x] backend/ — konfiguracja Django, kontrola gotowości i serializowane migracje, Gunicorn.
- [x] frontend/ — strona początkowa i produkcyjny obraz Next.js z blokadą zależności.
- [x] infra/Caddyfile — lokalny HTTPS i routing.
- [x] scripts/configure.ps1 — generowanie lokalnej konfiguracji bez nadpisywania.
- [x] README.md — start, certyfikat i obsługa danych.

## Decyzje
- Model użytkownika pozostaje do bolta 002; auth nie zostało jeszcze zmigrowane.
- Oddzielny proces migracji i blokada PostgreSQL zapobiegają współbieżności.
- Lokalny CA nie jest automatycznie importowany do magazynu zaufania Windows.
- Backend i frontend pracują jako użytkownicy bez uprawnień root.

## Zależności
Django 5.2.17, psycopg 3.3.5, Gunicorn 26.2.0; Next.js 16.3.4, React 19.3.0, TypeScript 5.9.3.
Źródła wersji: oficjalne rejestry PyPI i npm odczytane podczas realizacji.