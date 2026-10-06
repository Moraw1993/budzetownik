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
- [ ] **Given** a closed month, **when** a user adds, edits, or deletes an income, **then** the API rejects the write, including requests racing with closure.
- [ ] **Given** a closed month, **when** I explicitly reopen it, **then** it returns to active and income changes are allowed again.
- [ ] **Given** an inactive month, **when** I request closure or reopening, **then** the API enforces the defined valid state transitions and does not permit income writes.
- [ ] **Given** Member or Viewer access, **when** the user closes/reopens a month, **then** the API denies the operation.

## Technical Notes

The authoritative lock must be checked in the same consistency boundary as income writes. Construction defines whether closure is blocked by in-flight writes and how duplicate transition requests are handled.

## Dependencies

### Requires
- 002-activate-month

### Enables
- All write stories in 002-monthly-income-api.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| A write races with close | The result is consistent with a single serialized state transition; no untracked write is accepted after closure. |
| An already closed month is closed again | State remains closed; response is deterministic and audit is not duplicated unnecessarily. |

## Out of Scope

- Reopening automatically after an attempted edit.
