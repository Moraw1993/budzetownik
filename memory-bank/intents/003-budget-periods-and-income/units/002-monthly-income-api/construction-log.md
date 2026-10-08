---
unit: 002-monthly-income-api
intent: 003-budget-periods-and-income
created: '2026-10-07T11:31:16Z'
last_updated: '2026-10-08T20:18:26Z'
---

# Construction Log: 002-monthly-income-api

## Original Plan

**From Inception**: 2 bolts planned
**Planned Date**: 2026-10-06

| Bolt ID | Stories | Type |
| --- | --- | --- |
| 014-monthly-income-api | 001-record-income, 002-select-dictionary-source, 003-record-amount-currency-date, 004-period-totals-by-currency | ddd-construction-bolt |
| 015-income-attachments-api | 005-private-income-attachments | ddd-construction-bolt |

## Current Bolt Structure

| Bolt ID | Stories | Status | Changed |
| --- | --- | --- | --- |
| 014-monthly-income-api | 001-record-income, 002-select-dictionary-source, 003-record-amount-currency-date, 004-period-totals-by-currency | ✅ complete | 2026-10-07T17:49:42Z |
| 015-income-attachments-api | 005-private-income-attachments | ✅ complete | 2026-10-08T20:18:26Z |

## Execution History

| Date | Bolt | Event | Details |
| --- | --- | --- | --- |
| 2026-10-07T11:28:03Z | 014-monthly-income-api | domain-model-ready | Prepared model, snapshots, eligibility, validation rules and proposed API contract for user checkpoint. |
| 2026-10-07T11:31:16Z | 014-monthly-income-api | domain-model-accepted | User selected option 1: accepted D1–D4 and the proposed API contract. Stage 1 complete; Stage 2 technical design is active. |
| 2026-10-07T11:33:22Z | 014-monthly-income-api | technical-design-ready | Documented persistence, API schemas, security, error codes, idempotency and lock/transaction sequence. Stage 2 awaits user checkpoint. |
| 2026-10-07T11:43:55Z | 014-monthly-income-api | independent-review | Reviewer scored Stage 2 as 7/10 and requires five design changes R1–R5 before acceptance. Findings and required tests are recorded in `ddd-02-technical-design.md`; no code changes authorized or made. |
| 2026-10-07T11:47:50Z | 014-monthly-income-api | technical-design-revised | Incorporated R1–R5 in the API, transaction, PATCH, 404, and conflict contracts. Prepared for independent re-review; user approval remains pending. |
| 2026-10-07T11:55:46Z | 014-monthly-income-api | technical-design-accepted | Second independent review of commit `7fa75b6`: R1–R5 resolved, no Stage 2 blocker, score 8.5/10. User's conditional acceptance applies after revisions. Stage 2 complete; review suggestions are recorded as pre-implementation follow-ups. |
| 2026-10-07T12:16:28Z | 014-monthly-income-api | adr-analysis-complete | User selected both proposed decisions. Created accepted ADR-007 for durable create idempotency and ADR-008 for historical snapshots and soft delete; updated the decision index. Stage 3 is complete; Stage 4 awaits human checkpoint approval. |
| 2026-10-07T13:31:28Z | 014-monthly-income-api | stage-start | Stage 4 Implement approved by the user's explicit instruction to continue. Resolved pre-implementation follow-ups in implementation-plan.md; based on current develop plus the in-progress 013 dependency. |
| 2026-10-07T13:51:15Z | 014-monthly-income-api | implement-complete | Added IncomeRecord and durable create idempotency, scoped income CRUD/options/totals API, migration and focused tests. 82 households tests pass and migration state matches models. scripts/quality.ps1 reaches format:check but reports 34 existing unformatted files outside this backend-only diff; full script is not green. Stage 5 awaits user checkpoint. |
| 2026-10-07T15:55:40Z | 014-monthly-income-api | stage4-review-fixes | Fixed contract option JSON projection by reusing the whitelisted contract snapshot and shared source eligibility query for options and writes. Added API render and inclusive overlap boundary regressions; 84 households tests, Ruff and diff checks pass. Full quality remains blocked by 34 existing Prettier files outside this backend diff. Prepared for independent Stage 4 re-review; Stage 5 has not started. |
| 2026-10-07T17:49:42Z | 014-monthly-income-api | stage5-accepted | Independent reviewer accepted Stage 5 at 8.8/10 after verifying 130/130 Django tests, 98% production households statement coverage, full quality and migration checks. P95 remains explicitly assigned to acceptance bolt 017. |
| 2026-10-07T17:49:42Z | 014-monthly-income-api | integrated-develop | Integrated `origin/develop` 7384b149; reviewer verified all eight resolved 013 files match develop and no merge conflicts remain. Merge commit `efd8abb` records the integration. |
| 2026-10-07T17:49:42Z | 014-monthly-income-api | bolt-complete | Official `bolt-complete.cjs` marked 014 and its four stories complete; it incorrectly marked unit 002 complete because its LF-only scan skipped the CRLF frontmatter in planned bolt 015. Corrected unit 002 back to in-progress; story 005 remains pending 015. Artifact path is `ddd-03-test-report.md`. |
| 2026-10-07T18:04:00Z | 014-monthly-income-api | completion-scope-corrected | Kept 014 and stories 001–004 complete, restored unit 002 to in-progress for pending story 005/bolt 015, and removed 015's self-referencing requires_units. The completion script's LF-only frontmatter scan had silently skipped 015's CRLF metadata. |
| 2026-10-07T18:03:48Z | 015-income-attachments-api | stage-start | Started Stage 1 Domain Model from develop commit 4e3b8de after PR #8 merged; required bolt 014 is complete. |
| 2026-10-07T20:08:00Z | 015-income-attachments-api | domain-model-ready | Modeled private attachment ownership, lifecycle, validation, access control, batch atomicity and cleanup; Stage 1 artifact submitted for independent review. |
| 2026-10-07T20:09:25Z | 015-income-attachments-api | domain-model-revised | Resolved reviewer findings on active-month mutation rules, single IncomeRecord aggregate ownership, batch visibility/orphan claims, and atomic audit versus asynchronous storage cleanup; committed as 54ce295. |
| 2026-10-07T20:13:37Z | 015-income-attachments-api | domain-model-accepted | Reviewer accepted model at 8.7/10. Incorporated both non-blocking P3 clarifications; Stage 1 complete. |
| 2026-10-07T20:13:37Z | 015-income-attachments-api | stage-start | Started Stage 2 Technical Design after Stage 1 acceptance. Inspected existing 014 API/models, ADR-006 lock order, private media volume, Caddy routes and backup/restore. |
| 2026-10-07T20:18:58Z | 015-income-attachments-api | technical-design-ready | Defined API, limits, private filesystem, transaction/lock order, cleanup/retention, audit, failure behavior and test plan. scripts/quality.ps1 and git diff --check passed; awaiting independent Stage 2 review. |
| 2026-10-07T20:25:05Z | 015-income-attachments-api | technical-design-revised | Reviewer returned 7.0/10 CHANGES REQUIRED (S2-1–S2-5); documented pre-parser byte limits, claim lock/fencing, 404 ordering, post-commit cleanup retries and bounded format contract. Resubmitted for review. |
| 2026-10-07T20:32:09Z | 015-income-attachments-api | technical-design-revised | Reviewer returned 8.0/10 CHANGES REQUIRED on commit `62e05da` (Caddy deadline semantics and Django StopUpload partial-result handling). Specified Caddy 2.10.0 absolute body-read deadline and direct-backend boundary; added request error latch, post-CSRF abort guard, DRF parser and SessionAuthentication checks, final use-case guard, atomic-batch failure mapping, and required regression tests. Resubmitted for independent review. |
| 2026-10-07T20:34:47Z | 015-income-attachments-api | technical-design-accepted | Independent review accepted commit `a77a951` at 8.7/10; all Stage 2 blockers resolved. ADR analysis found no new standalone decision beyond existing private storage/audit patterns; optional Stage 3 skipped. Began Stage 4 after prior user authorization for autonomous completion. Implementation will align Gunicorn sync worker timeout with Caddy upload deadline and test the actual end-to-end budget. |
| 2026-10-07T20:51:00Z | 015-income-attachments-api | implementation-ready | Implemented private attachment metadata, bounded format validation, staged all-or-nothing upload, tenant-scoped list/download/delete, audit/soft-delete cleanup, and dry-run reconciliation. Caddy 2.10.0 config validates; Ruff and scripts/quality.ps1 pass; 117 households tests pass, including seven attachment tests. Submitted Stage 4 for independent review; bolt advanced to Stage 5. |
| 2026-10-07T21:02:00Z | 015-income-attachments-api | stage4-review-fixes | Resolved reviewer R4-1–R4-4: post-commit finalization errors no longer compensate committed bytes; reconciliation persists cursors across bounded passes and detects missing/checksum-mismatched available files without deleting metadata; JPEG requires valid SOF/SOS/EOI structure. Added commit-boundary, reconciliation progress/integrity, and JPEG regressions. 123 households tests, full quality, Ruff and migration check pass; submitted updated commit for independent Stage 4 review. |
| 2026-10-07T21:08:00Z | 015-income-attachments-api | stage4-review-race-fix | Resolved reviewer R4-5 by re-reading the attachment after acquiring its batch lock and verifying only if its current state remains available. Added TransactionTestCase interleavings for committed removal against both dry-run and execute, plus invalid UUID cursor recovery and directory fsync after cursor replacement. Attachment suite: 15/15; requesting focused Stage 4 re-review. |
| 2026-10-07T21:21:01Z | 015-income-attachments-api | stage5-test-evidence | Added CSRF, upload byte-limit, failure/rollback/retry, cross-process flock and upload-vs-close/delete/capacity regressions. Full households suite 136/136 and scripts/quality.ps1 pass. Caddy 2.10.0 adapter includes request_body.read_timeout; corrected idle-body probe had upstream reject 1/4 bytes with 400 while client saw empty 200. Production Caddyfile remains unchanged. Stage 5 and bolt remain blocked pending diagnosis of this inconsistent runtime response and reviewer acceptance. |
| 2026-10-08T19:23:27Z | 015-income-attachments-api | stage5-review-evidence-revised | Added endpoint role/tenant/404 matrix and deterministic PostgreSQL lock/promotion/cleaner interleavings. Complete Django suite 168/168; explicit attachment production coverage 83% including reconciliation command at 73%; full quality passes. Repeatable asyncio TLS harness has valid positive controls, per-request byte/hash/access-log evidence and reproduces Caddy v2.10.0 empty 200 after deadline. Independent advisor confirms source semantics and proposes bounded repair candidates; production config remains unchanged and Stage 5 blocked. |
| 2026-10-08T20:02:48Z | 015-income-attachments-api | stage5-proxy-repair-ready | Resolved remaining role/period matrix cells and R5-5 fail-closed evidence manifest with ten self-tests. Full Django 169/169; attachment coverage 83% (1003 statements/170 missed). Baseline20 reproduced 28 empty H1 200 responses. After advisor consultation, ordered API-only write-before-read deadlines and explicit h1/h2 pass final 133/133 probes including 20 stalled/drip per protocol, concurrent H2 stream isolation and exact late-write A/B. ADR-009 proposed; technical design/report corrected Gunicorn to explicit 660 s. Awaiting independent review; no service restart or release. |

| 2026-10-08T20:13:54Z | 015-income-attachments-api | stage5-accepted | Reviewer accepted code 2a4dda2 and ADR-009 at 8.9/10 after independent 169/169 tests, 83% coverage, quality, ten assessor regressions, archived133 reassessment and fresh25 TLS smoke. R5-1–R5-5 resolved. |
| 2026-10-08T20:18:26Z | 015-income-attachments-api | bolt-complete | Official bolt-complete.cjs marked 015, story005 and unit002 complete. Normalized the scanner's relevant frontmatter to LF and verified that units003/004 and bolts016/017 remain planned; intent003 is not marked complete. Reconciled story-index from all48 source stories (41 complete,7 planned/draft). |

## Execution Summary

| Metric | Value |
| --- | --- |
| Original bolts planned | 2 |
| Current bolt count | 2 |
| Bolts completed | 2 |
| Bolts in progress | 0 |
| Bolts remaining | 0 |

## Notes

Bolts 014 and 015 and stories001–005 are complete and independently accepted. Unit002 is complete. The LF-only completion scanner was given readable relevant metadata; no framework source was modified. Bolts016 UI and017 acceptance remain planned; P95 belongs to017. Work stops after this completion and handoff report.
