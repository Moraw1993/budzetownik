---
unit: 001-periods-api
bolt: 013-periods-api
stage: technical-design
status: complete
created: '2026-10-07T10:11:57Z'
updated: '2026-10-07T10:14:45Z'
---

# Technical Design — 013-periods-api

## Scope and constraints

This bolt implements accounting years and the lifecycle of their twelve accounting months. It does not create income records or income sources. The next bolt, `014-monthly-income-api`, will use the month state as a write guard.

The design follows the existing modular-monolith architecture and the accepted household-access and immutable-audit decisions. Exact serializer/error-envelope conventions and the project's identifier type will be reconciled with the implementation in Stage 4, before source changes.

## Component design

The request path is:

`DRF route/view → application use case → AccountingYear aggregate/repository → PostgreSQL`

The API layer validates request shape, establishes the authenticated actor, applies household membership and role policy, and maps application outcomes to HTTP responses. Use cases coordinate transactions, locking, aggregate rules, and the existing financial audit writer. The aggregate enforces the twelve-month structure and legal state transitions. Repository queries always scope by household. No Django signals or external event store are introduced.

## API contract

All routes are household-scoped, consistent with ADR-002. Names and payloads below are the proposed public contract; response envelope details must match the established API convention discovered during implementation.

| Method and route | Access | Behavior |
| --- | --- | --- |
| `GET /api/households/{household_id}/accounting-years/` | Household member | List years for the household, newest calendar year first. |
| `POST /api/households/{household_id}/accounting-years/` | Owner/Admin | Accept `{ "calendar_year": 2027 }`; atomically create the year and its twelve inactive months; return `201` with the year and ordered months. |
| `GET /api/households/{household_id}/accounting-years/{year_id}/months/` | Household member | Return January through December with month id, number, state, calendar start/end, and latest transition timestamps. |
| `POST /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/activate` | Owner/Admin | Apply `inactive → active`. |
| `POST /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/close` | Owner/Admin | Apply `active → closed`. |
| `POST /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/reopen` | Owner/Admin | Apply `closed → active`. |

Named transition operations prevent callers from assigning arbitrary lifecycle states. Every operation verifies that the year and month belong to the household in the URL. Income CRUD routes are explicitly out of scope.

## Persistence design

The proposed relational model uses two tables, subject to matching project-wide identifier conventions in Stage 4:

| Table | Fields and constraints |
| --- | --- |
| `AccountingYear` | `id`, `household_id` FK, `calendar_year`, `created_at`; unique `(household_id, calendar_year)`; calendar year range `1..9999` so every value is representable by the calendar date domain. |
| `AccountingMonth` | `id`, `accounting_year_id` FK, `month_number`, `state`, `activated_at`, `closed_at`, `created_at`, `updated_at`; unique `(accounting_year_id, month_number)`; check `month_number` between 1 and 12; state restricted to `inactive`, `active`, or `closed`. |

The unique year constraint supports household year listing and duplicate prevention. The month constraint supports ordered month access. Create the year and all twelve month rows in one database transaction, with month number derived from 1 through 12 and initial state `inactive`. Do not publish or return success if fewer than twelve rows were persisted. A repeated create for the same household/year returns conflict.

The month timestamps represent the most recent activation and close; immutable audit records retain the full transition history. On reopen, update `activated_at`; retain `closed_at` as the last close time. The exact timestamp nullability/semantics should be implemented consistently and documented in the model migration.

## State transitions and idempotency

| Current state | Operation | Result |
| --- | --- | --- |
| `inactive` | activate | `active`, append one activation audit entry |
| `active` | close | `closed`, append one close audit entry |
| `closed` | reopen | `active`, append one reopen audit entry |

Repeating an operation when the month is already in that operation's target state is idempotent: return the current representation and do not append another audit event. Other invalid transitions return `409 Conflict` with a stable domain error code. In particular, a closed month is reopened through the explicit `reopen` operation before further edits; it cannot be activated directly.

## Authorization and tenant isolation

- Preserve the existing authenticated session and CSRF protections for state-changing requests.
- Household members may read years and months. Only Owner and Admin may create years or change month state; Member and Viewer receive `403` on writes.
- Resolve each object through the household-scoped query, not by loading a global id and trusting a later check. Missing and cross-household objects both return `404` to avoid disclosing another household's records.
- For writes, lock the aggregate root first and re-check current household membership and role after acquiring the lock, including after any lock wait, as specified by ADR-002.
- Do not accept household, actor, role, or audit identity from the request body.

## Transactions and concurrency

Year creation runs in `transaction.atomic()`. Database uniqueness is the final guard against concurrent duplicate creates; translate the losing insert to `409 Conflict`, with the transaction rolled back so no partial months remain.

State changes lock the `AccountingYear` row with `select_for_update()`, then re-check membership/role, resolve the month within that locked year, verify its state, persist the transition, and append the immutable audit record in the same transaction. Locking the year (rather than only one month) gives the future income writer a shared synchronization point.

Bolt `014-monthly-income-api` must acquire the same year lock before checking that a month is active and before persisting an income change, keeping the state check and income write in the same transaction. Therefore close-versus-income races serialize: whichever transaction obtains the root lock first determines whether the income write precedes the close or is rejected after it. This deliberately serializes writes within one household-year; transactions must remain short and database-only. Validate the target API latency of P95 below 500 ms under representative household load.

## Audit integration

Append the transition to the existing immutable financial audit mechanism in the same database transaction as the period change, following ADR-004. Record only whitelisted fields: household, actor, accounting year/month identity, action, transition timestamp, and before/after state. Do not duplicate audit infrastructure, persist sensitive request payloads, or use signals that could separate the audit outcome from transaction success.

Year creation should also use the existing audit mechanism if its established policy treats structural financial setup as auditable; Stage 4 must verify the current audit action taxonomy and record the year creation atomically. No standalone event store is introduced.

## HTTP error mapping

| Condition | HTTP status |
| --- | --- |
| Malformed payload or invalid calendar year | `400 Bad Request` |
| Unauthenticated request | `401 Unauthorized` |
| Authenticated non-writer attempting a mutation | `403 Forbidden` |
| Missing year/month or object outside the URL household | `404 Not Found` |
| Duplicate year or invalid lifecycle transition | `409 Conflict` |

Error body shape and stable code naming must follow the existing API conventions, which will be confirmed during Stage 4. Do not introduce a new global response envelope for this bolt.

## Reliability and performance

- PostgreSQL is the source of truth; year creation, transitions, and audit writes are transactional.
- Enforce year/month uniqueness and month-number/state domains in the database as well as in application logic.
- Retrieve the twelve months in one ordered query; avoid N+1 access. Paginate the year list if consistent with the existing API convention and expected growth.
- Keep aggregate locks limited to the mutation transaction and avoid network or file operations while holding them.
- Target P95 below 500 ms for year listing, month listing, creation, and lifecycle operations under representative load.

## Verification design

The implementation and tests must demonstrate:

1. A newly created year has exactly twelve uniquely numbered months, January through December, all `inactive`.
2. Duplicate creation is rejected even under concurrent requests and leaves no partial rows.
3. Months activate independently and in any order; multiple months may be active at once.
4. Only the three defined transitions succeed; retries are idempotent and do not duplicate audit entries.
5. Closing blocks future income writes once bolt 014 uses the shared year lock; reopening restores eligibility. Add a cross-bolt contract test with bolt 014 or an agreed integration test when that bolt is implemented.
6. Owner/Admin mutations succeed, Member/Viewer mutations are denied, and household data cannot be accessed through another household's URL.
7. State and audit entries commit or roll back together.
8. Concurrent close and income-write operations serialize on the same year root, with no write accepted after the close has committed.

## Open implementation checks

- Confirm identifier field type, model naming, route registration, serializer conventions, and API error envelope against the current code in Stage 4.
- Confirm whether year-creation audit is required by the existing audit taxonomy and use its approved action name.
- Confirm precise timestamp update semantics in model tests and API documentation.
