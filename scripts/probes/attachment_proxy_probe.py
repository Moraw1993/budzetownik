"""Byte-counting upstream and TLS client for the attachment proxy smoke test."""

import argparse
import asyncio
import hashlib
import json
import math
import os
import ssl
import time
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class ProbeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        request_id = self.headers.get("X-Test-Id", "unknown")
        declared = int(self.headers.get("Content-Length", "0"))
        received = 0
        digest = hashlib.sha256()
        started = time.monotonic()
        error = None
        self.connection.settimeout(12)
        print(json.dumps({"event": "start", "id": request_id, "declared": declared}), flush=True)
        try:
            while received < declared:
                chunk = self.rfile.read1(min(65536, declared - received))
                if not chunk:
                    break
                received += len(chunk)
                digest.update(chunk)
        except OSError as exc:
            error = type(exc).__name__
        complete = declared == received
        status = 200 if complete else 400
        result = {
            "event": "end",
            "id": request_id,
            "declared": declared,
            "received": received,
            "complete": complete,
            "sha256": digest.hexdigest(),
            "read_error": error,
            "elapsed": round(time.monotonic() - started, 3),
            "selected_status": status,
        }
        response_delay = float(self.headers.get("X-Response-Delay", "0"))
        if response_delay:
            time.sleep(response_delay)
        result["response_delay"] = response_delay
        body = json.dumps(result).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
            result["response_written"] = True
        except OSError:
            result["response_written"] = False
        print(json.dumps(result), flush=True)
        self.close_connection = True

    def log_message(self, *_args):
        pass


async def send_probe_async(host, port, request_id, schedule, declared, response_delay=0):
    context = ssl._create_unverified_context()
    context.set_alpn_protocols(["http/1.1"])
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(host, port, ssl=context, server_hostname="localhost"),
        timeout=12,
    )
    headers = (
        f"POST /api/upload?probe={request_id} HTTP/1.1\r\n"
        f"Host: localhost:{port}\r\nContent-Length: {declared}\r\n"
        f"X-Test-Id: {request_id}\r\nX-Response-Delay: {response_delay}\r\n"
        "Connection: close\r\n\r\n"
    )
    writer.write(headers.encode())
    await writer.drain()
    started = time.monotonic()
    result = {
        "id": request_id,
        "port": port,
        "status": None,
        "body": None,
        "alpn": writer.get_extra_info("ssl_object").selected_alpn_protocol(),
        "queued_bytes": 0,
        "send_times": [],
    }
    final_headers = asyncio.Event()

    async def receive():
        try:
            first_byte = await reader.readexactly(1)
            result["first_response_elapsed"] = round(time.monotonic() - started, 3)
            response_headers = first_byte + await reader.readuntil(b"\r\n\r\n")
            lines = response_headers.decode("iso-8859-1").split("\r\n")
            result["status"] = int(lines[0].split(" ")[1])
            if result["status"] < 200:
                raise ValueError("Unexpected interim response without an Expect header")
            result["headers_elapsed"] = round(time.monotonic() - started, 3)
            result["response_headers"] = lines
            final_headers.set()
            fields = dict(
                (name.strip().lower(), value.strip())
                for name, value in (line.split(":", 1) for line in lines[1:] if ":" in line)
            )
            if "content-length" in fields:
                body = await reader.readexactly(int(fields["content-length"]))
            elif fields.get("transfer-encoding") == "chunked":
                body = b""
                while True:
                    size = int((await reader.readline()).split(b";", 1)[0].strip(), 16)
                    if size == 0:
                        while True:
                            trailer = await reader.readline()
                            if trailer in {b"\r\n", b""}:
                                break
                        break
                    body += await reader.readexactly(size)
                    await reader.readexactly(2)
            else:
                body = await reader.read()
            result["body"] = body.decode(errors="replace")
        except (OSError, ValueError, asyncio.IncompleteReadError) as exc:
            result["response_error"] = type(exc).__name__
            result["response_error_detail"] = str(exc)
        finally:
            result["response_elapsed"] = round(time.monotonic() - started, 3)
            final_headers.set()

    receiver = asyncio.create_task(receive())
    try:
        for at_seconds, data in schedule:
            remaining = at_seconds - (time.monotonic() - started)
            if remaining > 0:
                with suppress(TimeoutError):
                    await asyncio.wait_for(final_headers.wait(), timeout=remaining)
            if final_headers.is_set():
                result["sender_stopped_after_response_or_rejection"] = True
                break
            try:
                for offset in range(0, len(data), 65536):
                    if final_headers.is_set():
                        break
                    chunk = data[offset : offset + 65536]
                    writer.write(chunk)
                    result["queued_bytes"] += len(chunk)
                    result["send_times"].append(round(time.monotonic() - started, 3))
                    await writer.drain()
                    await asyncio.sleep(0)
            except OSError as exc:
                result["send_error"] = type(exc).__name__
                result["send_error_detail"] = str(exc)
                break
        await asyncio.wait_for(receiver, timeout=13)
    except TimeoutError:
        result["response_error"] = "probe_receiver_did_not_finish"
    finally:
        writer.close()
        with suppress(OSError):
            await writer.wait_closed()
    return result


def send_probe(host, port, request_id, schedule, declared, response_delay=0):
    return asyncio.run(send_probe_async(host, port, request_id, schedule, declared, response_delay))


def validate_complete(result, expected=b"test"):
    try:
        body = json.loads(result.get("body") or "{}")
    except ValueError:
        return False
    return (
        result["status"] == 200
        and body.get("id") == result["id"]
        and body.get("complete") is True
        and body.get("received") == len(expected)
        and body.get("sha256") == hashlib.sha256(expected).hexdigest()
    )


def run_client(repetitions):
    host = os.environ["PROXY_HOST"]
    results = []
    for name, schedule in (
        ("quick", [(0, b"test")]),
        ("slow-under", [(0, b"t"), (0.15, b"e"), (0.3, b"s"), (0.45, b"t")]),
    ):
        result = send_probe(host, 8443, name, schedule, 4)
        result["pass"] = validate_complete(result)
        results.append(result)

    schedules = {
        "stalled": [(0, b"t"), (4, b"est")],
        "drip": [(0, b"t"), (0.8, b"e"), (1.6, b"s"), (2.4, b"t")],
    }
    for name, schedule in schedules.items():
        control = send_probe(host, 8444, f"control-{name}", schedule, 4)
        control["pass"] = validate_complete(control)
        results.append(control)
        for number in range(repetitions):
            result = send_probe(host, 8443, f"{name}-{number}", schedule, 4)
            status = result["status"]
            transport_rejection = status is None and result.get("response_error") in {
                "IncompleteReadError",
                "ConnectionResetError",
                "SSLError",
            }
            result["pass"] = (
                (status is not None and not 200 <= status < 300) or transport_rejection
            ) and 1.5 <= result["response_elapsed"] < 3
            if status is not None and 200 <= status < 300:
                result["failure"] = "unexpected_2xx_after_deadline"
            elif status is None:
                result["classification"] = "transport_rejection_requires_server_evidence"
            results.append(result)

    length = 26 * 1024 * 1024 + 1
    oversize = send_probe(host, 8443, "oversize", [(0, b"x" * length)], length)
    oversize["pass"] = oversize["status"] == 413
    results.append(oversize)
    if os.environ.get("REQUIRE_RESPONSE_BUDGET") == "1":
        late_control = send_probe(
            host, 8445, "control-late-write", [(0, b"t"), (1.7, b"est")], 4, 0.7
        )
        late_control["pass"] = validate_complete(late_control)
        results.append(late_control)
        boundary = send_probe(host, 8443, "near-boundary", [(0, b"t"), (1.7, b"est")], 4, 0.7)
        boundary["pass"] = (
            boundary["status"] is None
            and boundary.get("response_error")
            in {"IncompleteReadError", "ConnectionResetError", "SSLError"}
            and 1.5 <= boundary["response_elapsed"] < 3.5
        )
        results.append(boundary)
    for result in results:
        print(json.dumps(result), flush=True)
    return 0 if all(result["pass"] for result in results) else 1


def read_json_lines(path, *, strict=False):
    values = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            values.append(json.loads(line))
        except ValueError as exc:
            if strict:
                raise ValueError(f"Malformed JSON in {path.name}:{number}") from exc
    return values


def expected_cases(manifest):
    repetitions = manifest["repetitions"]
    protocols = manifest["protocols"]
    if (
        type(repetitions) is not int
        or not 1 <= repetitions <= 20
        or not isinstance(protocols, list)
        or not protocols
        or len(protocols) != len(set(protocols))
        or not set(protocols) <= {"http/1.1", "h2"}
        or type(manifest["response_budget"]) is not bool
        or len(manifest["configuration_sha256"]) != 64
    ):
        raise ValueError("Invalid probe manifest")
    cases = {}
    for protocol in protocols:
        prefix = "h2-" if protocol == "h2" else ""
        for name in ("quick", "slow-under", "control-stalled", "control-drip"):
            cases[prefix + name] = (protocol, "control")
        cases[prefix + "oversize"] = (protocol, "oversize")
        for name in ("stalled", "drip"):
            for number in range(repetitions):
                request_id = f"{prefix}{name}-{number}"
                cases[request_id] = (protocol, "deadline")
                if protocol == "h2":
                    cases[request_id + "-healthy-stream"] = (protocol, "healthy")
        if manifest["response_budget"]:
            cases[prefix + "near-boundary"] = (protocol, "boundary")
            if protocol == "http/1.1":
                cases["control-late-write"] = (protocol, "late-control")
    return cases


def transport_rejection(result, protocol):
    if result.get("local_watchdog") or result["status"] is not None:
        return False
    if protocol == "h2":
        return isinstance(result.get("rst_code"), int) and result["rst_code"] != 0
    return result.get("response_error") in {
        "IncompleteReadError",
        "ConnectionResetError",
        "SSLError",
    }


def assess_case(result, case, end, log):
    protocol, kind = case
    if not end or not log:
        return False
    if kind in {"control", "healthy", "late-control"}:
        complete = (
            validate_complete(result)
            and end.get("complete") is True
            and end.get("received") == 4
            and end.get("sha256") == hashlib.sha256(b"test").hexdigest()
            and log.get("status") == 200
        )
        if kind == "late-control":
            return (
                complete
                and 1.5 <= end.get("elapsed", 0) < 2
                and end.get("elapsed", 0) + end.get("response_delay", 0) >= 2
                and 2 <= result["response_elapsed"] < 3.5
            )
        return complete
    if kind == "oversize":
        return (
            result["status"] == 413
            and log.get("status") == 413
            and end.get("complete") is False
            and end.get("received", 0) < end.get("declared", 0)
        )
    rejected = (
        result["status"] is not None and not 200 <= result["status"] < 300
    ) or transport_rejection(result, protocol)
    if kind == "boundary":
        return (
            rejected
            and 1.5 <= result["response_elapsed"] < 3.5
            and end.get("complete") is True
            and end.get("received") == 4
            and end.get("sha256") == hashlib.sha256(b"test").hexdigest()
            and 1.5 <= end.get("elapsed", 0) < 2
            and end.get("elapsed", 0) + end.get("response_delay", 0) >= 2
            and 1.5 <= log.get("duration", 0) < 3.5
        )
    correlated = (
        end.get("complete") is False
        and end.get("received", 4) < 4
        and 1.5 <= end.get("elapsed", 0) < 3.5
        and 1.5 <= log.get("duration", 0) < 3.5
    )
    result["correlated_deadline"] = correlated
    return rejected and 1.5 <= result["response_elapsed"] < 3 and correlated


def valid_result(row, protocol):
    return (
        isinstance(row, dict)
        and isinstance(row.get("id"), str)
        and "status" in row
        and (row["status"] is None or (type(row["status"]) is int and 100 <= row["status"] <= 599))
        and "body" in row
        and (row["body"] is None or isinstance(row["body"], str))
        and type(row.get("response_elapsed")) in {int, float}
        and math.isfinite(row["response_elapsed"])
        and row["response_elapsed"] >= 0
        and row.get("alpn") == protocol
    )


def index_unique(rows, key, errors, label):
    indexed = {}
    for row in rows:
        request_id = key(row)
        if request_id in indexed:
            errors.append(f"Duplicate {label} ID: {request_id}")
        indexed[request_id] = row
    return indexed


def assess_evidence(directory):
    errors = []
    results = []
    cases = {}
    upstream = {}
    access = {}
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8-sig"))
        cases = expected_cases(manifest)
        config_bytes = (directory / "probe.Caddyfile").read_bytes()
        if hashlib.sha256(config_bytes).hexdigest() != manifest["configuration_sha256"]:
            raise ValueError("Probe configuration does not match its manifest hash")
        if (b"write_timeout 2s" in config_bytes) != manifest["response_budget"]:
            raise ValueError("Response budget differs from the probe configuration")
        for protocol in manifest["protocols"]:
            filename = "client-h2.jsonl" if protocol == "h2" else "client.jsonl"
            rows = read_json_lines(directory / filename, strict=True)
            if not all(valid_result(row, protocol) for row in rows):
                raise ValueError(f"Invalid result schema in {filename}")
            results.extend(rows)
        indexed = index_unique(results, lambda row: row["id"], errors, "client")
        if set(indexed) != set(cases):
            errors.append(
                f"Case set mismatch: missing={sorted(set(cases) - set(indexed))}; "
                f"unexpected={sorted(set(indexed) - set(cases))}"
            )
        upstream = index_unique(
            [
                row
                for row in read_json_lines(directory / "upstream.jsonl")
                if isinstance(row, dict) and row.get("event") == "end"
            ],
            lambda row: row["id"],
            errors,
            "upstream",
        )
        access = index_unique(
            [
                row
                for row in read_json_lines(directory / "proxy.jsonl")
                if isinstance(row, dict)
                and "http.log.access" in row.get("logger", "")
                and "probe=" in row.get("request", {}).get("uri", "")
            ],
            lambda row: row["request"]["uri"].split("probe=", 1)[1],
            errors,
            "access log",
        )
        for label, records in (("upstream", upstream), ("access log", access)):
            if set(records) != set(cases):
                errors.append(f"{label} case set differs from manifest")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    for result in results:
        request_id = result["id"]
        result["pass"] = request_id in cases and bool(
            assess_case(
                result, cases[request_id], upstream.get(request_id, {}), access.get(request_id, {})
            )
        )
        if request_id.endswith("-healthy-stream"):
            sibling = next(
                (row for row in results if row["id"] == request_id.removesuffix("-healthy-stream")),
                {},
            )
            result["pass"] = result["pass"] and (
                result.get("relative_start", float("inf"))
                < sibling.get("response_elapsed", 0)
                < result.get("relative_end", 0)
            )
    controls = {
        request_id for request_id, case in cases.items() if case[1] in {"control", "late-control"}
    }
    controls_valid = (
        bool(controls)
        and {result["id"] for result in results if result["pass"] and result["id"] in controls}
        == controls
    )
    summary = {
        "controls_valid": controls_valid,
        "expected_cases": len(cases),
        "observed_cases": len(results),
        "evidence_errors": errors,
        "passed": sum(bool(result["pass"]) for result in results),
        "failed": sum(not result["pass"] for result in results),
        "results": results,
    }
    summary["status"] = (
        "PASS" if not errors and controls_valid and results and summary["failed"] == 0 else "FAIL"
    )
    (directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}))
    return 0 if summary["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["server", "client", "assess"])
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--evidence-directory", type=Path)
    args = parser.parse_args()
    if args.mode == "server":
        ThreadingHTTPServer(("0.0.0.0", 8001), ProbeHandler).serve_forever()
        return 0
    if args.mode == "assess":
        return assess_evidence(args.evidence_directory)
    return run_client(args.repetitions)


if __name__ == "__main__":
    raise SystemExit(main())
