---
id: 016-periods-income-ui
unit: 003-periods-income-ui
intent: 003-budget-periods-and-income
type: simple-construction-bolt
status: in-progress
stories:
  - 001-navigate-periods
  - 002-change-period-state
  - 003-add-income-recipient-source
  - 004-enter-income-details
  - 005-manage-attachments-and-totals
created: "2026-10-06T20:32:37Z"
started: "2026-10-09T05:36:59Z"
completed: null
current_stage: implement
stages_completed:
  - name: plan
    completed: "2026-10-09T06:21:19Z"
    artifact: implementation-plan.md
requires_bolts:
  - 013-periods-api
  - 014-monthly-income-api
  - 015-income-attachments-api
  - 011-family-management-ui
enables_bolts:
  - 017-periods-income-acceptance
requires_units:
  - 001-periods-api
  - 002-monthly-income-api
  - 002-family-management-ui
blocks: true
complexity:
  avg_complexity: 2
  avg_uncertainty: 2
  max_dependencies: 3
  testing_scope: 3
---

# Bolt: 016-periods-income-ui

## Overview

Udostępnić jasny interfejs lat i miesięcy, formularz rzeczywistego przychodu, szybki wybór/dodanie źródła, pliki oraz podsumowania per waluta.

## Objective

Zrealizować FR-01–FR-08 po stronie widocznych przepływów i spełnić pięć stories UI.

## Stories Included

- [ ] [001-navigate-periods](../../intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/001-navigate-periods.md): lista lat i miesięcy — Must.
- [ ] [002-change-period-state](../../intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/002-change-period-state.md): jawne akcje stanu — Must.
- [ ] [003-add-income-recipient-source](../../intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/003-add-income-recipient-source.md): odbiorca i źródło — Must.
- [ ] [004-enter-income-details](../../intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/004-enter-income-details.md): kwota, waluta i data — Must.
- [ ] [005-manage-attachments-and-totals](../../intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/005-manage-attachments-and-totals.md): załączniki i sumy — Should.

## Bolt Type and Stages

**Type**: Simple Construction Bolt (`simple-construction-bolt`).

- [ ] 1. Plan → `implementation-plan.md`
- [ ] 2. Implement → source code and `implementation-walkthrough.md`
- [ ] 3. Test → tests and `test-walkthrough.md`

## Dependencies

### Requires

- [013-periods-api](../013-periods-api/bolt.md), [014-monthly-income-api](../014-monthly-income-api/bolt.md), and [015-income-attachments-api](../015-income-attachments-api/bolt.md).
- [011-family-management-ui](../011-family-management-ui/bolt.md) for the current source-management flows.

### Enables

- `017-periods-income-acceptance`.

## Success Criteria

- [ ] All five stories work with the server as the source of truth for access and validation.
- [ ] Responsive states, forms, validation, summaries, and authenticated file access pass UI and API checks.
- [ ] No typed source-name path is offered; actual income is distinct from a source suggestion.

## Notes

**Mandatory UI gate before implementation:** plan → visualization → independent-agent review with score **greater than 7.5/10** → explicit user acceptance. Record evidence under `memory-bank/standards/ui-design-review.md`; inception approval alone does not satisfy this gate. Preserve the application's light background and current visual language.

Plan checkpoint prepared at 2026-10-09T06:07:09Z: implementation-plan.md and evidence/ui-design/sidebar-v3. Independent reviewer /root/review_ui016 accepted each view at 8.4–8.5/10 and all auxiliary panels above 7.5. The user's earlier PNG canvases were exploratory; the existing sidebar/topbar is preserved. Source hashes and 27 real CUA captures are recorded in review.md. Human acceptance of sidebar-v3 is pending; current_stage remains plan and production implementation has not started.

User approved sidebar-v3 and requested implementation at 2026-10-09T06:21:19Z. Plan gate passed; production implementation begins. Prototype-only navigation is excluded.
