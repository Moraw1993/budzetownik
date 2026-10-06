---
id: 002-income-journey-attachments
unit: 004-periods-income-acceptance
intent: 003-budget-periods-and-income
status: draft
priority: must
created: '2026-10-06T20:32:37Z'
assigned_bolt: 017-periods-income-acceptance
implemented: false
requirements: [FR-03, FR-04, FR-05, FR-06, FR-08]
---

# Story: 002-income-journey-attachments

## User Story

**As an** Owner or Administrator
**I want** to verify recording actual income with its source and evidence
**So that** the family can rely on complete, private, and correctly summarized records.

## Acceptance Criteria

- [ ] **Given** a person and household recipient, **when** I create multiple income entries with eligible dictionary sources, **then** each record keeps its recipient and source and the person view offers contracts active for the accounting period.
- [ ] **Given** a salary received on September 30, **when** I assign it to October, **then** the October total includes it with September 30 as the actual receipt date.
- [ ] **Given** entries in multiple currencies, **when** I view month and year summaries, **then** each currency is totaled separately without conversion or contract estimates.
- [ ] **Given** multiple PNG, JPG/JPEG, and PDF files, **when** I attach them to an entry, **then** they persist and can be downloaded by an authorized household user only.
- [ ] **Given** Member/Viewer, another household, or an unsupported/oversized file, **when** access or upload is attempted, **then** the correct authorization or validation failure is returned and no private file is exposed.
- [ ] **Given** a service restart, **when** I revisit the entry, **then** its amount, date, source relation, attachments, and summary contribution persist.

## Technical Notes

Use synthetic fixtures and documented Construction attachment limits. Keep the scenario deterministic and do not call external services.

## Dependencies

### Requires
- 001-period-role-lifecycle.
- 002-monthly-income-api and 003-periods-income-ui complete.

### Enables
- Acceptance of intent 003.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Source is later archived or its display name changes | Historical record remains traceable according to the approved Construction snapshot/version policy. |
| One file upload fails among several | Outcome matches the API's documented atomicity/partial-save contract without orphan files. |

## Out of Scope

- OCR extraction, exchange rates, expense records, or production deployment.
