---
id: 015-income-attachments-api
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
type: ddd-construction-bolt
status: in-progress
stories:
  - 005-private-income-attachments
created: '2026-10-06T20:32:37Z'
started: '2026-10-07T18:03:48Z'
completed: null
current_stage: implement
stages_completed:
  - domain-model
  - technical-design
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

- [ ] [005-private-income-attachments](../../intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/005-private-income-attachments.md): prywatne załączniki — Should.

## Bolt Type and Stages

**Type**: DDD Construction Bolt (`ddd-construction-bolt`).

- [ ] 1. Domain Model → `ddd-01-domain-model.md`
- [ ] 2. Technical Design → `ddd-02-technical-design.md`
- [ ] 3. ADR Analysis (optional) → `adr-*.md`
- [ ] 4. Implement → private storage/API
- [ ] 5. Test → `ddd-03-test-report.md`

Each DDD stage requires its human checkpoint under the bolt type instructions.

## Dependencies

### Requires
- [014-monthly-income-api](../014-monthly-income-api/bolt.md) for a stable income record.

### Enables
- `016-periods-income-ui` and `017-periods-income-acceptance`.

## Success Criteria

- [ ] Multiple supported files remain linked to the correct record and household.
- [ ] Limits, content validation, atomicity, retention, and storage policy are documented and implemented.
- [ ] Downloads require authorization; files cannot be fetched publicly or cross-tenant.
- [ ] Failure, orphan cleanup, size/type, role, and isolation tests pass.

## Notes

Attachment count and size limits are a Construction decision. Inspect available private storage and scanning controls; do not trust client MIME headers or expose storage URLs publicly.
