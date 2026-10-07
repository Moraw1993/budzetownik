---
unit: 002-monthly-income-api
bolt: 014-monthly-income-api
stage: test
status: complete
updated: '2026-10-07T18:04:00Z'
---

# Test Report — 002-monthly-income-api

## Test Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Focused income API, concurrency, acceptance | 35 | 0 | 0 | Included below |
| Full Django backend suite after integrating develop `7384b1490271e6b5e2f82c95aa8d92aafd24aac7` | 130 | 0 | 0 | 98% statements — households production |
| Performance | Not run | — | — | P95 belongs to acceptance bolt 017 |
| **Verified total** | **130 in full suite** | **0** | **0** | **98% statements — households production** |

The focused 35-test run is included in the full 130-test backend suite; totals are not additive.

## Acceptance Criteria Validation

| Story / criterion | Evidence | Status |
|-------|----------|--------|
| Create, edit and delete require authorization and an active period; close/write interleavings are serialized | PostgreSQL tests cover CREATE/PATCH/DELETE in both close-first and write-first orders; backend lock wait is observed before releasing the competing transaction | ✅ |
| Income entries remain separate from contract gross/default amounts; dictionary changes preserve historical snapshots | API and acceptance tests verify immutable recipient/source snapshots, contract details, source conversion, reassignment, archive and audit history | ✅ |
| Receipt dates may differ from accounting period; currencies remain separate | Acceptance tests cover prior-period and future dates, calendar boundaries, currency validation, exact monthly/yearly totals and deleted-row exclusion | ✅ |
| Validation, audit, tenant isolation, roles and idempotency work under retries and concurrency | 35 focused tests and the full Django suite pass on PostgreSQL; tenant/role/CSRF, rollback, replay and conflicting-key scenarios are covered | ✅ |
| Coverage and performance | Production household modules reached 98% statement coverage; P95 measurement is assigned to acceptance bolt 017 | ✅ coverage / ⏳ P95 in 017 |

## Unit and Integration Tests

- python manage.py test households.tests.test_monthly_income_api households.tests.test_monthly_income_concurrency households.tests.test_monthly_income_acceptance --noinput: **35/35 passed** on an isolated PostgreSQL test database.
- python manage.py test --noinput: **130/130 passed** on a separate isolated PostgreSQL test database.
- The same full suite passed under coverage.py; coverage.py was installed only in the disposable container at /tmp, not in project dependencies.
- PostgreSQL race tests hold the first transaction, observe the competing backend waiting on a lock, then release it. Concurrent idempotency tests assert one income, one audit, one scoped idempotency row, the saved 201 response, and the winning record version.
- The role/security matrix checks anonymous requests, all household roles, tenant-mixed identifiers and enforced CSRF failures, including record/audit/idempotency side-effect counts.

## Security Tests

Authentication, household role authorization, tenant isolation, and CSRF rejection are included in the 35 focused tests. Rejected anonymous and CSRF requests assert that income, audit and idempotency row counts remain unchanged.

## Performance Tests

No P95 measurement was run in this bolt. The intent assigns end-to-end P95 measurement to acceptance bolt 017; no performance result is claimed here. This is not a completion gate specific to bolt 014.

## Coverage Report

The full backend suite was run with coverage.py 7.16.2 over the production households package, excluding tests and migrations: **98% statement coverage (1,327 statements, 28 missed)**. This is statement coverage, not branch coverage, and does not represent every backend package. The generic DDD template target of >80% is met. Coverage was installed only in the disposable container; no project dependency or generated artifact was added.

Reproduction commands inside the disposable backend container:

- python -m coverage run --source=households --omit="*/tests/*,*/migrations/*" manage.py test --noinput
- python -m coverage report --omit="*/tests/*,*/migrations/*" --fail-under=80

## Quality and Dependency Gates

- Ruff format check: **78 plików backend/scripts już sformatowanych**.
- Ruff check: **passed**.
- git diff --check: **passed**.
- makemigrations --check --dry-run households: **no changes detected**.
- scripts/quality.ps1 after integrating the repository LF policy from PR #6: **passed** (Ruff, Prettier, ESLint, Stylelint, TypeScript).
- Required bolt 013-periods-api: **complete and merged into develop** in PR #7 (`7384b1490271e6b5e2f82c95aa8d92aafd24aac7`). Its final acceptance test and lock-order regression test are included in this branch.

## Independent Review

The reviewer accepted the Stage 5 test checkpoint at **8.8/10 (PASS)**. The review confirmed the 35 focused tests, full 130-test suite, Ruff checks, migration check, unchanged production implementation, and the S5-1 through S5-3 concurrency/history/security evidence. Three non-blocking clarity suggestions were applied: explicit version/status assertions in both idempotency races, before/after state counts for anonymous and CSRF requests, and a fixture with equal receipt date and creation time to exercise the ID tie-breaker. The reviewer completed the follow-up review with **ACCEPTED / PASS (8.8/10)**.

## Issues Found

| Issue | Severity | Status |
|-------|----------|--------|
| Existing Prettier baseline | Quality gate | Resolved by repository LF policy in PR #6; full quality gate passes |
| Bolt 013 prerequisite | Dependency gate | Complete and merged in PR #7 |
| Independent review of the P3 clarifications | Review gate | Accepted / PASS (8.8/10) |

## Ready for Operations

- [x] Bolt 014 criteria and prerequisites complete; unit 002 waits for 015
- [x] Coverage target measured and met
- [x] Full quality script passes
- [x] Independent test checkpoint review accepted
- [x] Bolt 014 and stories 001–004 are complete; unit 002 remains in progress until bolt 015 completes story 005.
