---
id: 014-monthly-income-api
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
type: ddd-construction-bolt
status: in-progress
stories:
  - 001-record-income
  - 002-select-dictionary-source
  - 003-record-amount-currency-date
  - 004-period-totals-by-currency
created: '2026-10-06T20:32:37Z'
started: '2026-10-07T11:31:16Z'
completed: null
current_stage: adr-analysis
stages_completed:
  - name: domain-model
    completed: '2026-10-07T11:31:16Z'
    artifact: ddd-01-domain-model.md
  - name: technical-design
    completed: '2026-10-07T11:55:46Z'
    artifact: ddd-02-technical-design.md
requires_bolts:
  - 013-periods-api
  - 010-family-income-api
enables_bolts:
  - 015-income-attachments-api
  - 016-periods-income-ui
requires_units:
  - 001-periods-api
  - 001-family-income-api
blocks: true
complexity:
  avg_complexity: 3
  avg_uncertainty: 2
  max_dependencies: 3
  testing_scope: 2
---

# Bolt: 014-monthly-income-api

## Overview

Wprowadzić zapis faktycznych przychodów ze słownikowym źródłem, odbiorcą, kwotą/walutą/datą oraz podsumowania per waluta.

## Objective

Spełnić FR-03, FR-04, FR-05 i FR-08 oraz wesprzeć egzekwowanie FR-07 przez CRUD przychodów i jego kontrakt współbieżności.

## Stories Included

- [ ] [001-record-income](../../intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/001-record-income.md): oddzielny wpis rzeczywistego przychodu — Must.
- [ ] [002-select-dictionary-source](../../intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/002-select-dictionary-source.md): źródło `IncomeSource` i szybkie dodanie — Must.
- [ ] [003-record-amount-currency-date](../../intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/003-record-amount-currency-date.md): kwota, waluta i data otrzymania — Must.
- [ ] [004-period-totals-by-currency](../../intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/004-period-totals-by-currency.md): sumy okresu i roku — Must.

## Bolt Type and Stages

**Type**: DDD Construction Bolt (`ddd-construction-bolt`).

- [x] 1. Domain Model → `ddd-01-domain-model.md`
- [x] 2. Technical Design → `ddd-02-technical-design.md`
- [ ] 3. ADR Analysis (optional) → `adr-*.md`
- [ ] 4. Implement → source code and migrations
- [ ] 5. Test → `ddd-03-test-report.md`

Each DDD stage requires its human checkpoint under the bolt type instructions.

## Dependencies

### Requires
- [013-periods-api](../013-periods-api/bolt.md) and its period state contract.
- [010-family-income-api](../010-family-income-api/bolt.md) and the existing household `IncomeSource`/`Contract` domain.

### Enables
- `015-income-attachments-api` attaches files to the parent income record.
- `016-periods-income-ui` consumes income/source/summary endpoints.

## Success Criteria

- [ ] Create/edit/delete writes are allowed only for authorized households and active periods. PostgreSQL tests force both close–write orders and prove that a mutation cannot commit after close based on a stale active-state read.
- [ ] Actual records remain distinct from contract gross/default amounts.
- [ ] Sources are validated dictionary entries; dates may be outside the accounting period.
- [ ] Month/year totals use exact amounts grouped by currency, without conversion.
- [ ] Validation, audit, tenant isolation, role, and concurrency tests pass.

## Notes

Before implementation, decide how source/recipient historical values are preserved if their dictionary data changes. Keep attachment storage and limits in bolt 015.
