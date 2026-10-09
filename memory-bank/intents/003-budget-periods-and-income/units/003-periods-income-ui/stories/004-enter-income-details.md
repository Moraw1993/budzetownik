---
id: 004-enter-income-details
unit: 003-periods-income-ui
intent: 003-budget-periods-and-income
status: complete
priority: must
created: "2026-10-06T20:32:37Z"
assigned_bolt: 016-periods-income-ui
implemented: true
requirements:
  - FR-03
  - FR-05
---

# Story: 004-enter-income-details

## User Story

**As an** Owner or Administrator
**I want** to enter the actual amount, currency, and receipt date
**So that** the record reflects money received rather than a contract estimate.

## Acceptance Criteria

- [ ] **Given** a selected recipient and source, **when** I complete a valid form, **then** I can save an actual decimal amount, currency, and receipt date.
- [ ] **Given** a receipt date before or after the accounting month, **when** I save it, **then** the selected accounting month stays unchanged and the receipt date is preserved.
- [ ] **Given** contract gross pay or a source suggestion, **when** I open a new income form, **then** it is not silently copied as the actual received amount.
- [ ] **Given** a validation error, **when** saving fails, **then** field-level feedback is accessible and entered values remain available for correction.
- [ ] **Given** a read-only role or a closed/inactive month, **when** I try to save, **then** the form does not claim success and reflects the API response.

## Technical Notes

Reuse project form, money, date, and API error patterns. Do not convert currencies in the client.

## Dependencies

### Requires

- 003-add-income-recipient-source.
- 003-record-amount-currency-date in 002-monthly-income-api.

### Enables

- 005-manage-attachments-and-totals.

## Edge Cases

| Scenario                                  | Expected Behavior                                                                                 |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Receipt date is outside the selected year | Keep the explicitly selected period and show the actual receipt date without silent reassignment. |
| Save request fails                        | Keep the form data and allow retry after presenting the error.                                    |

## Out of Scope

- Net-pay calculation, bank import, or automatic date-based month selection.
