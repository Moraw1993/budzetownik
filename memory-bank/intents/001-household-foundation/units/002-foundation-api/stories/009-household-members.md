---
id: 009-household-members
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 005-foundation-api
implemented: true
requirements:
  - FR-06
  - NFR-01
---
# Członkowie niezależni od kont

## User Story
Jako Administrator chcę zarządzać członkami, aby opisać całe gospodarstwo.

## Kryteria akceptacji
- [ ] Owner/Administrator dodaje członka bez konta i bez dochodów oraz edytuje jego dane; Member/Viewer ma tylko odczyt.
- [ ] Powiązanie konta dotyczy użytkownika należącego do tego gospodarstwa; nie można powiązać osoby spoza gospodarstwa.
- [ ] Proponowane ograniczenie projektu do przeglądu: konto może wskazywać najwyżej jednego członka w danym gospodarstwie, niezależnie od powiązań w innych gospodarstwach.

## Zależności
Bolty wymagane: 004-foundation-api.
W tym bolcie poprzedzają: Brak.
Pełna identyfikacja story: 002-foundation-api/009-household-members.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
