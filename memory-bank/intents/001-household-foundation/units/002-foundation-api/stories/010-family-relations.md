---
id: 010-family-relations
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 005-foundation-api
implemented: true
requirements:
  - FR-07
---
# Konfigurowalne relacje rodzinne

## User Story
Jako Administrator chcę definiować typy relacji, aby dopasować opis rodziny.

## Kryteria akceptacji
- [ ] Owner/Administrator tworzy typ relacji w swoim gospodarstwie i przypisuje go członkowi.
- [ ] Zmiana relacji rodzinnej nie zmienia uprawnień aplikacyjnych i nie modyfikuje słownika innego gospodarstwa.
- [ ] Usunięcie używanego typu nie niszczy członka; projekt przewiduje dezaktywację albo jawną zmianę powiązania.

## Zależności
Bolty wymagane: 004-foundation-api.
W tym bolcie poprzedzają: 009-household-members.
Pełna identyfikacja story: 002-foundation-api/010-family-relations.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
