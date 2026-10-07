---
id: 002-select-dictionary-source
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 014-monthly-income-api
implemented: false
requirements: [FR-04]
---

# Story: 002-select-dictionary-source

## User Story

**As an** Owner or Administrator
**I want** to select or quickly add an income source in the dictionary
**So that** all saved income records use validated, reusable source data.

## Acceptance Criteria

- [ ] **Given** a person recipient and selected accounting month, **when** I request available sources, **then** I can choose that person's contracts active during the period and their other eligible sources.
- [ ] **Given** a household recipient, **when** I request available sources, **then** I can choose eligible household-level sources.
- [ ] **Given** a source owned by another person or household, **when** I try to use it for this recipient, **then** the API rejects it.
- [ ] **Given** a new source is needed, **when** I use quick-add, **then** it creates a regular `IncomeSource` dictionary record with type-specific validation before the income references it.
- [ ] **Given** an arbitrary string not represented by an `IncomeSource`, **when** I submit it as the income source, **then** the API rejects it.
- [ ] **Given** a saved income, **when** it is read later, **then** its source relationship remains available and is not inferred only from a mutable display name.

## Technical Notes

Construction must verify actual `IncomeSource`/`Contract` fields and define the date overlap rule for a contract active during a month (contract start on or before period end, and no end or end on/after period start). Preserve source identity. The historical snapshot/version strategy remains an explicit open design question.

## Dependencies

### Requires
- 001-record-income.
- Existing 001-family-income-api (`IncomeSource` and `Contract`).

### Enables
- 003-add-income-recipient-source in the UI unit.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Contract starts or ends on a month boundary | Period-overlap rule includes/excludes it consistently and is covered by tests. |
| A source is archived after use | Existing record remains readable; new use follows the dictionary's active/archive policy. |

## Out of Scope

- Unvalidated free-text source names.
- Redesign of the existing income-source dictionary.
