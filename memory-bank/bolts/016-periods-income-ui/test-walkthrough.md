---
stage: test
bolt: 016-periods-income-ui
created: "2026-10-09T14:04:56Z"
status: verified
test_commit: bb5598f
acceptance_run: 041217c6
---

# Test Report: 003-periods-income-ui

## Summary

- **Frontend controlled-response tests:** 67/67 passed in the implementation checkpoint.
- **Real HTTPS UI flows:** 10/10 passed across the verified family regression (5), period/income flows (4) and post-restart file verification (1).
- **Django regression:** 169/169 passed, exit 0, isolated test database with keepdb.
- **Quality:** scripts/quality.ps1 passed; Prettier, ESLint, Stylelint, TypeScript and Ruff.
- **Coverage:** not measured as a code percentage; all five stories verified through mapped scenarios.

The source installation uses an isolated Compose project, its own PostgreSQL/media volumes, synthetic users and HTTPS. Browser integration uses real API/session/CSRF/storage; no route mocking in periods-live.spec.ts.

## Test Files

- [x] frontend/tests/periods-api.spec.ts — shared transport, status confirmation and binary limits.
- [x] frontend/tests/periods-income.spec.ts — periods, source pagination, actual amounts, conflicts and responsive geometry.
- [x] frontend/tests/periods-recovery.spec.ts — unknown results, safe retries, role/membership loss and pending writes.
- [x] frontend/tests/periods-render.spec.ts — contextual screens, authenticated files and viewport geometry.
- [x] frontend/tests/periods-live.spec.ts — actual year creation, month transitions, recipients, dictionary creation, decimals, dates, three currencies, files, conflict merge and four roles.
- [x] frontend/tests/family-acceptance.spec.ts, family-live-fixture.ts — reused synthetic authentication and existing family/contract regression.
- [x] backend/accounts, households, runtime — complete Django regression, including concurrent period/income/attachment cases.

## Acceptance Criteria Validation

- ✅ **001-navigate-periods:** UI creates a real year and shows exactly 12 inactive months; responsive navigation, reader controls and recoverable error states verified.
- ✅ **002-change-period-state:** October and April activate independently; confirmed close/reopen changes real state and enables/disables actions.
- ✅ **003-add-income-recipient-source:** person selects a period-eligible source; household uses dictionary quick-add. Creating a source leaves income count unchanged and preserves the draft.
- ✅ **004-enter-income-details:** actual amount starts empty, remains independent of source/gross suggestions, keeps decimal precision and accepts receipt dates outside the accounting year. Real stale-version comparison and explicit merge use current version.
- ✅ **005-manage-attachments-and-totals:** month/year totals remain separated by currency; actual PNG/PDF batch uploads, byte-identical private download, deletion, invalid content rejection and closed-month downloads verified.

Geometry and no page-level horizontal overflow were checked at 1440/1024/390 px. Real UI flows additionally cover desktop Owner and mobile Administrator. Member/Viewer cannot write; foreign household access returns privacy-preserving 404, own-household forbidden writes return 403.

## Issues Found and Resolved

The initial PNG fixture had an invalid CRC. The backend correctly rejected it; the synthetic fixture was replaced with a valid one-pixel PNG. The foreign-household test initially expected 403 and was corrected to the actual privacy contract, 404.

The first Django run reached a teardown error from a remaining concurrency-test connection. The complete rerun with keepdb passed all 169 tests with exit 0, without affecting application data.

An API snapshot comparison originally overlapped a writing UI test and detected the legitimate fixture changes. The sequential rerun passed role/foreign-link checks and unchanged state/audit after rejected writes.

## Notes

The UI implementation and its Test stage are ready for completion under the user's explicit authorization of all remaining stages through merge/push/synchronization. The original Plan and Implement evidence remain historical checkpoints.

Bolt 017 remains planned: this scoped UI verification does not close the acceptance unit or the intent, does not provide a new P95 claim, and does not create a release. Private manifests, credentials, traces and database snapshots stay in ignored .runtime/test-results; only synthetic post-login screenshots are retained as public evidence.

Restart persistence PASS: family API snapshots and all household domain tables unchanged. A separate real browser check confirmed saved amount 8900.00 and byte-identical private PNG download after restart.

## Reproduction order

Use a fresh acceptance_stack init and family_acceptance prepare run. Execute family-acceptance (5) and periods-live excluding the after-restart case (4); run family_acceptance access without concurrent writers, then checkpoint and restart. Finally execute only the after-restart browser case (1). The browser test does not restart the stack itself. Keep manifests/env files private and outside Git. Story frontmatter and the unit index are the completion status; original AC checkboxes are definitions retained by the official generator, with validation mapped above.
