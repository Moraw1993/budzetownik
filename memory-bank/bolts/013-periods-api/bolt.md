---
id: 013-periods-api
unit: 001-periods-api
intent: 003-budget-periods-and-income
type: ddd-construction-bolt
status: in-progress
stories:
  - 001-create-year-months
  - 002-activate-month
  - 003-close-and-reopen-month
created: '2026-10-06T20:32:37Z'
started: '2026-10-07T09:57:34Z'
completed: null
current_stage: domain-model
stages_completed: []
requires_bolts: []
enables_bolts:
  - 014-monthly-income-api
  - 016-periods-income-ui
requires_units:
  - 002-foundation-api
blocks: false
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 013-periods-api

## Overview

Wprowadzić API i model okresów rozliczeniowych z kompletnym rokiem, jawnymi niezależnymi stanami miesięcy i audytowanymi przejściami.

## Objective

Spełnić FR-01, FR-02 i FR-07 oraz historie w `001-periods-api`.

## Stories Included

- [ ] [001-create-year-months](../../intents/003-budget-periods-and-income/units/001-periods-api/stories/001-create-year-months.md): rok i 12 nieaktywnych miesięcy — Must.
- [ ] [002-activate-month](../../intents/003-budget-periods-and-income/units/001-periods-api/stories/002-activate-month.md): jawna, niezależna aktywacja — Must.
- [ ] [003-close-and-reopen-month](../../intents/003-budget-periods-and-income/units/001-periods-api/stories/003-close-and-reopen-month.md): zamknięcie i ponowne otwarcie — Must.

## Bolt Type and Stages

**Type**: DDD Construction Bolt (`ddd-construction-bolt`).

- [ ] 1. Domain Model → `ddd-01-domain-model.md`
- [ ] 2. Technical Design → `ddd-02-technical-design.md`
- [ ] 3. ADR Analysis (optional) → `adr-*.md`
- [ ] 4. Implement → source code and migrations
- [ ] 5. Test → `ddd-03-test-report.md`

Each DDD stage requires its human checkpoint under the bolt type instructions.

## Dependencies

### Requires
- Existing `002-foundation-api` for households, membership, roles, and audit.

### Enables
- `014-monthly-income-api` uses period states to guard writes.
- `016-periods-income-ui` consumes year/month endpoints.

## Success Criteria

- [ ] Exactly twelve unique months are created atomically, all inactive.
- [ ] Months activate independently and in any order; multiple may be active.
- [ ] Closed month writes are blocked until explicit reopening.
- [ ] Role, tenant isolation, concurrency, and audit checks pass.

## Notes

Resolve the state-transition model, year uniqueness, and locking behavior in design. No income records are created in this bolt.
