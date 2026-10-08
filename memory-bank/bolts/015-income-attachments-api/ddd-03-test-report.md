---
unit: 002-monthly-income-api
bolt: 015-income-attachments-api
stage: test
status: pending-review
updated: '2026-10-08T20:02:48Z'
---

# Test Report — Monthly Income Attachments API

## Current result

The complete Django suite passes: **169/169 tests** on PostgreSQL. Statement coverage is **83%** across the seven explicitly listed production attachment modules. Ten assessor integrity regressions pass, and full quality checks pass. The ordered Caddy write-before-read repair passes the final **133-case** runtime manifest for both supported protocols. Stage 5 awaits independent acceptance and official completion.

The independent reviewer rejected `8650ce8` at 7.0/10, then verified the 168-test/83%-coverage checkpoint `e8280a1` at 8.4/10 with R5-3/R5-4 resolved. This revision completes the remaining matrix cells, makes the evidence assessor fail closed, and fixes the reproduced proxy response defect with independent implementation advice from `_doradca`. The final review is separate from these author verification results.

## Application verification

| Check | Result |
| --- | --- |
| Full `manage.py test --noinput` | 169 passed, 0 failed |
| Attachment-specific tests included in the full suite | 39 tests |
| Probe assessor self-tests | 10 passed, 0 failed |
| Full `scripts/quality.ps1` | Passed: Ruff 91 files, Prettier, ESLint, Stylelint, TypeScript; probe JavaScript is included |
| Production attachment statement coverage | 83%: 1003 statements, 170 missed |
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

The endpoint matrix covers foreign households and attachments including POST, cross-parent UUIDs, removed children and deleted parents, Owner/Administrator mutation rights, Viewer/Member reads, Member mutation denial, inactive/closed read access, and first-404 ordering including POST for missing/deleted parents in a closed period. The inactive fixture respects timestamp constraints; it tests the state policy without adding a deactivation API to the public state machine. Existing CSRF and bounded multipart tests remain included.

Deterministic transaction tests exercise both orders of upload versus month close and parent deletion. Upload-first tests pause inside the real database transaction and query `pg_stat_activity` with `pg_blocking_pids` to prove that the competing operation waits on the uploader's real PostgreSQL lock. Close/delete-first tests pause after real filesystem promotion and verify rejection, metadata/audit absence, and compensation of final bytes. Capacity tests prove that only one competing batch reserves the remaining capacity.

A real reconciler runs while upload is paused after promotion and before metadata commit. It must skip the uploader's held OS claim lock and preserve bytes; the resumed upload commits successfully. The promotion hook asserts that filesystem promotion runs outside a Django atomic block. Post-commit cleanup failures, audit rollback, cross-process flock, bounded reconciliation progress, missing/corrupt byte reporting, and JPEG structure regressions remain covered.

## Repeatable Caddy baseline

Run `scripts/test-attachment-proxy-smoke.ps1 -Repetitions 20` with the existing Docker network and local images. `-ConfigPath` permits a disposable candidate without modifying the repository Caddyfile. The script validates the selected configuration, records digest/version/build info and adapted JSON, uses disposable proxies and a byte-counting upstream, and retains evidence in ignored `.runtime/attachment-proxy-<id>/` directories. It cleans up only its uniquely named temporary containers.

The client uses asyncio TLS with explicit HTTP/1.1 ALPN, localhost SNI, one Host header, fixed Content-Length, and concurrent sending/receiving on one event loop. It records response phases, raw headers, scheduled send times and queued bytes. Positive responses require matching ID, byte count and SHA-256. The assessor correlates each negative response with its upstream end record and Caddy access log.

Verified baseline: Caddy **v2.10.0**, Go **go1.24.2**. Correlated baseline evidence: `.runtime/attachment-proxy-12c3a30f/`; **controls valid, 130/130 cases present, 102 passed, 28 failed**. All 28 failures were empty HTTP/1.1 200 responses in the 40 stalled/drip requests. They are historical baseline failures, not current repair results.

| Probe | Result |
| --- | --- |
| Quick 4-byte upload | Complete HTTP 200, 4/4 bytes and matching hash |
| Slow upload below 2-second deadline | Complete HTTP 200, 4/4 bytes and matching hash |
| Stalled 4-second schedule under 6-second control deadline | Complete HTTP 200, 4/4 bytes and matching hash |
| Slow drip 2.4-second schedule under 6-second control deadline | Complete HTTP 200, 4/4 bytes and matching hash |
| Stalled/drip under 2-second deadline, 20 repetitions each | 28 of 40 HTTP/1.1 requests returned empty 200 despite incomplete body; failed |
| 26 MiB + 1 byte | HTTP 413, no complete upstream body |
| Actual backend through production TLS config | HTTP/1.1 and HTTP/2 GET authentication responses pass |

The GET checks prove actual application routing and authentication only. The additional HTTP/2 POST probes exercise upload bodies through the real proxy into the byte-counting upstream; application metadata/storage behavior is exercised separately by the PostgreSQL-backed Django suite.

Upstream logs distinguish `selected_status=400` from `response_written=false`. They do **not** prove that Caddy received a 400 response. The exact-version handler sets a read deadline; it does not guarantee an HTTP error status. An empty 2xx response for an incomplete upload remains `FAIL`. A client watchdog or uncorrelated connection error is never accepted as proof of the Caddy deadline.

Exact-version references: [request body handler](https://github.com/caddyserver/caddy/blob/v2.10.0/modules/caddyhttp/requestbody/requestbody.go), [reverse proxy](https://github.com/caddyserver/caddy/blob/v2.10.0/modules/caddyhttp/reverseproxy/reverseproxy.go), [Go HTTP server](https://github.com/golang/go/blob/go1.24.2/src/net/http/server.go).

## Repair and final verification

The repository Caddyfile now uses the [ADR-009](adr-009-proxy-upload-deadlines.md) ordered API handlers: write600s, then read600s/max26MiB, then reverse proxy. The :8443 server explicitly supports h1/h2; its production adapt has no h3 and no H3 advertisement. The frontend has no API write handler. All limits are positive; no idle protection is disabled. This is a source/configuration change, not a restart or deployment of the running application.

Final evidence: `.runtime/attachment-proxy-e67e9f4a/`. The strict manifest requires **133 unique cases**: 80 stalled/drip rejections (20 each per protocol), 40 healthy H2 streams spanning their sibling's reset, eight complete controls, one exact late-write A/B control, two size rejections, and two near-boundary response rejections. Every required case has its matching upstream and access-log record. The source configuration hash ties the run to the actual repository Caddyfile.

The assessor derives the exact ID set/count from the manifest, rejects missing/duplicate/malformed client rows and missing/duplicate server records, checks configuration SHA, and recomputes outcomes without trusting client `pass` flags. Ten regressions reproduce controls-only, missing negative/oversize/protocol evidence, duplicates, malformed JSON, missing correlation, configuration tampering, and forged success flags.

The A/B probe uses identical body completion at 1.7 s and response delay 0.7 s: read2/write2 rejects the response, while read2/write6 returns complete 200 with matching ID/hash. The negative H1 case may end with a TLS record error; H2 resets the stream. An internal Caddy access-log 200 or upstream `response_written=true` for a late response is not a received final HTTP 200. Every final 2xx seen by the client for an incomplete body remains FAIL; own watchdogs and uncorrelated errors remain FAIL.

The production values are validated at 600 seconds; runtime probes scale them to 2/6 seconds to exercise the same ordering. They do not claim a ten-minute wall-clock performance measurement. A deadline prevents late reads/writes but does not guarantee handler termination or rollback. A fully received mutation may commit before the client loses its response; upload is nonidempotent and must not auto-retry. Client success requires 201 and a valid JSON results envelope. API reads/downloads share the write budget; frontend responses do not. Gunicorn's project configuration is explicitly 660 s rather than its default 30 s.

Migration check, source diff review, formatter/lint checks and final quality results are retained with this checkpoint. P95 remains assigned to bolt 017.

- [x] Full Django suite and quality checks pass
- [x] Explicit production coverage measured above 80% in aggregate
- [x] Role/tenant matrix and deterministic concurrency evidence added
- [x] Proxy incomplete-body response defect resolved on both supported protocols
- [x] Evidence assessor fails closed and its ten regression tests pass
- [ ] Independent Stage 5 acceptance
- [ ] Official bolt completion after acceptance

**Bolt 015 remains in progress pending independent Stage 5 acceptance.**
