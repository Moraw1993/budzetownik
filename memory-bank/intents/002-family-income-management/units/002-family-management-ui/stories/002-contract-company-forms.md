---
id: 002-contract-company-forms
unit: 002-family-management-ui
intent: 002-family-income-management
status: complete
priority: must
created: '2026-09-23T08:26:40Z'
assigned_bolt: 011-family-management-ui
implemented: true
requirements:
  - FR-02
  - FR-03
  - FR-05
  - FR-07
---

# Formularz firmy i umowy

## User Story

Jako Administrator chcę dodać firmę i umowę osoby, widząc wyraźnie, że wpisuję kwotę brutto z umowy.

## Kryteria akceptacji

- [ ] Z formularza umowy można wybrać istniejącą firmę albo dodać nową, której jedynym wymaganym polem jest nazwa, bez utraty wcześniej wpisanych danych.
- [ ] Formularz zbiera osobę, typ, daty, walutę, kwotę brutto i podstawę; pole stanowiska jest wyświetlane dla pracy i zlecenia, a „inne” pozwala podać nazwę typu.
- [ ] Można edytować i archiwizować umowę; lista wskazuje osobę, firmę, typ, okres, brutto i podstawę bez sugerowania zrealizowanego przychodu.
- [ ] Owner i Administrator widzą akcje zmiany; Member i Viewer mają odczyt. Błędy walidacji API pojawiają się przy odpowiednich polach.

## Zależności

001-family-navigation i API firm/umów z bolta 010.
