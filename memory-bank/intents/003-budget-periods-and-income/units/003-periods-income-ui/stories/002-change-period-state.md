---
id: 002-change-period-state
unit: 003-periods-income-ui
intent: 003-budget-periods-and-income
status: complete
priority: must
created: "2026-10-06T20:32:37Z"
assigned_bolt: 016-periods-income-ui
implemented: true
requirements:
  - FR-02
  - FR-07
---

# Story: 002-change-period-state

## User Story

**As an** Owner or Administrator
**I want** explicit controls to activate, close, and reopen a month
**So that** its lifecycle is intentional and visible.

## Acceptance Criteria

- [ ] **Given** an inactive month, **when** I have write permission, **then** I can explicitly activate it and see the updated state.
- [ ] **Given** an active month, **when** I choose close, **then** the UI communicates the action and shows the closed state after success.
- [ ] **Given** a closed month, **when** I choose reopen, **then** the UI shows it active after success and permits income editing.
- [ ] **Given** a Member or Viewer, **when** I inspect a period, **then** state-change controls are not offered and the API remains authoritative.
- [ ] **Given** a failed state transition, **when** the request returns an error, **then** the displayed state remains consistent with the server and the error is accessible.

## Technical Notes

Use distinct actions for activate, close, and reopen. Confirm destructive/locking transitions according to the accepted visual design; never infer a transition from navigation.

## Dependencies

### Requires

- 001-navigate-periods.
- 002-activate-month and 003-close-and-reopen-month in 001-periods-api.

### Enables

- 003-add-income-recipient-source.

## Edge Cases

| Scenario                                     | Expected Behavior                                                                   |
| -------------------------------------------- | ----------------------------------------------------------------------------------- |
| Another user changes the period concurrently | Refresh or error state reflects server state rather than a stale optimistic status. |
| User has a read-only role                    | No control exposes a write action.                                                  |

## Out of Scope

- Client-side authorization as a substitute for API checks.
