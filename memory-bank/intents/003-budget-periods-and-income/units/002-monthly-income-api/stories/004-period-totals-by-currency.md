---
id: 004-period-totals-by-currency
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 014-monthly-income-api
implemented: false
requirements: [FR-08]
---

# Story: 004-period-totals-by-currency

## User Story

**As a** household user
**I want** monthly and yearly actual-income totals grouped by currency
**So that** I can understand recorded receipts without misleading conversion.

## Acceptance Criteria

- [ ] **Given** saved actual incomes in a month, **when** I view the month summary, **then** it totals only those entries and groups each currency separately.
- [ ] **Given** saved actual incomes in a year, **when** I view the year summary, **then** it totals the year's entries by currency without including contract or suggested amounts.
- [ ] **Given** entries in more than one currency, **when** I view the summary, **then** no combined converted total is presented.
- [ ] **Given** a closed month, **when** I read its summary, **then** the saved totals remain available to authorized readers.
- [ ] **Given** another household's entries, **when** I request totals, **then** tenant isolation excludes and protects them.

## Technical Notes

Use exact decimal aggregation and project-standard authorization/filtering. Define behavior for inactive empty periods consistently (zero or no summary) during design.

## Dependencies

### Requires
- 001-record-income.
- 003-record-amount-currency-date.

### Enables
- 005-manage-attachments-and-totals in the UI unit.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Period contains no entries | Return the documented empty/zero representation. |
| Entries mix currencies with equal numeric amounts | Keep them in distinct currency buckets. |

## Out of Scope

- Currency conversion, forecasts, contract values, and budgets.
