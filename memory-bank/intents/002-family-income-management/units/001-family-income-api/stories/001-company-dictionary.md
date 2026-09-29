---
id: 001-company-dictionary
unit: 001-family-income-api
intent: 002-family-income-management
status: complete
priority: must
created: '2026-09-23T08:26:40Z'
assigned_bolt: 010-family-income-api
implemented: true
requirements:
  - FR-02
  - FR-07
---

# Słownik firm gospodarstwa

## User Story

Jako Administrator chcę zapisać firmę raz i wybierać ją przy wielu umowach tego gospodarstwa.

## Kryteria akceptacji

- [ ] Nazwa jest jedynym wymaganym polem firmy; zapis tworzy identyfikator i pozwala wybrać firmę przy kolejnych umowach.
- [ ] Firma należy do dokładnie jednego gospodarstwa. Żądanie dotyczące firmy innego gospodarstwa nie ujawnia ani nie zmienia jej danych.
- [ ] Owner i Administrator mogą dodawać, edytować i archiwizować firmę; Member i Viewer mogą ją tylko odczytać.
- [ ] Archiwizacja firmy nie usuwa istniejących umów ani audytu; nie można przypisać archiwalnej firmy do nowej umowy.

## Zależności

Istniejące gospodarstwa, role i mechanizm audytu. Pierwsza story w bolcie 010.
