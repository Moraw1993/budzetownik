---
id: 001-period-role-lifecycle
unit: 004-periods-income-acceptance
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 017-periods-income-acceptance
implemented: false
requirements: [FR-01, FR-02, FR-07]
---

# Story: 001-period-role-lifecycle

## User Story

**As a** household owner
**I want** to verify the complete period lifecycle and role boundaries
**So that** inactive and closed months cannot accept accidental or unauthorized changes.

## Acceptance Criteria

- [ ] **Given** an Owner, **when** they create a year, activate months out of sequence, and close/reopen one, **then** twelve unique months and the expected independent states are visible.
- [ ] **Given** a Member or Viewer, **when** they read the same periods, **then** they can read but cannot create a year or change month states.
- [ ] **Given** an inactive or closed month, **when** an authorized user attempts an income write, **then** the request is rejected; after explicit activation/reopening it can proceed.
- [ ] **Given** another household, **when** any role attempts to query or change its year/month, **then** isolation prevents disclosure and mutation.
- [ ] **Given** an application restart after creating and changing period states, **when** the household returns, **then** persisted periods and states remain intact.

## Technical Notes

Use synthetic household accounts and test state transitions via both UI and API. Verify backend denial even when requests bypass the UI.

## Dependencies

### Requires
- 001-periods-api and 003-periods-income-ui complete.

### Enables
- 002-income-journey-attachments.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| A second household has a year with the same calendar year | Records remain isolated and independently addressable. |
| Two months are activated in reverse order | Both can be active at once. |

## Out of Scope

- Production user data or release/deployment operations.
