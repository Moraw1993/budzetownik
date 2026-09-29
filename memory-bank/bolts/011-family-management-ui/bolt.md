---
id: 011-family-management-ui
unit: 002-family-management-ui
intent: 002-family-income-management
type: simple-construction-bolt
status: in-progress
stories:
  - 001-family-navigation
  - 002-contract-company-forms
  - 003-other-source-and-conversion
created: 2026-09-23T08:28:54Z
started: 2026-09-26T19:46:13Z
completed: null
current_stage: implement
stages_completed:
  - name: plan
    completed: 2026-09-26T19:49:21Z
    artifact: implementation-plan.md
requires_bolts: ["010-family-income-api"]
enables_bolts: ["012-family-income-acceptance"]
requires_units: ["001-family-income-api", "003-household-foundation-ui"]
blocks: true
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 2
  testing_scope: 3
---

# Interfejs zarządzania rodziną

## Cel

Zastąpić obecny podział „Członkowie” i „Dochody” działem „Zarządzanie rodziną” z osobnymi akcjami dla umowy i innego źródła oraz widocznym miejscem źródeł całego gospodarstwa.

## Stories

- [ ] [001-family-navigation](../../intents/002-family-income-management/units/002-family-management-ui/stories/001-family-navigation.md): Nawigacja, członkowie i źródła.
- [ ] [002-contract-company-forms](../../intents/002-family-income-management/units/002-family-management-ui/stories/002-contract-company-forms.md): Firma i formularz umowy.
- [ ] [003-other-source-and-conversion](../../intents/002-family-income-management/units/002-family-management-ui/stories/003-other-source-and-conversion.md): Inne źródło oraz jawna konwersja.

## Etapy

- [x] Plan implementacji i przegląd ponownego użycia obecnych komponentów.
- [ ] Implementacja ekranów, formularzy, typów API i responsywnych stylów.
- [ ] Testy przepływów, ról, walidacji i dostępności klawiaturowej.

## Wyniki

Nowa nawigacja i ekran rodziny, formularze firm/umów/innych źródeł, aktualizacja typów API, testy UI i raport wizualny szerokiego oraz mobilnego widoku.

## Zależności

Wymaga ukończonego [010-family-income-api](../010-family-income-api/bolt.md) i zachowuje wynik responsywnego bolta 009. Po zakończeniu umożliwia odbiór w 012.

## Warunki zakończenia

Wszystkie scenariusze UI przechodzą bez tworzenia przychodów miesięcznych. Istniejące formularze i style nie są kopiowane bez potrzeby; `scripts/quality.ps1`, build i testy interfejsu przechodzą.
