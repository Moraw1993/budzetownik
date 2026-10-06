---
intent: 003-budget-periods-and-income
created: '2026-10-06T20:09:33Z'
completed: null
status: in-progress
---

# Inception Log: Okresy rozliczeniowe i rzeczywiste przychody

## Overview

**Intent**: Dodać lata/miesiące rozliczeniowe i ewidencję rzeczywistych przychodów w miesiącu.
**Type**: brown-field
**Created**: 2026-10-06T20:09:33Z

## Artifacts Created

| Artifact | Status | File |
| --- | --- | --- |
| Requirements | Checkpoint 2 approved; draft for checkpoint 3 | requirements.md |
| System Context | Defined | system-context.md |
| Units | Generated; awaiting checkpoint 3 review | units.md and units/*/unit-brief.md |
| Stories | 15 generated; awaiting checkpoint 3 review | units/*/stories/*.md |
| Bolt Plan | 5 planned; awaiting checkpoint 3 review | memory-bank/bolts/013–017/bolt.md |

## Summary

| Metric | Count |
| --- | --- |
| Functional Requirements | 8 draft |
| Non-Functional Requirements | 2 draft groups |
| Units | 4 |
| Stories | 15 draft |
| Bolts Planned | 5 |

## Units Breakdown

Four units: periods API (3 stories), monthly-income API (5), periods-and-income UI (5), and acceptance (2). Backend units own business rules; UI implements their user-facing flows; acceptance validates the integrated journey.

## Decision Log

| Date | Decision | Rationale | Approved |
| --- | --- | --- | --- |
| 2026-10-06 | A year contains exactly 12 calendar months; each month starts inactive and must be explicitly activated. | User checkpoint 1 response. | Confirmed by user at Checkpoint 2 |
| 2026-10-06 | Intent covers periods and actual income only; each month can be explicitly reopened before edits after closure. | User checkpoint 1 response. | Confirmed by user at Checkpoint 2 |
| 2026-10-06 | Income records identify a person or household, support multiple income items, and include amount, currency, receipt date and attachment. | User checkpoint 1 response. | Confirmed by user at Checkpoint 2 |
| 2026-10-06 | Multiple months may be active at once and in any order; the received date can differ from the accounting month; income sources must be dictionary entries, with quick-add to the dictionary; each income may have multiple PNG/JPG/PDF attachments. | User checkpoint 1 follow-up. | Confirmed by user at Checkpoint 2 |
| 2026-10-06 | Preserve existing access roles: Owner/Administrator edit, Member/Viewer read-only. | Keeps financial writes consistent with established household access policy. | Confirmed by user at Checkpoint 2 |

## Scope Changes

| Date | Change | Reason | Impact |
| --- | --- | --- | --- |
| 2026-10-06 | Started new intent after completion of family-income management intent and refined requirements from user answers. | User invoked Inception for the next planned feature. | Requirements and design artifacts only; no application code. |

## Ready for Construction

**Checklist**:
- [x] All requirements documented and approved at Checkpoint 2
- [x] System context defined
- [x] Units decomposed
- [x] Stories created for all units
- [x] Bolts planned
- [ ] Human review complete

## Next Steps

1. Review requirements, context, units, stories, and bolt sequence at Checkpoint 3.
2. After Checkpoint 3 approval, perform the separate Checkpoint 4 readiness confirmation before Construction.

## Dependencies

The intent extends existing household membership, roles, income sources and contracts. Execution order: 013 periods API → 014 monthly-income API → 015 attachment API → 016 UI → 017 acceptance. The existing family-income API and family-management UI are prerequisites where their contracts are reused.
