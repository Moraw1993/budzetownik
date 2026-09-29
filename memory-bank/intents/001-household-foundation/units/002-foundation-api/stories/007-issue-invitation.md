---
id: 007-issue-invitation
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 004-foundation-api
implemented: true
requirements:
  - FR-04
  - FR-05
---
# Wydanie i odwołanie zaproszenia

## User Story
Jako Owner chcę utworzyć kopiowany link, aby zaprosić osobę bez e-maila.

## Kryteria akceptacji
- [ ] Owner tworzy zaproszenie przypisane do gospodarstwa i roli, ważne 7 dni od utworzenia.
- [ ] Owner może odwołać zaproszenie; lista i podgląd nie ujawniają zaproszeń innych gospodarstw.
- [ ] Link zawiera nieprzewidywalny token, który nie trafia do logów; zaproszenie nie wymaga wysyłki e-maila.

## Zależności
Bolty wymagane: 003-foundation-api.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 002-foundation-api/007-issue-invitation.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
