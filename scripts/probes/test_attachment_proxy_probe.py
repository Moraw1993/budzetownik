"""Regression tests for missing, corrupt, and falsely positive proxy evidence."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import attachment_proxy_probe as probe


class EvidenceAssessmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        config = b"request_body {\n read_timeout 2s\n}\n"
        self.manifest = {
            "repetitions": 2,
            "protocols": ["http/1.1"],
            "response_budget": False,
            "configuration_sha256": hashlib.sha256(config).hexdigest(),
        }
        (self.directory / "probe.Caddyfile").write_bytes(config)
        self.write_json("manifest.json", self.manifest)
        self.clients = []
        self.upstream = []
        self.access = []
        for request_id, (_, kind) in probe.expected_cases(self.manifest).items():
            complete = kind == "control"
            status = 200 if complete else (413 if kind == "oversize" else 504)
            elapsed = 2 if kind == "deadline" else 0.1
            end = {
                "event": "end",
                "id": request_id,
                "complete": complete,
                "received": 4 if complete else 1,
                "declared": 4 if kind != "oversize" else 26 * 1024 * 1024 + 1,
                "sha256": hashlib.sha256(b"test").hexdigest(),
                "elapsed": elapsed,
                "response_written": complete,
            }
            self.upstream.append(end)
            self.clients.append(
                {
                    "id": request_id,
                    "status": status,
                    "body": json.dumps(end) if complete else "",
                    "response_elapsed": elapsed,
                    "alpn": "http/1.1",
                    "pass": True,
                }
            )
            self.access.append(
                {
                    "logger": "http.log.access.log0",
                    "request": {"uri": f"/api/upload?probe={request_id}"},
                    "status": status,
                    "duration": elapsed,
                }
            )

    def write_json(self, filename, value):
        (self.directory / filename).write_text(json.dumps(value), encoding="utf-8")

    def write_rows(self, filename, rows):
        (self.directory / filename).write_text(
            "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
        )

    def assess(self, clients=None, upstream=None, access=None):
        self.write_rows("client.jsonl", self.clients if clients is None else clients)
        self.write_rows("upstream.jsonl", self.upstream if upstream is None else upstream)
        self.write_rows("proxy.jsonl", self.access if access is None else access)
        return probe.assess_evidence(self.directory)

    def assert_failed(self, exit_code):
        self.assertEqual(exit_code, 1)
        summary = json.loads((self.directory / "summary.json").read_text())
        self.assertEqual(summary["status"], "FAIL")

    def test_complete_correlated_manifest_passes(self):
        self.assertEqual(self.assess(), 0)
        summary = json.loads((self.directory / "summary.json").read_text())
        self.assertEqual(summary["expected_cases"], 9)
        self.assertEqual(summary["passed"], 9)

    def test_controls_alone_cannot_pass(self):
        controls = [row for row in self.clients if row["status"] == 200]
        self.assert_failed(self.assess(clients=controls))

    def test_missing_negative_or_oversize_case_fails(self):
        for request_id in ("stalled-0", "drip-1", "oversize"):
            with self.subTest(request_id=request_id):
                rows = [row for row in self.clients if row["id"] != request_id]
                self.assert_failed(self.assess(clients=rows))

    def test_duplicate_client_or_upstream_id_fails(self):
        self.assert_failed(self.assess(clients=[*self.clients, self.clients[0]]))
        self.assert_failed(self.assess(upstream=[*self.upstream, self.upstream[0]]))

    def test_malformed_client_row_fails(self):
        self.assess()
        path = self.directory / "client.jsonl"
        path.write_text(path.read_text() + "\n{truncated", encoding="utf-8")
        self.assert_failed(probe.assess_evidence(self.directory))

    def test_missing_correlated_server_record_fails(self):
        rows = [row for row in self.upstream if row["id"] != "stalled-0"]
        self.assert_failed(self.assess(upstream=rows))
        logs = [row for row in self.access if "drip-0" not in row["request"]["uri"]]
        self.assert_failed(self.assess(access=logs))

    def test_client_pass_flag_does_not_override_empty_200(self):
        for row in self.clients:
            if row["id"] == "stalled-0":
                row["status"] = 200
                row["body"] = ""
                row["pass"] = True
        self.assert_failed(self.assess())

    def test_configuration_hash_mismatch_fails(self):
        (self.directory / "probe.Caddyfile").write_text("different configuration")
        self.assert_failed(self.assess())

    def test_manifest_protocol_without_its_evidence_fails(self):
        self.manifest["protocols"].append("h2")
        self.write_json("manifest.json", self.manifest)
        self.assert_failed(self.assess())

    def test_internal_late_200_requires_transport_rejection_and_never_wire_2xx(self):
        config = b"request_body {\n write_timeout 2s\n}\nrequest_body {\n read_timeout 2s\n}\n"
        (self.directory / "probe.Caddyfile").write_bytes(config)
        self.manifest["response_budget"] = True
        self.manifest["configuration_sha256"] = hashlib.sha256(config).hexdigest()
        self.write_json("manifest.json", self.manifest)
        late_end = {
            "event": "end",
            "id": "control-late-write",
            "complete": True,
            "received": 4,
            "declared": 4,
            "sha256": hashlib.sha256(b"test").hexdigest(),
            "elapsed": 1.7,
            "response_delay": 0.7,
            "response_written": True,
        }
        self.upstream.append(late_end)
        self.clients.append(
            {
                "id": "control-late-write",
                "status": 200,
                "body": json.dumps(late_end),
                "alpn": "http/1.1",
                "response_elapsed": 2.4,
            }
        )
        self.access.append(
            {
                "logger": "http.log.access.log0",
                "request": {"uri": "/api/upload?probe=control-late-write"},
                "status": 200,
                "duration": 2.4,
            }
        )
        self.clients.append(
            {
                "id": "near-boundary",
                "status": None,
                "body": None,
                "alpn": "http/1.1",
                "response_error": "SSLError",
                "response_elapsed": 2.4,
            }
        )
        self.upstream.append(
            {
                "event": "end",
                "id": "near-boundary",
                "complete": True,
                "received": 4,
                "declared": 4,
                "sha256": hashlib.sha256(b"test").hexdigest(),
                "elapsed": 1.7,
                "response_delay": 0.7,
                "response_written": True,
            }
        )
        self.access.append(
            {
                "logger": "http.log.access.log0",
                "request": {"uri": "/api/upload?probe=near-boundary"},
                "status": 200,
                "duration": 2.4,
            }
        )
        self.assertEqual(self.assess(), 0)
        self.clients[-1]["status"] = 200
        self.assert_failed(self.assess())


if __name__ == "__main__":
    unittest.main()
