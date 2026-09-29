---
id: 002-session-login
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 002-foundation-api
implemented: true
requirements:
  - FR-01
---
# Logowanie i wylogowanie

## User Story
Jako użytkownik chcę logować się i kończyć sesję, aby chronić dostęp do danych.

## Kryteria akceptacji
- [x] Poprawne dane logowania otwierają sesję; błędne dane nie otwierają sesji i nie ujawniają istnienia konkretnego konta.
- [x] Po wylogowaniu ponowne użycie wcześniejszej sesji nie umożliwia chronionych operacji.
- [x] Testy obejmują limity prób logowania, ochronę przed CSRF odpowiednią do sesji oraz żądania bez logowania; zdarzenia bezpieczeństwa nie zapisują haseł ani tokenów.

## Zależności
Bolty wymagane: 001-local-runtime.
W tym bolcie poprzedzają: 001-bootstrap-account.
Pełna identyfikacja story: 002-foundation-api/002-session-login.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
