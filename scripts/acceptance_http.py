"""Authenticated HTTPS requests for synthetic acceptance data."""

import json
import ssl
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

from acceptance_common import base_url, load_run


class ApiSession:
    """Keep one Django session, CSRF cookie and trusted local CA together."""

    def __init__(self, run_id, role):
        run_dir, manifest = load_run(run_id)
        self.base = base_url(manifest, role)
        self.cookies = CookieJar()
        context = ssl.create_default_context(cafile=run_dir / f"{role}-root.crt")
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies),
            urllib.request.HTTPSHandler(context=context),
        )
        self.csrf_token = None

    def request(self, method, path, payload=None, expected=(200,)):
        headers = {"Accept": "application/json"}
        if method not in ("GET", "HEAD"):
            headers["Origin"] = self.base
            headers["Content-Type"] = "application/json"
            if self.csrf_token:
                headers["X-CSRFToken"] = self.csrf_token
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        started = time.perf_counter()
        try:
            response = self.opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            status = response.status
        elapsed_ms = (time.perf_counter() - started) * 1000
        result = json.loads(body) if body else None
        if status not in expected:
            raise AssertionError(f"{method} {path}: HTTP {status}; {result}")
        return result, elapsed_ms, status

    def prepare_csrf(self):
        result, _, _ = self.request("GET", "/api/auth/setup/")
        self.csrf_token = result["csrf_token"]

    def login(self, username, password):
        self.prepare_csrf()
        self.request(
            "POST",
            "/api/auth/login/",
            {"username": username, "password": password},
        )
        self.prepare_csrf()
