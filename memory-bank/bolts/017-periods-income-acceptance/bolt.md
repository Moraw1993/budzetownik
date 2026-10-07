---
id: 017-periods-income-acceptance
unit: 004-periods-income-acceptance
intent: 003-budget-periods-and-income
type: simple-construction-bolt
status: planned
stories:
  - 001-period-role-lifecycle
  - 002-income-journey-attachments
created: '2026-10-06T20:32:37Z'
started: null
completed: null
current_stage: null
stages_completed: []
requires_bolts:
  - 013-periods-api
  - 014-monthly-income-api
  - 015-income-attachments-api
  - 016-periods-income-ui
enables_bolts: []
requires_units:
  - 001-periods-api
  - 002-monthly-income-api
  - 003-periods-income-ui
blocks: true
complexity:
  avg_complexity: 2
  avg_uncertainty: 2
  max_dependencies: 3
  testing_scope: 3
---

# Bolt: 017-periods-income-acceptance

## Overview

Potwierdzić zintegrowany przebieg od utworzenia roku po zapis, podsumowanie i prywatny odczyt przychodów.

## Objective

Sprawdzić na danych syntetycznych role, izolację, niezależne stany miesięcy, źródła, daty, waluty, załączniki i trwałość.

## Stories Included

- [ ] [001-period-role-lifecycle](../../intents/003-budget-periods-and-income/units/004-periods-income-acceptance/stories/001-period-role-lifecycle.md): cykl życia okresów i ról — Must.
- [ ] [002-income-journey-attachments](../../intents/003-budget-periods-and-income/units/004-periods-income-acceptance/stories/002-income-journey-attachments.md): przepływ przychodu i załączników — Must.

## Bolt Type and Stages

**Type**: Simple Construction Bolt (`simple-construction-bolt`).

- [ ] 1. Plan → `implementation-plan.md`
- [ ] 2. Implement → isolated synthetic-data harness and `implementation-walkthrough.md`
- [ ] 3. Test → full acceptance report in `test-walkthrough.md`

## Dependencies

### Requires
- Bolts [013-periods-api](../013-periods-api/bolt.md), [014-monthly-income-api](../014-monthly-income-api/bolt.md), [015-income-attachments-api](../015-income-attachments-api/bolt.md), and [016-periods-income-ui](../016-periods-income-ui/bolt.md).

### Enables
- Acceptance review for intent 003; release/deployment remains a separate authorized Operations action.

## Success Criteria

- [ ] Both stories pass on a clean runtime with synthetic records.
- [ ] Owner/Admin write and Member/Viewer read-only behavior is checked at UI and API layers.
- [ ] Cross-household access, inactive/closed period writes, attachment privacy, totals, and restart persistence pass.
- [ ] P95 for period lifecycle and income/summary endpoints is measured against the <500 ms target with documented fixtures, warm-up, sample count, concurrency, percentile method, and environment; if not measured, intent acceptance remains incomplete.
- [ ] Results, limits, and any unverified behavior are documented without using production financial data.

## Notes

Do not run release or production deployment as part of this acceptance bolt.
