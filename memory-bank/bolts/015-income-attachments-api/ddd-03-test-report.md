---
unit: 002-monthly-income-api
bolt: 015-income-attachments-api
stage: test
status: blocked
updated: '2026-10-07T21:21:01Z'
---

# Test Report - Monthly Income Attachments API

## Test Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Django households suite | 136 | 0 | 0 | Not measured |
| Attachment-specific suite | 26 | 0 | 0 | Not measured |
| Caddy HTTP upload smoke | 2 | 1 | 0 | N/A |
| Quality checks | Passed | 0 | 0 | N/A |

The 26 attachment tests are included in the 136-test `households.tests` total. Caddy's normal upload (200) and oversized upload (413) passed. The timeout behavior did not pass: Caddy 2.10.0 accepts the current `request_body read_timeout` configuration during validation but does not enforce it. The real idle-upload probe returned 200 instead of timing out. A correction requires choosing the intended idle-read timeout scope; the safe matching Caddy directive depends on changing the server-wide body idle timeout, so the persistent config change is awaiting explicit approval after automatic review blocked it.

## Acceptance Criteria Validation

| Story | Criteria | Status |
|-------|----------|--------|
| 005-private-income-attachments | Multiple supported files remain linked to the correct record and household | ✅ Django API and isolation tests pass |
| 005-private-income-attachments | Limits, content validation, atomicity, retention, and storage policy | ⚠️ Application tests pass; Caddy timeout remains unresolved |
| 005-private-income-attachments | Downloads require authorization; files cannot be fetched publicly or cross-tenant | ✅ Django API security tests pass |
| 005-private-income-attachments | Failure, orphan cleanup, size/type, role, and isolation tests | ✅ Django suite passes |

## Unit and Integration Tests

- `households.tests.test_income_attachments`: 26/26 pass.
- `households.tests`: 136/136 pass on PostgreSQL.
- Added/covered CSRF, multipart actual-byte limits, parser timeout/abort, atomic batch rollback, audit rollback, post-commit close failure, cleanup retry, cross-process claim flock, upload races with month close and parent delete, concurrent capacity reservation, and reconciliation consistency.

## Security and Runtime Tests

- Caddy 2.10.0 configuration validation passed.
- Real HTTP upload through Caddy: 4-byte body reached upstream and returned 200.
- Real HTTP body of 26 MiB + 1 byte returned 413.
- Real idle-body test exposed that the configured `request_body read_timeout` is not enforced by Caddy 2.10.0. No production configuration was changed during the probe.
- The 10-minute application upload guard and claim lock tests pass; the reverse-proxy idle-timeout policy still needs a reviewed configuration decision.

## Quality Checks

- `scripts/quality.ps1`: passed (89 Ruff files, Ruff checks, Prettier, ESLint, Stylelint, TypeScript typecheck).
- `git diff --check`: passed.
- Coverage and performance targets were not measured in this stage.

## Issues Found

| Issue | Severity | Status |
|-------|----------|--------|
| Caddy 2.10.0 ignores `request_body read_timeout`; safe 10-minute correction affects server-wide idle-read behavior | Medium | Open; automatic review blocked persistent change pending explicit approval |

## Ready for Operations

- [x] Application tests and quality checks pass
- [ ] All acceptance criteria met
- [ ] Coverage > 80% measured
- [ ] No open medium/high issues
- [ ] Performance targets measured where required
- [ ] Independent Stage 5 reviewer acceptance
- [ ] Human checkpoint for bolt completion

**Stage 5 status: blocked; bolt 015 remains in progress.**
