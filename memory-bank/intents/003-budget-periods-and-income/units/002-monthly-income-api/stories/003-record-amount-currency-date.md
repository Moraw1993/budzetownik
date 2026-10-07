---
id: 003-record-amount-currency-date
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 014-monthly-income-api
implemented: false
requirements: [FR-05]
---

# Story: 003-record-amount-currency-date

## User Story

**As an** Owner or Administrator
**I want** to save the received amount, its currency, and actual receipt date
**So that** the income record describes what arrived, independently of the accounting month.

## Acceptance Criteria

- [ ] **Given** a valid income, **when** I save it, **then** its amount is stored at the project's supported decimal precision with an explicit currency.
- [ ] **Given** an accounting month, **when** an income was actually received on a date outside that month, **then** it can still be assigned to that month and its receipt date is preserved.
- [ ] **Given** a salary received on September 30 and assigned to October, **when** I read the October record, **then** it remains part of October's accounting total with September 30 as its receipt date.
- [ ] **Given** an invalid amount, currency, or receipt date, **when** I submit the record, **then** the API returns validation feedback and stores no partial entry.
- [ ] **Given** a successful record, **when** its amount is read, **then** it is not copied from contract gross pay or an income-source suggestion.

## Technical Notes

Reuse project decimal and currency conventions after inspection in Construction. Receipt date has a different semantic role from the associated accounting period.

## Dependencies

### Requires
- 001-record-income.

### Enables
- 004-period-totals-by-currency.
- 004-enter-income-details in the UI unit.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Receipt date is in a different calendar year | The accounting period remains explicitly selected; no implicit reassignment occurs. |
| Decimal value has unsupported precision | Validation rejects or applies only the existing explicit project rule; no silent rounding. |

## Out of Scope

- Foreign-exchange conversion or exchange-rate lookup.
