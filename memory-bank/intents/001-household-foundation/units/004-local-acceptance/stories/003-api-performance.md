---
id: 003-api-performance
unit: 004-local-acceptance
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 008-local-acceptance
implemented: true
requirements:
  - PRD-63
---
# Pomiar wydajności lokalnej

## User Story
Jako operator chcę poznać wydajność podstawowych widoków, aby zweryfikować cel PRD.

## Kryteria akceptacji
- [ ] Plan pomiaru opisuje sprzęt, rozmiar syntetycznych danych, rozgrzewkę i równoległość; nie przypisuje wynikom reprezentatywności bez tych danych.
- [ ] Dla podstawowych operacji API bez integracji zewnętrznych raport zawiera P95 i porównanie z celem PRD <500 ms.
- [ ] Jeżeli cel nie został osiągnięty, raport wskazuje operację, warunki i dalsze działania; testy nie są oznaczane jako zaliczone bez pomiaru.

## Zależności
Bolty wymagane: 009-household-foundation-ui.
W tym bolcie poprzedzają: 001-end-to-end-acceptance, 002-backup-restore.
Pełna identyfikacja story: 004-local-acceptance/003-api-performance.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
