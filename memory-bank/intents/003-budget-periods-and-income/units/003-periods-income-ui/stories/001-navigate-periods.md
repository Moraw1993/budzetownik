---
id: 001-navigate-periods
unit: 003-periods-income-ui
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 016-periods-income-ui
implemented: false
requirements: [FR-01, FR-02]
---

# Story: 001-navigate-periods

## User Story

**As a** household user
**I want** to select a year and see its twelve months with clear states
**So that** I can navigate to the accounting period I need.

## Acceptance Criteria

- [ ] **Given** an available year, **when** I open it, **then** its twelve calendar months appear in order with visible inactive, active, or closed state.
- [ ] **Given** no year exists, **when** an authorized user creates one, **then** the UI confirms the result and shows all twelve months inactive.
- [ ] **Given** a reader role, **when** I view periods, **then** I can read available data without edit controls that imply write access.
- [ ] **Given** an API error or unavailable year, **when** I navigate, **then** the UI preserves context and presents a recoverable, accessible error state.

## Technical Notes

Follow the current light-background visual system, responsive layout, and existing household navigation conventions.

## Dependencies

### Requires
- 001-create-year-months in 001-periods-api.

### Enables
- 002-change-period-state.
- 001-period-role-lifecycle in acceptance.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Year list is empty | Explain the empty state and offer year creation only to an authorized editor. |
| Narrow viewport | Months remain readable and navigable without horizontal clipping. |

## Out of Scope

- Implementing period state rules in the client.
