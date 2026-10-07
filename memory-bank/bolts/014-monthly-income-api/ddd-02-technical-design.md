---
unit: 002-monthly-income-api
bolt: 014-monthly-income-api
stage: design
status: awaiting-validation
created: '2026-10-07T11:31:16Z'
updated: '2026-10-07T11:43:55Z'
---

# Technical Design — 014-monthly-income-api

## Scope and approved inputs

This design implements the accepted domain model in [ddd-01-domain-model.md](ddd-01-domain-model.md) and D1–D4 checkpoint. Bolt 014 owns actual income records, dictionary eligibility, amount/currency/date validation, edits/deletes, audit, and month/year totals. It does not own the source dictionary, accounting-period lifecycle, attachments, UI, budgets, expenses, conversion, or income calculations.

`IncomeSource` and `Contract` remain configuration. `IncomeRecord.amount` is an independent actual receipt and is never initialized from gross contract pay or suggested source amounts. Accounting month is the user-selected allocation period and is independent of `receipt_date`.

## Architecture Pattern

Use the existing Django modular-monolith pattern: DRF presentation endpoints call focused application services, which apply domain rules and use Django ORM/PostgreSQL in explicit transactions. Keep serializers responsible for strict request validation and response schemas; keep business rules, row locks, audit creation, idempotency, and aggregation in application services. Household-scoped query helpers enforce tenant boundaries. No generic repository framework, signals, event bus, external service, or duplicated eligibility implementation is introduced.

The request path is:

```text
DRF route/view
    → strict serializer and access policy
    → income use case / shared eligibility rule
    → transaction and household/year locks
    → Django ORM and PostgreSQL
    → immutable AuditLog
```

### Layer responsibilities

| Layer | Responsibility |
| --- | --- |
| Presentation | Household-scoped routes, session/CSRF, serializer validation, pagination and HTTP mapping. Derive actor and household from authenticated request/path, never body fields. |
| Application | Create/update/soft-delete, source options, read/list and totals use cases; transaction boundary, locking order, current authorization check and idempotency replay. |
| Domain rules | Source-recipient-period eligibility, immutable month assignment, snapshot refresh rules, amount/currency/date semantics and active-period write invariant. |
| Persistence | PostgreSQL constraints and indexes, scoped ORM queries, migrations, income/idempotency rows and immutable audit rows. |

## API Design

All paths are under `/api/households/{household_id}/`, end with `/`, and use UUID path identifiers. All four household roles may read; only Owner and Administrator may mutate. Session authentication and CSRF follow the existing project contract. Do not accept `household_id`, actor, version, snapshots, deletion fields, or audit data from create input.

| Method and route | Access | Request | Response |
| --- | --- | --- | --- |
| `GET /accounting-years/{year_id}/months/{month_id}/incomes/` | Household member | Optional `page`; page size 50. | `count`, `next`, `previous`, `results`; ordered by `receipt_date`, `created_at`, `id`. |
| `POST /accounting-years/{year_id}/months/{month_id}/incomes/` | Owner/Admin; active month | JSON body below and UUID `Idempotency-Key` header. | `201` and the created income representation. An exact retry returns the stored original `201` result and creates no row/audit. |
| `GET /accounting-years/{year_id}/months/{month_id}/incomes/{income_id}/` | Household member | None. | One income representation; soft-deleted resources return `404`. |
| `PATCH /accounting-years/{year_id}/months/{month_id}/incomes/{income_id}/` | Owner/Admin; active month | One or more of `amount`, `currency`, `receipt_date`, `member_id`, `source_id`, plus mandatory integer `expected_version`. | `200` and updated representation. `month_id` is immutable and unknown fields fail validation. |
| `DELETE /accounting-years/{year_id}/months/{month_id}/incomes/{income_id}/` | Owner/Admin; active month | JSON body containing mandatory `expected_version`. | `204`; soft-delete. Subsequent normal GET/PATCH/DELETE returns `404`. |
| `GET /accounting-years/{year_id}/months/{month_id}/income-source-options/` | Household member; active month | `member_id={UUID}` for a person; omit for household recipient. | Page-number list of eligible dictionary source options, 50 per page, ordered by `name`, `id`. |
| `GET /accounting-years/{year_id}/months/{month_id}/income-totals/` | Household member | None. | `{"totals":[{"currency":"PLN","amount":"1000.00"}]}`; no entries: `{"totals":[]}`. |
| `GET /accounting-years/{year_id}/income-totals/` | Household member | None. | Same totals shape, aggregated by the year's assigned months, not receipt dates. |

Create example:

```http
Idempotency-Key: 98d3e9df-c0c5-4a7c-8c90-9f125af6b3ab
```

```json
{
  "member_id": null,
  "source_id": "7b372ef3-262e-46cf-b9c7-4c7bb302bc32",
  "amount": "800.00",
  "currency": "PLN",
  "receipt_date": "2026-09-30"
}
```

`member_id: null` means the household itself is the recipient. A person ID selects that exact active member. The returned record has `id`, `household_id`, `month_id`, `member_id`, `source_id`, `amount`, `currency`, `receipt_date`, `version`, `recipient_snapshot`, `source_snapshot`, `created_at`, and `updated_at`. Decimal values are JSON strings. Snapshot schemas are stable, versioned API objects; the contract contains names/types/identity only and never copies source or contract amounts into actual `amount`.

The snapshot JSON response shapes are:

```json
{
  "recipient_snapshot": {
    "kind": "member",
    "id": "4c3bb128-3faf-46b8-8fa0-202ad56ed2e2",
    "label": "Arek"
  },
  "source_snapshot": {
    "id": "7b372ef3-262e-46cf-b9c7-4c7bb302bc32",
    "name": "Sygnity",
    "kind": "contract",
    "version": 3,
    "contract": {
      "company_id": "9ee84b51-16e0-46fb-8e51-f89f72579c3f",
      "company_name": "Sygnity S.A.",
      "contract_type": "employment",
      "other_type_name": null
    }
  }
}
```

For a household recipient, `recipient_snapshot.kind` is `household` and `id` is `null`; its `label` is captured from the household's display label at create/reassignment. For a non-contract source, `source_snapshot.contract` is `null`. Snapshots contain no contract gross/default amount. A source option is `{id, name, kind, start_date, end_date, currency, contract}`; when `kind` is `contract`, `contract` contains company ID/name and contract type/name only. The option deliberately excludes gross amount. For an `other` source, `contract` is `null`.

The source-options endpoint and final create/reassignment call the same eligibility query/rule. It requires an active month because it supports a possible assignment; ordinary income reads and totals remain available for inactive and closed periods. A source is eligible only when its household and recipient exactly match and its active date interval inclusively overlaps the selected accounting month. `receipt_date` does not change eligibility. Archived sources and members are excluded from new assignments but remain visible through existing income snapshots. A later company archive does not invalidate an existing active contract source. `one_off` permits multiple distinct receipts.

### Validation and error contract

- `amount` accepts only a JSON decimal string with at most two fractional digits, from `0.01` through `9999999999999999.99`. Reject zero, negatives, excess precision and overflow; never round silently.
- `currency` is exactly three uppercase letters, per the current project convention. It is independent of source currency; there is no conversion.
- `receipt_date` is a valid ISO calendar date and may be before/after the accounting month or in the future.
- Unknown JSON fields are rejected. Invalid field data returns `400` with field-level validation feedback and does not write income or audit.
- Inaccessible household/foreign/missing resource returns `404`; an authenticated household user without write role or a missing/invalid CSRF token returns `403` under the existing API behavior.
- Mutations in inactive/closed periods return `409` with `code: "income_period_not_active"` and current period state. A stale `expected_version` returns `409` with `code: "income_version_conflict"` and the current version. Reusing an idempotency key with another payload returns `409` with `code: "idempotency_conflict"`.
- Successful idempotent replay is checked only after current session, household access and write-role checks. A matching replay returns the stored create result before period/source revalidation, so a retry after close/archive remains the same operation. The saved response is the original create representation; a later GET can return `404` if that income has subsequently been soft-deleted.
- An `Idempotency-Key` that is not a UUID returns `400`. Missing key on POST returns `400` with a field/header validation error.
- Unsupported methods return `405`. Totals are exact decimal database sums grouped and ordered by currency; no combined cross-currency amount is returned. Aggregate totals are not capped at the per-record maximum.

## Data Persistence

Use two new PostgreSQL tables and the existing immutable audit table. Schema names are descriptive; exact Django naming is decided during implementation without changing public JSON fields.

| Table | Columns and constraints | Relationships and indexes |
| --- | --- | --- |
| `IncomeRecord` | UUID PK; `household_id`; `accounting_month_id`; nullable `member_id`; `income_source_id`; `amount NUMERIC(18,2)`; `currency CHAR(3)`; `receipt_date DATE`; `recipient_snapshot JSONB`; `source_snapshot JSONB`; `version INTEGER` default 1; `created_at`, `updated_at`; nullable `deleted_at`, `deleted_by_id`. DB checks: `amount > 0`, `version > 0`, currency `^[A-Z]{3}$`, deletion timestamp/actor both null or both present. | FKs to Household, AccountingMonth, HouseholdMember, IncomeSource and deleting actor use `PROTECT`; snapshots preserve the creation-time display values. Index `(household_id, accounting_month_id, receipt_date, created_at, id)` for lists and `(household_id, accounting_month_id, currency)` for totals. Add household/member/source lookup indexes for eligibility and detail queries. |
| `IncomeCreateIdempotency` | UUID PK; `household_id`; `actor_id`; operation code (`income.create`); UUID client key; SHA-256 request fingerprint; JSONB stored HTTP status/body; `created_at`. | FKs to Household, User and created IncomeRecord use `PROTECT`. Unique `(household_id, actor_id, operation, client_key)`. Retain at least as long as the soft-deleted or active income record; there is no time-based expiry that could make an old retry create a second income. |
| Existing `AuditLog` | Existing immutable UUID event; extend allowed object type to `income_record`; create/update/delete action; before/after JSON includes actor-visible business values and snapshots, not attachments. | FK to household and actor remains protected. Write audit in the same transaction as record mutation. Idempotent replay writes no second audit event. |

`IncomeRecord` is the root of a single-entry aggregate; `AccountingYear` remains the cross-context synchronization root. The unique idempotency constraint is the final duplicate guard even though `locked_access` serializes household mutations. Snapshot JSON is immutable after creation except when an explicit recipient/source reassignment records its own before/after audit. The request model stores current FKs alongside snapshots: FK identity supports authorization and queries; snapshots support faithful historical display. Soft delete preserves FKs, snapshots and audit history.

## Transaction and concurrency design

All financial mutations run in `transaction.atomic()` and follow ADR-002/ADR-006 order: acquire `locked_access` (Household row), recheck membership/role, then lock the matching `AccountingYear` row. Resolve year/month IDs scoped to the URL household, verify the month belongs to that year, and read its state only after the year lock. The month must be `active` for a new mutation. No file or network I/O occurs in the transaction.

Create sequence:

1. Validate request shape and UUID key before opening the transaction.
2. Acquire household access lock and recheck Owner/Admin.
3. Look up the key in its household/actor/operation scope. If found, compare canonical payload fingerprint; return its stored result on match or `409` on mismatch. This lookup precedes period state validation so a lost-response retry after close does not create or report a second operation.
4. For a new key, lock the accounting year, verify URL ownership and `active` month.
5. Resolve and validate member/source and period overlap; capture recipient/source snapshots.
6. Insert IncomeRecord, its immutable audit, and the idempotency key plus original response body in the same transaction. Unique-constraint collision is caught and resolved by re-reading the existing key and applying step 3 semantics.

PATCH/DELETE sequence: household access lock and role recheck → accounting year lock → active month check → scoped, non-deleted IncomeRecord lock → compare `expected_version` → validate changed relationships and preserve unchanged historical relationships → apply mutation and increment version → audit before/after → commit. A failed validation, conflict or audit insert rolls back all changes. DELETE stores `deleted_at` and `deleted_by`, increments version, and audits once; all normal detail/list/total querysets filter out deleted rows.

Close versus income write is serialized by the same year lock. The result is either an income mutation committed before close, or a rejected mutation after close commits; no mutation may commit using a stale `active` read. Eligibility changes are serialized by the existing household access lock; every final write repeats the eligibility predicate after that lock. Concurrency tests for these guarantees must run against PostgreSQL.

Totals are read-only exact aggregates. Month totals filter by household/month and `deleted_at IS NULL`, group by currency, and use `SUM(amount)`. Year totals join through the year's months and apply the same filter. Closed months remain included. Neither query reads `Contract.gross_amount` or source defaults.

## Security Design

| Concern | Approach |
| --- | --- |
| Authentication and CSRF | Existing Django session authentication and explicit CSRF for unsafe requests; no token or actor fields in request bodies. |
| Authorization | All household roles read; Owner/Admin write. Every request checks current membership. Mutations use `locked_access` and recheck role after acquiring Household lock. |
| Tenant isolation | Every queryset is scoped to URL household. Year, month, member, source, income and idempotency key are resolved in that scope; foreign/missing identifiers share a not-found result. |
| Historical integrity | FK `PROTECT`, immutable snapshots, soft deletion, optimistic `expected_version`, atomic audit. No normal endpoint mutates or deletes audit history. |
| Idempotency | UUID key scoped by household/actor/operation and protected by a database unique constraint. Replays require current access and cannot expose another actor's result. |
| Input | Strict serializers reject unknown fields, arbitrary source names, client-supplied audit data and untrusted ownership metadata. Exact decimal parsing avoids float arithmetic. |
| Transport/storage | Use existing local HTTPS endpoint and PostgreSQL network boundary; no external integration or new secret-bearing service. Attachment bytes are out of scope and remain private under bolt 015. |

## NFR Implementation

| Requirement | Design approach |
| --- | --- |
| Financial integrity | PostgreSQL Decimal sums and check constraints; explicit migrations; audit and mutation atomic; no implicit rounding or currency conversion. |
| Concurrency | Stable Household → AccountingYear lock order, row lock/version compare for edits, unique idempotency constraint, PostgreSQL race tests for close/create/PATCH/DELETE and same-key retries. |
| Performance | Page size 50, deterministic indexed list order, database aggregation, indexes for household/month/currency and source eligibility. Avoid per-row lookups by selecting the related snapshot/source data needed for a page. P95 <500 ms remains unverified and is measured in bolt 017. |
| Reliability | One transaction for each mutation plus audit/idempotency result; database uniqueness handles simultaneous keys; rollback leaves no partial income, audit, or key. No external dependency. |
| Compatibility | New paths are additive and do not change existing family-income or periods endpoints. Public API uses accepted `source_id` even if persistence uses an `income_source_id` relation. |
| Observability | Existing audit records meaningful writes; application logs may record error code/request correlation but must not log financial payloads unnecessarily. No separate event store. |

## Error Handling

| Error | HTTP | Stable code/response |
| --- | --- | --- |
| Invalid amount/currency/date/UUID/unknown field/missing idempotency key | 400 | Existing field-error form; identify invalid field/header, no writes. |
| Ineligible recipient/source or source period mismatch | 400 | `source_id` or `member_id` field error; no writes. |
| No session, failed CSRF, or read-only role attempting a mutation | 403 | Existing authentication/permission response. |
| Foreign/missing household, year, month, member, source or income | 404 | Existing not-found response, independent of whether ID belongs to another tenant. |
| Inactive or closed accounting month | 409 | `{"code":"income_period_not_active"}`. |
| Stale `expected_version` | 409 | `{"code":"income_version_conflict"}`; client refetches the resource to obtain the latest version. |
| Same idempotency key with a different payload | 409 | `{"code":"idempotency_conflict"}`. |
| Unsupported HTTP method | 405 | Existing method-not-allowed response. |

Use the existing DRF field-error shape for validation and the existing compact `{ "code": ... }` conflict convention; do not introduce a global error envelope. The stable codes above extend, rather than replace, existing API errors such as the periods API's `accounting_period_conflict`. Exact localized human wording can evolve; clients rely on status, code and field path.

## External Dependencies

| Service | Purpose | Integration |
| --- | --- | --- |
| PostgreSQL 17 | Transactional records, row locks, unique/check constraints and decimal aggregation. | Existing Django ORM connection. |
| Household/access and accounting-period domains | Membership/role verification and the shared year-lock lifecycle contract. | In-process application calls; ADR-002 and ADR-006. |
| Existing immutable audit | Record actor, action, object, before and after state atomically. | In-process ORM write under ADR-004. |
| IncomeSource/Contract dictionary | Validate eligible source and preserve its identity in the income record. | In-process scoped relationship; gross/default amounts remain separate. |

There are no new external services or package dependencies in this design.

## Implementation and verification boundary

The later implementation/test stages must include migrations and prove: all four roles; session/CSRF; household isolation for every identifier; Member/Viewer denied writes; snapshots remain stable after source/member/company archive or conversion; strict amount/date boundaries; create retry with same and conflicting payloads including concurrent same-key POST; version conflicts; audit rollback; exact month/year totals and deleted-row exclusion; and both PostgreSQL close-write orders for create, PATCH and DELETE. Full system P95 remains a bolt 017 acceptance item.

## Stage 2 checkpoint

The user has accepted the domain rules and route family. This stage asks approval for the technical choices that make them executable: `IncomeRecord` plus `IncomeCreateIdempotency` tables; JSONB snapshots and protected relationships; stored original response for idempotent create; lock and transaction sequence above; stable error codes; endpoint access/pagination; and the listed constraints/indexes. Any requested change must be incorporated before Stage 3 or implementation.

## Independent review — required changes before Stage 2 acceptance

The independent reviewer rated this design **7/10** and recommended revision before acceptance. The following five items are required changes, not optional suggestions. Stage 2 remains awaiting validation until they are resolved in the design and verified by a second review.

### R1 — Bind an idempotency fingerprint to the URL operation

**Finding:** A fingerprint of only the request body can replay the result from one month when the same key/body is sent to another month. Looking up the key before validating the URL can also disclose a stored result for a missing or foreign year/month.

**Required design change:** Keep key uniqueness scoped to `(household, actor, operation)`; do not add month to the key scope. Define a versioned canonical fingerprint over operation, `year_id`, `month_id`, and normalized body. Normalize UUID text, amount, date, and household-recipient `member_id`; explicitly treat omitted and `null` `member_id` consistently. Resolve and tenant-scope the year/month path before replay, without requiring the month to remain active. A foreign/missing path returns `404`; the same key with a different valid month or payload returns `409 idempotency_conflict`. Exact retries after close, source/member archive, later edit, or soft-delete may replay the stored original `201` only while current access and write role remain valid.

**Required tests:** Same key/body under two valid months conflicts and creates no second income; missing/foreign year or month does not replay; exact retry after close/archive/edit/delete returns the saved original response without a second audit; revoked membership or write role prevents replay.

### R2 — Validate the effective recipient/source pair on PATCH

**Finding:** The current rule “validate changed relationships and preserve unchanged historical relationships” is ambiguous for partial PATCH. Changing only `member_id` while retaining a source assigned to the old member could bypass new-assignment eligibility.

**Required design change:** Construct `effective_member_id` and `effective_source_id` from the stored values plus PATCH fields, then compare actual IDs. If neither ID changes, retain both historical relationships without revalidating archived records. If either ID changes, validate the resulting pair together: member (if any) and source must be active, tenant-scoped, assigned to the same resulting recipient, and the source date interval must overlap the accounting month. Refresh `recipient_snapshot` only when `member_id` actually changes; refresh `source_snapshot` only when `source_id` actually changes. Explicitly resubmitting an unchanged ID does not refresh a snapshot.

**Required tests:** `member_id` only, `source_id` only, both changed, neither changed, and same IDs resubmitted; cover mismatched ownership, archived old relations, and source recipient changed in the dictionary. A member-only change must fail when the retained source belongs to the old member.

### R3 — Define the unique-key collision transaction boundary

**Finding:** The current “catch collision and re-read” instruction does not say whether the error occurs inside a broken atomic block or whether income/audit could commit without the key.

**Required design change:** Use the household lock to serialize ordinary same-scope requests and the unique constraint as the final guard. Prefer treating any unexpected idempotency uniqueness violation as failure of the entire outer transaction: roll back income, audit, and key together, then let the client retry and observe the committed key. Do not catch/recover `IntegrityError` unless the design first introduces a savepoint around the full income+audit+key unit, catches only the named key constraint after savepoint rollback, and proves no partial writes. Propagate unrelated integrity errors.

**Required tests:** Parallel same-key/same-payload and same-key/different-payload requests; forced uniqueness conflict at the end of create; audit failure; idempotency insert failure. Final state must contain exactly one income/audit/key on success and no partial income/audit/key after a failed unit.

### R4 — Make 404 precedence consistent for missing/deleted records

**Finding:** PATCH/DELETE currently check period state before loading the scoped income. A deleted, missing, or foreign income under an inactive/closed month could return `409` instead of the documented `404`.

**Required design change:** Keep the lock order `Household → AccountingYear`, then resolve and lock the scoped, non-deleted income before checking active month state; only then validate the period, version, and mutation. Preserve `404` for missing, deleted, or foreign income regardless of whether its month is active, inactive, or closed. Ensure URL year/month ownership is checked before resource lookup.

**Required tests:** Matrix of deleted/missing/foreign income against active/inactive/closed month, with a `404` result for every unavailable income. Existing close/write tests must still prove both serial orders for create/PATCH/DELETE.

### R5 — Specify one exact 409 response shape and handler integration

**Finding:** Prose promises period state/current version, while examples return code-only bodies. The existing exception handler currently maps only existing conflicts, so new cases would not necessarily produce the documented response.

**Required design change:** Choose one exact JSON shape for each new conflict and use it consistently in prose, examples, endpoint notes, and tests. Preserve the current DRF field-error shape for `400` and current conflict convention for `409`; extend the existing exception mapping or use an explicit view response mapping, without introducing a global envelope. Either include `state`/`current_version` everywhere they are promised, or remove those promises and require clients to refetch.

**Required tests:** Assert exact status and JSON for inactive/closed period, stale version, and idempotency conflict; assert that existing period conflicts retain their current response shape.

The reviewer's additional suggestions (tenant-consistency rules for every FK, strict JSON types/no-op PATCH behavior, snapshot schema/action length, option endpoint edge cases, and additional overlap/aggregation fixtures) are advisory follow-ups. Include them in technical criteria where they close an ambiguity, but they are distinct from required changes R1–R5.
