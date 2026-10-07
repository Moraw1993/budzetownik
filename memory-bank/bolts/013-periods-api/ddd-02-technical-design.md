---
unit: 001-periods-api
bolt: 013-periods-api
stage: technical-design
status: complete
created: '2026-10-07T10:11:57Z'
updated: '2026-10-07T11:18:44Z'
---

# Technical Design — 013-periods-api

## Scope and constraints

This bolt implements accounting years and the lifecycle of their twelve accounting months. It does not create income records or income sources. The next bolt, `014-monthly-income-api`, will use the month state as a write guard.

The design follows the existing modular-monolith architecture and the accepted household-access and immutable-audit decisions. This artifact records the implemented contract verified in Stage 4 and the complete lifecycle matrix added during replanning; these details are no longer proposals.

## Component design

The request path is:

`DRF route/view → application use case → AccountingYear aggregate/repository → PostgreSQL`

The API layer validates request shape, establishes the authenticated actor, applies household membership and role policy, and maps application outcomes to HTTP responses. Use cases coordinate transactions, locking, aggregate rules, and the existing financial audit writer. The aggregate enforces the twelve-month structure and legal state transitions. Repository queries always scope by household. No Django signals or external event store are introduced.

## API contract

All routes are household-scoped, consistent with ADR-002.

| Method and route | Access | Implemented behavior |
| --- | --- | --- |
| `GET /api/households/{household_id}/accounting-years/` | Household member | Standard page-number pagination, 50 per page; ordered by descending `calendar_year`, then `id`. Each result has `id`, `household_id`, `calendar_year`, `created_at`. |
| `POST /api/households/{household_id}/accounting-years/` | Owner/Admin | Accept exactly `{ "calendar_year": 2027 }`, integer range `1..9999`; atomically create the year and twelve inactive months; return `201` with year fields and ordered `months`. |
| `GET /api/households/{household_id}/accounting-years/{year_id}/months/` | Household member | Return a JSON array of 12 months, ordered January through December. Each has `id`, `accounting_year_id`, `month_number`, `state`, `month_start`, `month_end`, `activated_at`, `closed_at`, `created_at`, `updated_at`. |
| `POST /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/activate/` | Owner/Admin | Apply target-state operation `activate`. |
| `POST /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/close/` | Owner/Admin | Apply target-state operation `close`. |
| `POST /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/reopen/` | Owner/Admin | Apply target-state operation `reopen`. |

All route and response IDs are UUIDs. Every path ends with `/`. A successful year create returns `201`; lifecycle actions return `200` and the month representation. A duplicate year returns `409` with code `accounting_period_conflict`. Named transition operations prevent callers from assigning arbitrary lifecycle states. Every operation verifies that the year and month belong to the household in the URL. Income CRUD routes are out of scope.

## Persistence design

The implemented relational model uses two tables with UUID primary keys:

| Table | Fields and constraints |
| --- | --- |
| `AccountingYear` | `id`, `household_id` FK, `calendar_year`, `created_at`; unique `(household_id, calendar_year)`; calendar year range `1..9999` so every value is representable by the calendar date domain. |
| `AccountingMonth` | `id`, `accounting_year_id` FK, `month_number`, `state`, `activated_at`, `closed_at`, `created_at`, `updated_at`; unique `(accounting_year_id, month_number)`; check `month_number` between 1 and 12; state restricted to `inactive`, `active`, or `closed`. |

The unique year constraint supports household year listing and duplicate prevention. The month constraint supports ordered month access. Create the year and all twelve month rows in one database transaction, with month number derived from 1 through 12 and initial state `inactive`. Do not publish or return success if fewer than twelve rows were persisted. A repeated create for the same household/year returns conflict.

The month timestamps represent the most recent activation and close; immutable audit records retain the full transition history. `activated_at` is set on activation and every successful reopen. `closed_at` is set on close and retained after reopen. No-op and rejected transitions preserve both timestamps.

## State transitions and idempotency

| State before | Operation | HTTP/result | Timestamp and audit behavior |
| --- | --- | --- | --- |
| `inactive` | activate | `200`, `active` | Set `activated_at`; append one `activated` audit. |
| `inactive` | close | `409`, unchanged | No timestamp or audit change. |
| `inactive` | reopen | `409`, unchanged | No timestamp or audit change. |
| `active` | activate | `200`, no-op | Preserve both timestamps; no audit. |
| `active` | close | `200`, `closed` | Set `closed_at`; preserve `activated_at`; append one `closed` audit. |
| `active` | reopen | `200`, no-op | Preserve both timestamps; no audit, including when no prior close exists. |
| `closed` | activate | `409`, unchanged | No timestamp or audit change. |
| `closed` | close | `200`, no-op | Preserve both timestamps; no audit. |
| `closed` | reopen | `200`, `active` | Set a new `activated_at`; preserve `closed_at` as the latest close; append one `reopened` audit. |

The rule is target-state idempotency: if the current state already equals that operation's target, return `200` without changing timestamps or appending audit. All other state/operation combinations return `409` with `accounting_period_conflict`. This includes `reopen(active)`, even without a previous close. No request-version token is currently used, so a delayed old close after a later reopen is not distinguished from a current close; any change requires a separate design decision in bolt 014.

## Authorization and tenant isolation

- Preserve the existing authenticated session and CSRF protections for state-changing requests.
- Household members may read years and months. Only Owner and Admin may create years or change month state; Member and Viewer receive `403` on writes.
- Resolve each object through the household-scoped query, not by loading a global id and trusting a later check. Missing and cross-household objects both return `404` to avoid disclosing another household's records.
- Route every mutation through the existing `locked_access` policy. It locks the `Household` row and re-checks membership and role after acquiring that lock, as required by ADR-002.
- For period state changes, acquire the `AccountingYear` row lock only after `locked_access` has acquired the household lock and revalidated access. Keep this lock order (`Household` then `AccountingYear`) consistent in every caller.
- Do not accept household, actor, role, or audit identity from the request body.

## Transactions and concurrency

Year creation runs in `transaction.atomic()`. Database uniqueness is the final guard against concurrent duplicate creates; translate the losing insert to `409 Conflict`, with the transaction rolled back so no partial months remain.

State changes run inside `locked_access`, which first locks the `Household` row and re-checks membership/role. They then lock the `AccountingYear` row with `select_for_update()`, resolve the month within that locked year, verify its state, persist the transition, and append the immutable audit record in the same transaction. This preserves ADR-002's lock order and gives the future income writer a shared period-domain synchronization point.

Bolt `014-monthly-income-api` must enter `locked_access` first, then acquire the same year lock before checking that a month is active and before persisting an income change, keeping the state check and income write in the same transaction. Therefore close-versus-income races serialize: whichever transaction obtains the year lock first determines whether the income write precedes the close or is rejected after it. The existing household lock serializes household mutations more broadly under ADR-002; the year lock remains the explicit shared contract for operations governed by period state. Transactions must remain short and database-only. Validate the target API latency of P95 below 500 ms under representative household load.

## Audit integration

Append the transition to the existing immutable financial audit mechanism in the same database transaction as the period change, following ADR-004. A month event stores `object_type=accounting_month`, `object_id=<month UUID>`, actor, `occurred_at`, action, and before/after state JSON. The year is resolved through `AccountingMonth.accounting_year_id`; `month_number` is available on that row. Current transition JSON records state before and after. New events may additionally duplicate `accounting_year_id`, `calendar_year`, and `month_number` for self-contained reads, but this extension is not implemented and requires a recorded contract decision; historical events are not rewritten.

Year creation stores `object_type=accounting_year`, the year UUID, actor/time/action, and an after snapshot containing `calendar_year`, the twelve `month_ids`, and `initial_month_state`. No audit event is added for an idempotent transition. Do not duplicate audit infrastructure, persist sensitive request payloads, or use signals that could separate the audit outcome from transaction success. No standalone event store is introduced.

## HTTP error mapping

| Condition | HTTP status |
| --- | --- |
| Malformed payload or invalid calendar year | `400 Bad Request` |
| Anonymous request, failed session authentication, missing CSRF on a session write, or authenticated non-writer mutation | `403 Forbidden` (response details distinguish the reason) |
| Missing year/month or object outside the URL household | `404 Not Found` |
| Duplicate year or invalid lifecycle transition | `409 Conflict` |

Malformed input uses the existing DRF validation response shape; lifecycle/year conflicts include `code=accounting_period_conflict`. Do not introduce a new global response envelope for this bolt.

## Reliability and performance

- PostgreSQL is the source of truth; year creation, transitions, and audit writes are transactional.
- Enforce year/month uniqueness and month-number/state domains in the database as well as in application logic.
- Retrieve the twelve months in one ordered query; avoid N+1 access. The year list uses the existing page-number pagination at 50 per page.
- Keep aggregate locks limited to the mutation transaction and avoid network or file operations while holding them.
- Target P95 below 500 ms for year listing, month listing, creation, and lifecycle operations under representative load.

## Verification design

The implementation and tests must demonstrate:

1. A newly created year has exactly twelve uniquely numbered months, January through December, all `inactive`.
2. Duplicate creation is rejected even under concurrent requests and leaves no partial rows.
3. Months activate independently and in any order; multiple months may be active at once.
4. All nine state/operation combinations match the matrix above; retries preserve timestamps and do not duplicate audit entries.
5. This bolt supplies period states and the shared year lock. Bolt 014 must verify create/edit/delete income writes are rejected after close and serialize correctly with concurrent close.
6. Owner/Admin mutations succeed, Member/Viewer mutations are denied, and household data cannot be accessed through another household's URL.
7. State and audit entries commit or roll back together.
8. Concurrent close and income-write operations serialize on the same year root, with no write accepted after the close has committed.

## Follow-up verification owned by later bolts

- Bolt 014 proves the close/write contract for create, edit, and delete using the shared lock order `Household → AccountingYear` and forced PostgreSQL interleavings.
- Bolt 017 owns the measured P95 benchmark for period and income endpoints. The existing family-acceptance benchmark does not include accounting-period routes; until 017 runs that measurement, P95 <500 ms is unverified.
