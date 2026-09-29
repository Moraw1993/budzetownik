---
id: 010-family-income-api
unit: 001-family-income-api
intent: 002-family-income-management
type: ddd-construction-bolt
status: complete
stories:
  - 001-company-dictionary
  - 002-contract-sources
  - 003-other-sources
  - 004-legacy-source-migration
created: '2026-09-23T08:28:54Z'
started: '2026-09-23T21:12:14Z'
completed: '2026-09-26T19:41:23Z'
current_stage: null
stages_completed:
  - name: model
    completed: '2026-09-23T21:17:26Z'
    artifact: ddd-01-domain-model.md
  - name: design
    completed: '2026-09-23T21:21:31Z'
    artifact: ddd-02-technical-design.md
  - name: adr
    completed: '2026-09-23T21:30:14Z'
    artifact: adr-005-shared-income-source-identity.md
  - name: implement
    completed: '2026-09-26T19:23:40Z'
    artifact: backend/households/
  - name: test
    completed: '2026-09-26T19:40:55Z'
    artifact: ddd-03-test-report.md
requires_bolts:
  - 008-local-acceptance
enables_bolts:
  - 011-family-management-ui
requires_units:
  - 001-local-runtime
  - 002-foundation-api
blocks: true
complexity:
  avg_complexity: 3
  avg_uncertainty: 2
  max_dependencies: 2
  testing_scope: 2
---

# Model i API firm, umów oraz źródeł dochodu

## Cel

Zbudować wspólną tożsamość źródła dochodu z osobnymi szczegółami umowy, słownikiem firm i bezpieczną migracją istniejących rekordów. Rozdzielić kwotę brutto umowy od opcjonalnej miesięcznej podpowiedzi przy innym źródle.

## Stories

- [x] [001-company-dictionary](../../intents/002-family-income-management/units/001-family-income-api/stories/001-company-dictionary.md): Firma w słowniku gospodarstwa.
- [x] [002-contract-sources](../../intents/002-family-income-management/units/001-family-income-api/stories/002-contract-sources.md): Umowa jako źródło członka.
- [x] [003-other-sources](../../intents/002-family-income-management/units/001-family-income-api/stories/003-other-sources.md): Inne źródła osoby i gospodarstwa.
- [x] [004-legacy-source-migration](../../intents/002-family-income-management/units/001-family-income-api/stories/004-legacy-source-migration.md): Migracja i jawna konwersja.

## Etapy DDD

- [x] Model domeny: encje, niezmienniki, granica źródła i plan migracji.
- [x] Projekt techniczny: schemat i kontrakty API, transakcje, audyt i zgodność starego endpointu.
- [x] Implementacja: migracja, serwisy, serializatory, widoki i testy.
- [x] Testy: role, izolacja, współbieżność, migracja ze starego schematu i kontrola jakości.

## Wyniki

Modele `Company` i `Contract`, ewolucja `IncomeSource`, migracja Django, API i raport testowy. Testy na danych syntetycznych wykazują, że stare źródła nie stają się umowami ani przychodami miesięcznymi.

## Zależności

Rozpocząć po zamknięciu [008-local-acceptance](../008-local-acceptance/bolt.md), aby najpierw odebrać dotychczasowy fundament. Po zakończeniu bolt udostępnia API dla 011-family-management-ui.

## Warunki zakończenia

Wszystkie kryteria czterech stories i weryfikacja migracji przechodzą; audyt i istniejące identyfikatory pozostają spójne. `scripts/quality.ps1` i odpowiednie testy nie wykazują regresji.
