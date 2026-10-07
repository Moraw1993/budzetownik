---
id: 001-create-year-months
unit: 001-periods-api
intent: 003-budget-periods-and-income
status: complete
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 013-periods-api
implemented: true
requirements:
  - FR-01
---

# Story: 001-create-year-months

## User Story

**As an** Owner or Administrator
**I want** to create a household accounting year
**So that** I can manage its months as distinct periods.

## Acceptance Criteria

- [x] **Given** a year not yet present for my household, **when** I create it, **then** it contains exactly January through December once each and all twelve months are inactive.
- [x] **Given** that the year already exists, **when** I submit it again, **then** the API rejects the duplicate without creating extra months.
- [x] **Given** simultaneous requests to create the same household/year, **when** both complete, **then** there is exactly one year and twelve months.
- [x] **Given** another household's year, **when** I request it, **then** tenant isolation prevents disclosure or modification.

## Technical Notes

Define year uniqueness and atomic creation at the database/domain boundary. Validate year range in Construction against existing project conventions.

## Dependencies

### Requires
- Existing household and role model.

### Enables
- 002-activate-month
- 001-navigate-periods in the UI unit.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Year has already been partially persisted by a failed operation | Transaction rollback or safe repair leaves a complete consistent year. |
| Two requests race to create the same year | Uniqueness and transaction logic prevent duplicates. |

## Out of Scope

- Creating budgets, expenses, or income automatically.
