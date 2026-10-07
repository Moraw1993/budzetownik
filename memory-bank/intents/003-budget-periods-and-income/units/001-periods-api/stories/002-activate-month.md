---
id: 002-activate-month
unit: 001-periods-api
intent: 003-budget-periods-and-income
status: complete
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 013-periods-api
implemented: true
requirements:
  - FR-02
---

# Story: 002-activate-month

## User Story

**As an** Owner or Administrator
**I want** to explicitly activate any inactive month
**So that** income entry begins only when I choose to manage that month.

## Acceptance Criteria

- [x] **Given** a newly created year, **when** I view its months, **then** all twelve are inactive and none accepts income.
- [x] **Given** an inactive month, **when** I explicitly activate it, **then** it becomes active and can accept income entries.
- [x] **Given** other months are active or inactive, **when** I activate any inactive month in any order, **then** its state changes independently and already active months remain active.
- [x] **Given** Member or Viewer access, **when** the user requests activation, **then** the API denies the state change.
- [x] **Given** a month from another household, **when** I try to activate it, **then** the operation is denied without leaking tenant data.

## Technical Notes

Persist and audit the explicit state transition. Resolve the allowed transition matrix and concurrency behavior in the domain design.

## Dependencies

### Requires
- 001-create-year-months

### Enables
- 003-close-and-reopen-month
- 001-record-income in 002-monthly-income-api.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Activation is submitted twice | The API returns a deterministic result and does not duplicate audit or state records. |
| Two different months are activated concurrently | Both may become active. |

## Out of Scope

- Automatically activating a month when its year is created or when another month is activated.
