---
id: 011-family-management-ui
unit: 002-family-management-ui
intent: 002-family-income-management
type: simple-construction-bolt
status: complete
stories:
  - 001-family-navigation
  - 002-contract-company-forms
  - 003-other-source-and-conversion
created: '2026-09-23T08:28:54Z'
started: '2026-09-26T19:46:13Z'
completed: '2026-09-29T20:57:35Z'
current_stage: null
stages_completed:
  - name: plan
    completed: '2026-09-26T19:49:21Z'
    artifact: implementation-plan.md
  - name: implement
    completed: '2026-09-29T20:37:58Z'
    artifact: implementation-walkthrough.md
  - name: test
    completed: 2026-09-29T20:57:35Z
    artifact: test-walkthrough.md
requires_bolts:
  - 010-family-income-api
enables_bolts:
  - 012-family-income-acceptance
requires_units:
  - 001-family-income-api
  - 003-household-foundation-ui
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

- [x] [001-family-navigation](../../intents/002-family-income-management/units/002-family-management-ui/stories/001-family-navigation.md): Nawigacja, członkowie i źródła.
- [x] [002-contract-company-forms](../../intents/002-family-income-management/units/002-family-management-ui/stories/002-contract-company-forms.md): Firma i formularz umowy.
- [x] [003-other-source-and-conversion](../../intents/002-family-income-management/units/002-family-management-ui/stories/003-other-source-and-conversion.md): Inne źródło oraz jawna konwersja.

## Etapy

- [x] Plan implementacji i przegląd ponownego użycia obecnych komponentów.
- [x] Implementacja ekranów, formularzy, typów API i responsywnych stylów.
- [x] Testy przepływów, ról, walidacji i dostępności klawiaturowej.

## Wyniki

Nowa nawigacja i ekran rodziny, formularze firm/umów/innych źródeł, aktualizacja typów API, testy UI i raport wizualny szerokiego oraz mobilnego widoku.

Aktualny kierunek wizualny: jasny design v3, wspólny dla całej aplikacji, opisany w [design systemie](../../standards/design-system.md) i [przeglądzie implementacji](implementation-walkthrough.md). Testy mają obejmować zakładki, karty członków i formularze otwierane na żądanie w tym designie. Wcześniejszy raport wizualny na danych demonstracyjnych nie zamyka etapu testów bolta.

[Raport testów](test-walkthrough.md) został zatwierdzony przez użytkownika: 42/42 uruchomione testy UI, 83/83 testy Django, build i kontrola jakości przeszły. Trzy scenariusze wymagające instalacji odbiorowej pominięto jawnie; pełny odbiór rzeczywistej instalacji pozostaje zakresem bolta 012.

## Zależności

Wymaga ukończonego [010-family-income-api](../010-family-income-api/bolt.md) i zachowuje wynik responsywnego bolta 009. Po zakończeniu umożliwia odbiór w 012.

## Warunki zakończenia

Wszystkie scenariusze UI przechodzą bez tworzenia przychodów miesięcznych. Istniejące formularze i style nie są kopiowane bez potrzeby; `scripts/quality.ps1`, build i testy interfejsu przechodzą.
