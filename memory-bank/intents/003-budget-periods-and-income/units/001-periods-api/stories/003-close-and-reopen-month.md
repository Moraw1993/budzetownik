---
id: 003-close-and-reopen-month
unit: 001-periods-api
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 013-periods-api
implemented: false
requirements: [FR-07]
---

# Story: 003-close-and-reopen-month

## User Story

**As an** Owner or Administrator
**I want** to close a completed month and explicitly reopen it for changes
**So that** financial records are protected from accidental edits.

## Acceptance Criteria

- [ ] **Given** an active month, **when** I close it, **then** its status becomes closed and the change records actor, time, and audit event.
- [ ] **Given** a closed month, **when** I explicitly reopen it, **then** it returns to active and exposes the state for downstream income operations.
- [ ] **Given** an inactive month, **when** I request closure or reopening, **then** the API enforces the defined valid state transitions.
- [ ] **Given** any of the nine combinations of current state and lifecycle operation, **when** I issue the operation, **then** the API follows the published matrix for status, timestamps, and audit, including `reopen(active)` as a no-op.
- [ ] **Given** Member or Viewer access, **when** the user closes/reopens a month, **then** the API denies the operation.

## Technical Notes

This story owns period state and lifecycle. Bolt 014 owns enforcement of that state for create/edit/delete income and the PostgreSQL close–write race tests. Lifecycle transition responses and timestamp/audit behavior follow the [matrix in the technical design](../../../../../bolts/013-periods-api/ddd-02-technical-design.md#state-transitions-and-idempotency).

## Dependencies

### Requires
- 002-activate-month

### Enables
- All write stories in 002-monthly-income-api.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| An already closed month is closed again | State remains closed; response is deterministic and audit is not duplicated unnecessarily. |

## Out of Scope

- Reopening automatically after an attempted edit.
