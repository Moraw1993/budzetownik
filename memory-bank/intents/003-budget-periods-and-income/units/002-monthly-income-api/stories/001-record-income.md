---
id: 001-record-income
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
status: complete
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 014-monthly-income-api
implemented: true
requirements:
  - FR-03
  - FR-07
---

# Story: 001-record-income

## User Story

**As an** Owner or Administrator
**I want** to record a distinct actual income in an active month for a family member or the household
**So that** the ledger reflects money actually received by the right recipient.

## Acceptance Criteria

- [x] **Given** an active month, **when** I submit a valid income for a member of that household or for the household itself, **then** the entry is stored against that household, month, and recipient.
- [x] **Given** multiple receipts for one member, household, or source, **when** I submit them separately, **then** each remains a distinct record and none overwrites another.
- [x] **Given** an inactive or closed month, **when** I create, edit, or delete an income, **then** the API rejects the mutation with a stable conflict response and leaves data and audit unchanged.
- [x] **Given** an income create/edit/delete races with closing its month, **when** both operations commit, **then** PostgreSQL serialization through `Household → AccountingYear` yields either the write committed before close or the write rejected after close; no write commits after close based on a stale active-state read.
- [x] **Given** Member or Viewer access, **when** the user creates, edits, or deletes an income, **then** the API denies the write.
- [x] **Given** a member, month, source, or period from another household, **when** I combine it with this household's entry, **then** the API rejects the mismatch.
- [x] **Given** a successful write, **when** it is committed, **then** the income and its required audit event are committed atomically.

## Technical Notes

Keep actual income distinct from `Contract.gross_amount` and any suggested/default source amount. Define edit/delete audit details consistently with current financial audit conventions.

## Dependencies

### Requires
- `001-periods-api` and 002-activate-month.
- Existing household members and `IncomeSource` data.

### Enables
- 002-select-dictionary-source
- 003-record-amount-currency-date
- 005-private-income-attachments

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Same amount/source/date is submitted twice | Both are preserved as separate income events unless an explicit idempotency key identifies a retry. |
| Member becomes inactive later | Historical income remains readable and is not reassigned implicitly. |
| Close races with create/edit/delete | The year lock determines one serial order; after close commits, a later mutation is rejected and produces no income or audit change. |

## Out of Scope

- Automatic creation from a contract or bank feed.
- Budgets, expenses, and net-pay calculation.
