---
unit: 001-local-runtime
intent: 001-household-foundation
unit_type: infrastructure
default_bolt_type: simple-construction-bolt
phase: inception
status: complete
created: '2026-09-09T22:26:09.504Z'
updated: '2026-09-09T22:26:09.504Z'
---
# Lokalne środowisko Docker

## Cel i zakres
Powtarzalny start środowiska, migracje, konfiguracja i trwałe dane. Funkcje aplikacji implementuje backend i UI.

## Przypisane wymagania
NFR-02.


## Encje i granice
Kontenery frontendu, Django, PostgreSQL; wolumen bazy i plików; lokalna konfiguracja HTTPS.
Interfejsy między frontendem i backendem będą określone przed implementacją UI; protokół HTTP/JSON z lokalnym HTTPS.
Logika i autoryzacja w Django; PostgreSQL i Django ORM; dane dziesiętne.
Nie dodawać wymagań z MVP 2–5 do tego etapu.

## Zależności
Brak innych jednostek.

## Stories
Łącznie 2, wszystkie Must, status draft.
- [001-compose-start](stories/001-compose-start.md): Uruchomienie przez Compose.
- [002-persistent-storage](stories/002-persistent-storage.md): Trwałe dane i konfiguracja.

## Plan realizacji
- 001-local-runtime: Docker, konfiguracja i trwałość.

## Kryteria sukcesu
- Wszystkie kryteria stories zweryfikowane rzeczywistymi wynikami.
- Brak zmiany uzgodnionej macierzy uprawnień i zakresu.
- Błędy i limity testów jawnie opisane, bez deklarowania wykonania planowanych testów.
