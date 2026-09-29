---
id: 011-income-sources
unit: 002-foundation-api
intent: 001-household-foundation
status: complete
priority: must
created: '2026-09-09T22:26:09.504Z'
assigned_bolt: 005-foundation-api
implemented: true
requirements:
  - FR-08
  - NFR-03
---
# Źródła dochodu

## User Story
Jako Administrator chcę zapisać źródła dochodu, aby przygotować dane do budżetu.

## Kryteria akceptacji
- [ ] Formularz/API zapisuje wszystkie pola FR-08, a źródło należy do gospodarstwa i opcjonalnie jego członka; właściciel innego gospodarstwa jest odrzucany.
- [ ] Owner/Administrator dodaje, edytuje i dezaktywuje źródła; Member/Viewer nie może ich zmienić. Członek może mieć zero lub wiele źródeł.
- [ ] Kwoty dziesiętne i waluta zachowują wartość po zapisie/odczycie; nazwy świadczeń są edytowalne; źródło nie tworzy miesięcznego przychodu ani transakcji.

## Zależności
Bolty wymagane: 004-foundation-api.
W tym bolcie poprzedzają: 009-household-members, 010-family-relations.
Pełna identyfikacja story: 002-foundation-api/011-income-sources.

## Uwagi techniczne
Stosować standardy projektu i zatwierdzone wymagania. Szczegóły implementacji określa projekt bolta.
Testować zachowanie także przez API, jeżeli kryterium dotyczy uprawnień.
Poza zakresem: budżety miesięczne, płatności kredytów, inwestycje, integracje bankowe i import Excel.
