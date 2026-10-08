---
id: 005-private-income-attachments
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
status: complete
priority: should
created: "2026-10-06T20:32:37Z"
assigned_bolt: 015-income-attachments-api
implemented: true
requirements:
  - FR-06
---

# Story: 005-private-income-attachments

## User Story

**As an** Owner or Administrator
**I want** to attach multiple supporting files to one income entry
**So that** evidence for that receipt stays with its record.

## Acceptance Criteria

- [x] **Given** an income entry, **when** I attach multiple PNG, JPG/JPEG, or PDF files, **then** every accepted file remains associated with that entry and household.
- [x] **Given** a file with an unsupported type or a file exceeding the designed limits, **when** I upload it, **then** the API rejects it safely and communicates the validation error.
- [x] **Given** a user authorized for the income, **when** they request its attachment, **then** the app serves the file only after authorization.
- [x] **Given** a different household or unauthorized role, **when** they request the file by URL or identifier, **then** access is denied and the file is not publicly reachable.
- [x] **Given** one upload fails in a multi-file submission, **when** the operation completes, **then** the documented all-or-partial save behavior is consistent and no orphaned file is left behind.

## Technical Notes

Bolt 015 establishes number/size limits, MIME/signature validation, storage policy, upload atomicity, deletion/retention behavior, and malware-scanning expectations using current application infrastructure. Treat client MIME type as untrusted.

## Dependencies

### Requires
- 001-record-income.
- 014-monthly-income-api for the parent income resource.

### Enables
- 005-manage-attachments-and-totals in the UI unit.
- 002-income-journey-attachments in acceptance.

## Edge Cases

| Scenario | Expected Behavior |
| --- | --- |
| Filename contains path separators or unusual Unicode | Stored name is safely normalized; user-visible name is escaped. |
| Income is deleted or attachment removed | Retention and cleanup follow the designed ownership policy; no public orphan remains. |

## Out of Scope

- OCR, parsing documents, or sending files to an external provider.
