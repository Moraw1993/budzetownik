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
| Requirements | Draft; checkpoint 2 pending | requirements.md |
| System Context | Pending | system-context.md |
| Units | Pending | units.md and units/*/unit-brief.md |
| Stories | Pending | units/*/stories/*.md |
| Bolt Plan | Pending | memory-bank/bolts/*/bolt.md |

## Summary

| Metric | Count |
| --- | --- |
| Functional Requirements | 8 draft |
| Non-Functional Requirements | 3 draft groups |
| Units | Pending approval |
| Stories | Pending approval |
| Bolts Planned | Pending approval |

## Units Breakdown

To be determined after requirements approval.

## Decision Log

| Date | Decision | Rationale | Approved |
| --- | --- | --- | --- |
| 2026-10-06 | A year contains exactly 12 calendar months; each month starts inactive and must be explicitly activated. | User checkpoint 1 response. | User input; requirements review pending |
| 2026-10-06 | Intent covers periods and actual income only; each month can be explicitly reopened before edits after closure. | User checkpoint 1 response. | User input; requirements review pending |
| 2026-10-06 | Income records identify a person or household, support multiple income items, and include amount, currency, receipt date and attachment. | User checkpoint 1 response. | User input; requirements review pending |
| 2026-10-06 | Multiple months may be active at once and in any order; the received date can differ from the accounting month; income sources must be dictionary entries, with quick-add to the dictionary; each income may have multiple PNG/JPG/PDF attachments. | User checkpoint 1 follow-up. | User input; requirements review pending |
| 2026-10-06 | Recommend preserving existing access roles: Owner/Administrator edit, Member/Viewer read-only. | Keeps financial writes consistent with established household access policy. | Pending user confirmation at Checkpoint 2 |

## Scope Changes

| Date | Change | Reason | Impact |
| --- | --- | --- | --- |
| 2026-10-06 | Started new intent after completion of family-income management intent and refined requirements from user answers. | User invoked Inception for the next planned feature. | Requirements and design artifacts only; no application code. |

## Ready for Construction

**Checklist**:
- [ ] All requirements documented and approved
- [ ] System context defined
- [ ] Units decomposed
- [ ] Stories created for all units
- [ ] Bolts planned
- [ ] Human review complete

## Next Steps

1. Resolve open questions and approve requirements at Checkpoint 2.
2. Generate context, units, stories and bolt plan.
3. Review all artifacts at Checkpoint 3 before Construction.

## Dependencies

The intent extends existing household membership, roles, income sources and contracts. Construction dependencies and execution order remain to be defined after requirements approval.
