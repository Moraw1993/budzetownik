---
unit: 002-monthly-income-api
bolt: 014-monthly-income-api
stage: implement
created: '2026-10-07T13:31:28Z'
updated: '2026-10-07T13:31:28Z'
---

# Stage 4 Implementation Plan — 014-monthly-income-api

## Decisions resolving the accepted design follow-ups

- `amount` must arrive as a JSON string matching a decimal lexical form with no whitespace, sign, or exponent. It must contain no more than two fractional digits, be greater than zero, and fit `Decimal(18,2)`. The API returns it with exactly two fractional digits.
- `expected_version` must be a JSON integer greater than or equal to one. Booleans and numeric strings are rejected.
- A PATCH with valid mutable fields that produce no state change returns `200` with the current representation and writes neither a version increment nor an audit event. A PATCH containing only `expected_version` is invalid.
- Source options require an active accounting month. A missing, foreign, or archived `member_id` returns `404`; a valid active recipient with no eligible sources receives an empty paginated result.
- Recipient snapshots use `{kind, id, label}`. Source snapshots use `{id, name, kind, version, contract}`; `version` is the dictionary version, `other_type_name` is normalized to `null`, and the contract object excludes gross/default amounts. Household recipient snapshots use `kind: household` and `id: null`.
- Unexpected uniqueness/integrity failures abort the full outer transaction; implementation does not catch and recover inside it. Audit, income and idempotency records commit or roll back together.

## Implementation slices

1. Add income and create-idempotency persistence models with constraints and indexes; generate and inspect the Django migration.
2. Add strict serializers, shared recipient/source eligibility, immutable snapshots, locked transactional use cases, audit and idempotency behavior.
3. Add household-scoped list/detail/create/PATCH/DELETE, source-options and month/year totals endpoints; map conflicts using the established envelope.
4. Add focused API and PostgreSQL concurrency coverage for contract, tenancy, role, audit, rollback, versioning, snapshots, retries, source eligibility and close/write ordering.

## Stage 5 verification checklist

- All household roles, authentication/CSRF, tenant isolation and unknown-field rejection.
- Exact JSON status/code for period, version and idempotency conflicts; existing period conflicts remain unchanged.
- Decimal string lexical and boundary cases; date outside accounting period; currencies remain independent.
- Source/member/company archival and reassignment snapshots; source-option overlap boundaries, no end date, leap February and empty results.
- Idempotency fingerprint includes operation, year, month and canonical body; replay after close/archive/edit/delete and after access revocation; same key across months conflicts.
- PATCH relationship matrix (member/source/both/neither/same IDs), unchanged historical links and no-op semantics.
- Deleted/missing/foreign PATCH/DELETE return 404 in active, inactive and closed months.
- Injected income, audit and idempotency persistence failures leave no partial rows.
- PostgreSQL races for create, PATCH and DELETE against close, and concurrent same-key retries.
- Exact month/year Decimal sums, currency grouping and soft-deleted row exclusion.

Concurrency guarantees and the complete matrix remain unverified until PostgreSQL-backed tests pass; bolt 013 remains an in-progress dependency.
