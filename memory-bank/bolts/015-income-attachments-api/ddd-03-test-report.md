---
unit: 002-monthly-income-api
bolt: 015-income-attachments-api
stage: test
status: blocked
updated: '2026-10-08T19:23:27Z'
---

# Test Report — Monthly Income Attachments API

## Current result

The complete Django suite passes: **168/168 tests** on PostgreSQL. Statement coverage is **83%** across the seven explicitly listed production attachment modules. Full quality checks pass. Stage 5 remains blocked by a reproduced Caddy v2.10.0 response defect: a body read deadline can end an incomplete upload with an empty HTTP 200. This is a failed proxy test, not accepted upload success.

The independent reviewer rejected checkpoint `8650ce8` at 7.0/10. The added tests address the missing role/tenant endpoint matrix and deterministic PostgreSQL/filesystem interleavings. The runtime diagnosis has been corrected using exact-version source and an independent consultation with `_doradca`; the proxy repair remains a separate work item in this stage.

## Application verification

| Check | Result |
| --- | --- |
| Full `manage.py test --noinput` | 168 passed, 0 failed |
| Attachment-specific tests included in the full suite | 38 tests |
| Full `scripts/quality.ps1` | Passed: Ruff 90 files, Prettier, ESLint, Stylelint, TypeScript |
| Production attachment statement coverage | 83%: 1003 statements, 171 missed |
| Performance P95 | Assigned to acceptance bolt 017; not measured by 015 |

Coverage was measured with coverage.py 7.10.6 while executing the complete Django suite, not only the attachment tests. The source list deliberately excludes tests and probe tooling:

| Production module | Statement coverage |
| --- | --- |
| `households.attachment_serializers` | 100% |
| `households.attachment_services` | 88% |
| `households.attachment_storage` | 93% |
| `households.attachment_upload` | 82% |
| `households.attachment_validation` | 83% |
| `households.attachment_views` | 100% |
| `households.management.commands.reconcile_income_attachment_storage` | 73% |
| Aggregate | 83% |

The aggregate exceeds the 80% criterion; the command's individual 73% is disclosed rather than omitted. Additions in the shared models file are exercised by the application suite but are not included in this new-module coverage calculation.

## Security and concurrency evidence

The endpoint matrix now covers foreign households and attachments, cross-parent UUIDs, removed children and deleted parents, Owner/Administrator mutation rights, Viewer/Member reads, Member mutation denial, inactive/closed read access, and first-404 ordering before period-state conflicts. Existing CSRF and bounded multipart tests remain included.

Deterministic transaction tests exercise both orders of upload versus month close and parent deletion. Upload-first tests pause inside the real database transaction and query `pg_stat_activity` with `pg_blocking_pids` to prove that the competing operation waits on the uploader's real PostgreSQL lock. Close/delete-first tests pause after real filesystem promotion and verify rejection, metadata/audit absence, and compensation of final bytes. Capacity tests prove that only one competing batch reserves the remaining capacity.

A real reconciler runs while upload is paused after promotion and before metadata commit. It must skip the uploader's held OS claim lock and preserve bytes; the resumed upload commits successfully. The promotion hook asserts that filesystem promotion runs outside a Django atomic block. Post-commit cleanup failures, audit rollback, cross-process flock, bounded reconciliation progress, missing/corrupt byte reporting, and JPEG structure regressions remain covered.

## Repeatable Caddy baseline

Run `scripts/test-attachment-proxy-smoke.ps1 -Repetitions 2` with the existing Docker network and local images. The script validates the production Caddyfile, records image digest/version/build info and adapted JSON, uses disposable proxies and a byte-counting upstream, and retains evidence in ignored `.runtime/attachment-proxy-<id>/` directories. It cleans up only its uniquely named temporary containers.

The client uses asyncio TLS with explicit HTTP/1.1 ALPN, localhost SNI, one Host header, fixed Content-Length, and concurrent sending/receiving on one event loop. It records response phases, raw headers, scheduled send times and queued bytes. Positive responses require matching ID, byte count and SHA-256. The assessor correlates each negative response with its upstream end record and Caddy access log.

Verified baseline: Caddy **v2.10.0**, Go **go1.24.2**. Latest correlated evidence: `.runtime/attachment-proxy-76606067/`; **controls valid, 8 passed, 1 failed** across nine probes.

| Probe | Result |
| --- | --- |
| Quick 4-byte upload | Complete HTTP 200, 4/4 bytes and matching hash |
| Slow upload below 2-second deadline | Complete HTTP 200, 4/4 bytes and matching hash |
| Stalled 4-second schedule under 6-second control deadline | Complete HTTP 200, 4/4 bytes and matching hash |
| Slow drip 2.4-second schedule under 6-second control deadline | Complete HTTP 200, 4/4 bytes and matching hash |
| Stalled under 2-second deadline, two repetitions | Empty HTTP 200 once; HTTP 504 once; both terminate around 2 seconds with incomplete upstream body |
| Slow drip under 2-second deadline, two repetitions | Negative responses were rejected in this series; earlier valid controls also reproduced empty HTTP 200 |
| 26 MiB + 1 byte | HTTP 413, no complete upstream body |
| Actual backend through production TLS config | HTTP/1.1 and HTTP/2 GET authentication responses pass |

The GET checks prove protocol routing and authentication only. They are not upload timeout tests for HTTP/2. Those are required for the proxy repair.

Upstream logs distinguish `selected_status=400` from `response_written=false`. They do **not** prove that Caddy received a 400 response. The exact-version handler sets a read deadline; it does not guarantee an HTTP error status. An empty 2xx response for an incomplete upload remains `FAIL`. A client watchdog or uncorrelated connection error is never accepted as proof of the Caddy deadline.

Exact-version references: [request body handler](https://github.com/caddyserver/caddy/blob/v2.10.0/modules/caddyhttp/requestbody/requestbody.go), [reverse proxy](https://github.com/caddyserver/caddy/blob/v2.10.0/modules/caddyhttp/reverseproxy/reverseproxy.go), [Go HTTP server](https://github.com/golang/go/blob/go1.24.2/src/net/http/server.go).

## Remaining gate

The production Caddyfile is unchanged at this checkpoint. A candidate repair must preserve positive bounded timeouts, keep the upload limit, prove absence of 2xx for incomplete bodies on every supported protocol, document response-budget implications, and receive independent review. No global idle protection is disabled.

- [x] Full Django suite and quality checks pass
- [x] Explicit production coverage measured above 80% in aggregate
- [x] Role/tenant matrix and deterministic concurrency evidence added
- [ ] Proxy incomplete-body response defect resolved
- [ ] Independent Stage 5 acceptance
- [ ] Official bolt completion after acceptance

**Bolt 015 remains in progress at Stage 5.**
