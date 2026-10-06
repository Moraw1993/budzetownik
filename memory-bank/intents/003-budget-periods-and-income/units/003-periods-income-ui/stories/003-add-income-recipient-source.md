---
id: 003-add-income-recipient-source
unit: 003-periods-income-ui
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 016-periods-income-ui
implemented: false
requirements: [FR-03, FR-04]
---

# Story: 003-add-income-recipient-source

## User Story

**As an** Owner or Administrator
**I want** to choose the income recipient and a dictionary source in the income form
**So that** each record is attached to the right person or household and a reusable source.

## Acceptance Criteria

- [ ] **Given** an active month, **when** I start an income entry, **then** I can choose a household member or the household as recipient.
- [ ] **Given** I select a person, **when** source options load, **then** the form shows their contracts active in the selected period and their eligible other sources.
- [ ] **Given** I select the household, **when** source options load, **then** the form shows eligible household-level dictionary entries.
- [ ] **Given** no suitable source exists, **when** I use quick-add, **then** I complete the validated source form and the new dictionary entry becomes selectable.
- [ ] **Given** any recipient, **when** I submit without a dictionary source or type a source name freely, **then** the UI/API does not save the income.
- [ ] **Given** a closed or inactive month, **when** I open its income view, **then** the form is unavailable and the state is explained.

## Technical Notes

Quick-add must reuse the existing income-source creation contract and the source type's fields. The form must not create a monthly income merely by saving a source.

## Dependencies

### Requires
- 002-change-period-state.
- 002-select-dictionary-source in 002-monthly-income-api.
- Existing 002-family-management-ui source forms.

### Enables
- 004-enter-income-details.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| No active contracts exist for the selected period | Show other eligible dictionary sources and quick-add; do not invent a contract. |
| Quick-added source fails validation | Preserve the income form context and explain field errors. |

## Out of Scope

- Free-text source names and automatic income creation from a contract.
