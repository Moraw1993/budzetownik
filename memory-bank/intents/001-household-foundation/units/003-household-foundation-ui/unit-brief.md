---
unit: 003-household-foundation-ui
intent: 001-household-foundation
unit_type: frontend
default_bolt_type: simple-construction-bolt
phase: construction
status: complete
created: '2026-09-09T22:26:09.504Z'
updated: '2026-09-23T20:23:56Z'
---
# Interfejs gospodarstwa

## Cel i zakres
Realizacja interfejsu FR należących do backendu; frontend wyświetla stan i wywołuje API, nie jest granicą autoryzacji. Bez dashboardu finansowego i pustych modułów przyszłego MVP.

## Przypisane wymagania
FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08.
FR są realizowane w interfejsie; właścicielem reguł jest 002-foundation-api.

## Encje i granice
Ekrany konfiguracji, logowania, wyboru gospodarstwa, ról, zaproszeń, członków i źródeł dochodu.
Interfejsy między frontendem i backendem będą określone przed implementacją UI; protokół HTTP/JSON z lokalnym HTTPS.
Logika i autoryzacja w Django; PostgreSQL i Django ORM; dane dziesiętne.
Nie dodawać wymagań z MVP 2–5 do tego etapu.
Standard projektowy i adnotacje dla agenta planującego UI: [design-system.md](../../../../standards/design-system.md).

## Zależności
001-local-runtime, 002-foundation-api

## Stories
Łącznie 6, wszystkie Must. Stories 001–003 ukończono w bolcie 006, stories 004–005 w bolcie 007; story 006 koryguje układ w bolcie 009.
- [001-account-screens](stories/001-account-screens.md): Konfiguracja i logowanie w przeglądarce.
- [002-household-screens](stories/002-household-screens.md): Gospodarstwa i role w interfejsie.
- [003-invitation-screens](stories/003-invitation-screens.md): Kopiowanie i przyjęcie zaproszeń.
- [004-members-screens](stories/004-members-screens.md): Członkowie i relacje w interfejsie.
- [005-income-screens](stories/005-income-screens.md): Źródła dochodu w interfejsie.
- [006-responsive-content-density](stories/006-responsive-content-density.md): Responsywna gęstość ekranów gospodarstwa.

## Plan realizacji
- 006-household-foundation-ui: Interfejs kont, gospodarstw i zaproszeń.
- 007-household-foundation-ui: Interfejs członków i dochodów.
- 009-household-foundation-ui: Gęstość i responsywność ekranów gospodarstwa.

## Kryteria sukcesu
- Wszystkie kryteria stories zweryfikowane rzeczywistymi wynikami.
- Brak zmiany uzgodnionej macierzy uprawnień i zakresu.
- Błędy i limity testów jawnie opisane, bez deklarowania wykonania planowanych testów.
