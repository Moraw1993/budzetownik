---
id: 013-preserve-history
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 005-foundation-api
implemented: true
requirements:
  - FR-06
  - FR-08
  - FR-09
---
# Dezaktywacja bez utraty historii

## User Story
Jako Administrator chcę dezaktywować członka lub źródło, aby zachować historyczne powiązania.

## Kryteria akceptacji
- [ ] Dezaktywacja członka nie kasuje jego źródeł i historii zmian; stan archiwalny jest rozróżnialny od aktywnego.
- [ ] Dezaktywacja źródła zachowuje jego dane i audyt; nie ma kaskadowego usunięcia historii.
- [ ] Próba operacji destrukcyjnej przez Member/Viewer lub użytkownika innego gospodarstwa jest odrzucana.

## Zależności
Bolty wymagane: 004-foundation-api.
W tym bolcie poprzedzają: 009-household-members, 010-family-relations, 011-income-sources, 012-financial-audit.
Pełna identyfikacja story: 002-foundation-api/013-preserve-history.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
