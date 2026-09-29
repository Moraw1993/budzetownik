---
unit: 004-local-acceptance
intent: 001-household-foundation
unit_type: infrastructure
default_bolt_type: simple-construction-bolt
phase: construction
status: complete
created: '2026-09-09T22:26:09.504Z'
updated: '2026-09-23T21:10:12Z'
---
# Odbiór i eksploatacja lokalna

## Cel i zakres
Weryfikacja całości, odtwarzania danych i celu wydajności PRD. Testy na odrębnych danych, bez usuwania danych użytkownika.

## Przypisane wymagania
NFR-01, NFR-02, NFR-03.


## Encje i granice
Scenariusze odbioru, testowa instalacja, zestaw danych syntetycznych, kopie zapasowe, instrukcja operatora.
Interfejsy między frontendem i backendem będą określone przed implementacją UI; protokół HTTP/JSON z lokalnym HTTPS.
Logika i autoryzacja w Django; PostgreSQL i Django ORM; dane dziesiętne.
Nie dodawać wymagań z MVP 2–5 do tego etapu.

## Zależności
001-local-runtime, 002-foundation-api, 003-household-foundation-ui

## Stories
Łącznie 3, wszystkie Must, status complete.
- [001-end-to-end-acceptance](stories/001-end-to-end-acceptance.md): Odbiór całego fundamentu.
- [002-backup-restore](stories/002-backup-restore.md): Kopia i odtworzenie danych.
- [003-api-performance](stories/003-api-performance.md): Pomiar wydajności lokalnej.

## Plan realizacji
- 008-local-acceptance: Odbiór, kopie i wydajność.

## Kryteria sukcesu
- Wszystkie kryteria stories zweryfikowane rzeczywistymi wynikami.
- Brak zmiany uzgodnionej macierzy uprawnień i zakresu.
- Błędy i limity testów jawnie opisane, bez deklarowania wykonania planowanych testów.
