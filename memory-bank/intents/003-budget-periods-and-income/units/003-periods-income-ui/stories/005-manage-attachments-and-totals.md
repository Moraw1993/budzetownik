---
id: 005-manage-attachments-and-totals
unit: 003-periods-income-ui
intent: 003-budget-periods-and-income
status: draft
priority: should
created: '2026-10-06T20:32:37Z'
assigned_bolt: 016-periods-income-ui
implemented: false
requirements: [FR-06, FR-08]
---

# Story: 005-manage-attachments-and-totals

## User Story

**As a** household user
**I want** to see per-currency income totals and manage receipt attachments
**So that** I can review recorded income and its supporting documents.

## Acceptance Criteria

- [ ] **Given** income entries in an accounting month/year, **when** I view its summary, **then** actual totals appear separately for each currency.
- [ ] **Given** an income form, **when** I attach files, **then** I can select multiple PNG, JPG/JPEG, and PDF files and see which were accepted.
- [ ] **Given** an unsupported or over-limit file, **when** I upload it, **then** the UI shows the server validation and does not imply that it was saved.
- [ ] **Given** an authorized household user, **when** they open a listed attachment, **then** the app uses the authenticated download flow and identifies its associated income.
- [ ] **Given** a closed month, **when** I review income, **then** totals and allowed read-only attachment access remain visible while edits stay unavailable.

## Technical Notes

Follow the accepted design system and accessible labels for file controls, summary groups, and download actions. API provides totals and authorization.

## Dependencies

### Requires
- 004-enter-income-details.
- 004-period-totals-by-currency and 005-private-income-attachments in 002-monthly-income-api.

### Enables
- 002-income-journey-attachments in 004-periods-income-acceptance.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| No income exists | Show a clear empty state and per-currency totals as defined by the API. |
| Attachment download expires or is denied | Show a recoverable access error without exposing a public URL. |

## Out of Scope

- Currency conversion, OCR, or file preview behavior beyond supported browser-native viewing.
