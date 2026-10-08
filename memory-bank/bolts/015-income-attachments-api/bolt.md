---
id: 015-income-attachments-api
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
type: ddd-construction-bolt
status: complete
stories:
  - 005-private-income-attachments
created: "2026-10-06T20:32:37Z"
started: "2026-10-07T18:03:48Z"
completed: "2026-10-08T20:18:26Z"
current_stage: null
stages_completed:
  - name: domain-model
    completed: "2026-10-07T20:13:37Z"
    artifact: ddd-01-domain-model.md
  - name: technical-design
    completed: "2026-10-07T20:34:47Z"
    artifact: ddd-02-technical-design.md
  - name: implement
    completed: "2026-10-07T21:09:27Z"
    artifact: private attachment models, storage, upload, reconciliation and API
  - name: adr-analysis
    completed: "2026-10-08T20:13:54Z"
    artifact: adr-009-proxy-upload-deadlines.md
  - name: test
    completed: "2026-10-08T20:13:54Z"
    artifact: ddd-03-test-report.md
requires_bolts:
  - 014-monthly-income-api
enables_bolts:
  - 016-periods-income-ui
  - 017-periods-income-acceptance
requires_units: []
blocks: true
complexity:
  avg_complexity: 3
  avg_uncertainty: 3
  max_dependencies: 3
  testing_scope: 3
---

# Bolt: 015-income-attachments-api

## Overview

Zapewnić prywatne, wielokrotne załączniki potwierdzające przychód oraz autoryzowany upload i odczyt.

## Objective

Spełnić FR-06 dla PNG, JPG/JPEG i PDF oraz kryteria story 005 jednostki 002-monthly-income-api.

## Stories Included

- [x] [005-private-income-attachments](../../intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/005-private-income-attachments.md): prywatne załączniki — Should.

## Bolt Type and Stages

**Type**: DDD Construction Bolt (`ddd-construction-bolt`).

- [x] 1. Domain Model → `ddd-01-domain-model.md`
- [x] 2. Technical Design → `ddd-02-technical-design.md`
- [x] 3. ADR Analysis → ADR-009 identified during Stage 5 and accepted.
- [x] 4. Implement → private storage/API
- [x] 5. Test → `ddd-03-test-report.md`

Each DDD stage requires its human checkpoint under the bolt type instructions.

## Dependencies

### Requires
- [014-monthly-income-api](../014-monthly-income-api/bolt.md) for a stable income record.

### Enables
- `016-periods-income-ui` and `017-periods-income-acceptance`.

## Success Criteria

- [x] Multiple supported files remain linked to the correct record and household.
- [x] Limits, content validation, atomicity, retention, and storage policy are documented and implemented.
- [x] Downloads require authorization; files cannot be fetched publicly or cross-tenant.
- [x] Failure, orphan cleanup, size/type, role, and isolation tests pass.

## Notes

Attachment count and size limits are a Construction decision. Inspect available private storage and scanning controls; do not trust client MIME headers or expose storage URLs publicly.

Independent Stage 5 review of 2a4dda2: 8.9/10 ACCEPTED / PASS at 2026-10-08T20:13:54Z. Official completion at 2026-10-08T20:18:26Z under the user's prior authorization. Bolt 016 is not started by this checkpoint.
