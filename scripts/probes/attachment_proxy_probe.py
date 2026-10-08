"""Byte-counting upstream and TLS client for the attachment proxy smoke test."""

import argparse
import asyncio
import hashlib
import json
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


async def send_probe_async(host, port, request_id, schedule, declared):
    context = ssl._create_unverified_context()
    context.set_alpn_protocols(["http/1.1"])
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(host, port, ssl=context, server_hostname="localhost"),
        timeout=12,
    )
    headers = (
        f"POST /api/upload?probe={request_id} HTTP/1.1\r\n"
        f"Host: localhost:{port}\r\nContent-Length: {declared}\r\n"
        f"X-Test-Id: {request_id}\r\nConnection: close\r\n\r\n"
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

    receiver = asyncio.create_task(receive())
    try:
        for at_seconds, data in schedule:
            remaining = at_seconds - (time.monotonic() - started)
            if remaining > 0:
                with suppress(TimeoutError):
                    await asyncio.wait_for(final_headers.wait(), timeout=remaining)
            if final_headers.is_set():
                result["sender_stopped_after_final_headers"] = True
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


def send_probe(host, port, request_id, schedule, declared):
    return asyncio.run(send_probe_async(host, port, request_id, schedule, declared))


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
            result["pass"] = (
                status is not None
                and not 200 <= status < 300
                and 1.5 <= result["response_elapsed"] < 3
            )
            if status is not None and 200 <= status < 300:
                result["failure"] = "unexpected_2xx_after_deadline"
            elif status is None:
                result["failure"] = "connection_error_requires_correlated_server_evidence"
            results.append(result)

    length = 26 * 1024 * 1024 + 1
    oversize = send_probe(host, 8443, "oversize", [(0, b"x" * length)], length)
    oversize["pass"] = oversize["status"] == 413
    results.append(oversize)
    for result in results:
        print(json.dumps(result), flush=True)
    return 0 if all(result["pass"] for result in results) else 1


def read_json_lines(path):
    values = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        with suppress(ValueError):
            values.append(json.loads(line))
    return values


def assess_evidence(directory):
    results = read_json_lines(directory / "client.jsonl")
    upstream = {
        row["id"]: row
        for row in read_json_lines(directory / "upstream.jsonl")
        if row.get("event") == "end"
    }
    access = {
        row["request"]["uri"].split("probe=", 1)[1]: row
        for row in read_json_lines(directory / "proxy.jsonl")
        if "probe=" in row.get("request", {}).get("uri", "")
    }
    controls = {"quick", "slow-under", "control-stalled", "control-drip"}
    controls_valid = (
        all(
            validate_complete(result)
            and upstream.get(result["id"], {}).get("complete") is True
            and upstream[result["id"]]["received"] == 4
            for result in results
            if result["id"] in controls
        )
        and {result["id"] for result in results if result["id"] in controls} == controls
    )
    for result in results:
        request_id = result["id"]
        end = upstream.get(request_id, {})
        log = access.get(request_id, {})
        if request_id.startswith(("stalled-", "drip-")):
            result["correlated_deadline"] = (
                end.get("complete") is False
                and end.get("received", 4) < 4
                and 1.5 <= end.get("elapsed", 0) < 3.5
                and 1.5 <= log.get("duration", 0) < 3.5
            )
            result["pass"] = bool(result["pass"] and result["correlated_deadline"])
        if request_id == "oversize":
            result["pass"] = result["pass"] and end.get("complete") is False
    summary = {
        "controls_valid": controls_valid,
        "passed": sum(bool(result["pass"]) for result in results),
        "failed": sum(not result["pass"] for result in results),
        "results": results,
    }
    (directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}))
    return 0 if controls_valid and results and summary["failed"] == 0 else 1


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
