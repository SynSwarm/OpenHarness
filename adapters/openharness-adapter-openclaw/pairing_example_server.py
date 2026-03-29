"""
Example pairing + device token gateway using SQLite (stdlib only).

This is a **reference implementation** for operators who deploy beside OpenClaw.
You are **not** required to run this in production inside the OpenHarness repo —
fork, replace with your own service, or graduate to a separate repository when
your account/device needs grow.

See README: "Example pairing gateway" and docs/guides/device-pairing-session.md
"""
from __future__ import annotations

import json
import secrets
import sqlite3
import string
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

_ALPHANUM = string.ascii_uppercase + string.digits


def _now() -> float:
    return time.time()


def _generate_code(length: int = 8) -> str:
    return "".join(secrets.choice(_ALPHANUM) for _ in range(length))


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS pending (
            code TEXT PRIMARY KEY,
            pairing_id TEXT NOT NULL,
            expires_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS devices (
            access_token TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            credential_ref TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        """
    )
    return conn


def _prune_expired(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM pending WHERE expires_at < ?", (_now(),))


class PairingExampleHandler(BaseHTTPRequestHandler):
    db_path: Path = Path(".openharness-pair-example.sqlite3")
    pair_ttl_sec: int = 300
    pair_create_path: str = "/pair/create"
    pair_confirm_path: str = "/pair/confirm"
    health_paths: frozenset[str] = frozenset({"/", "/health", "/pair/health"})
    confirm_secret: str | None = None

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def _json(self, code: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        data = self.rfile.read(length)
        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _conn(self) -> sqlite3.Connection:
        return init_db(self.db_path)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0].rstrip("/") in self.health_paths:
            self._json(
                200,
                {
                    "status": "ok",
                    "service": "openharness-pairing-example",
                    "note": "reference example; not a normative requirement",
                },
            )
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == self.pair_create_path:
            self._handle_pair_create()
        elif path == self.pair_confirm_path:
            self._handle_pair_confirm()
        else:
            self._json(404, {"error": "not_found", "message": path})

    def _handle_pair_create(self) -> None:
        conn = self._conn()
        try:
            _prune_expired(conn)
            for _ in range(20):
                code = _generate_code(8)
                cur = conn.execute("SELECT 1 FROM pending WHERE code = ?", (code,))
                if cur.fetchone() is None:
                    break
            else:
                self._json(500, {"error": "could_not_allocate_code"})
                return
            pairing_id = f"p_{uuid4().hex[:12]}"
            exp = _now() + self.pair_ttl_sec
            conn.execute(
                "INSERT INTO pending (code, pairing_id, expires_at) VALUES (?, ?, ?)",
                (code, pairing_id, exp),
            )
        finally:
            conn.close()
        self._json(
            200,
            {
                "code": code,
                "pairing_id": pairing_id,
                "expires_at": int(exp),
                "expires_in_sec": self.pair_ttl_sec,
            },
        )

    def _handle_pair_confirm(self) -> None:
        body = self._read_json()
        if body is None:
            self._json(400, {"error": "invalid_json"})
            return
        code = (body.get("code") or "").strip().upper()
        tenant_id = (body.get("tenant_id") or "").strip()
        if not code or not tenant_id:
            self._json(400, {"error": "missing_fields", "need": ["code", "tenant_id"]})
            return

        if self.confirm_secret:
            secret = body.get("confirm_secret") or self.headers.get("X-Pairing-Confirm", "")
            if secret != self.confirm_secret:
                self._json(403, {"error": "forbidden", "hint": "confirm_secret or X-Pairing-Confirm header"})
                return

        conn = self._conn()
        try:
            _prune_expired(conn)
            cur = conn.execute(
                "SELECT pairing_id, expires_at FROM pending WHERE code = ?",
                (code,),
            )
            row = cur.fetchone()
            if not row or row[1] < _now():
                self._json(400, {"error": "invalid_or_expired_code"})
                return
            conn.execute("DELETE FROM pending WHERE code = ?", (code,))

            access_token = f"demo_{uuid4().hex}"
            session_id = f"sess_{uuid4().hex[:16]}"
            credential_ref = f"cred_demo_{uuid4().hex[:12]}"
            device_id = f"dev_{uuid4().hex[:12]}"

            conn.execute(
                """INSERT INTO devices (access_token, tenant_id, session_id, credential_ref, device_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (access_token, tenant_id, session_id, credential_ref, device_id, _now()),
            )
        finally:
            conn.close()

        self._json(
            200,
            {
                "access_token": access_token,
                "session_id": session_id,
                "credential_ref": credential_ref,
                "device_id": device_id,
                "tenant_id": tenant_id,
            },
        )


def run_pair_server(
    host: str,
    port: int,
    db_path: Path,
    pair_ttl_sec: int,
    confirm_secret: str | None,
) -> None:
    PairingExampleHandler.db_path = db_path
    PairingExampleHandler.pair_ttl_sec = pair_ttl_sec
    PairingExampleHandler.confirm_secret = confirm_secret or None
    init_db(db_path)
    httpd = HTTPServer((host, port), PairingExampleHandler)
    sec = f"confirm secret: {confirm_secret[:4]}…" if confirm_secret else "confirm secret: (none)"
    print(
        f"Pairing EXAMPLE (SQLite) on http://{host}:{port}/\n"
        f"  POST {PairingExampleHandler.pair_create_path}\n"
        f"  POST {PairingExampleHandler.pair_confirm_path}\n"
        f"DB: {db_path.resolve()}\n"
        f"{sec}\n"
        "This is a reference — you may replace with your own gateway.",
        file=sys.stderr,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


def _http_json(method: str, url: str, body: dict[str, Any] | None, headers: dict[str, str]) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    h = {"Content-Type": "application/json", **headers}
    req = Request(url, data=data, method=method, headers=h)
    try:
        with urlopen(req, timeout=30.0) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            return e.code, json.loads(raw) if raw else {"error": str(e.reason)}
        except json.JSONDecodeError:
            return e.code, raw
    except URLError as e:
        return 0, {"error": str(e.reason)}


def cmd_pair_create(base_url: str) -> int:
    base = base_url.rstrip("/")
    url = f"{base}/pair/create"
    code, payload = _http_json("POST", url, {}, {})
    if code != 200 or not isinstance(payload, dict):
        print(f"pair-create failed: HTTP {code} {payload}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nShow on TV: {payload.get('code', '?')}", file=sys.stderr)
    return 0


def cmd_pair_confirm(
    base_url: str,
    code: str,
    tenant_id: str,
    confirm_secret: str | None,
) -> int:
    base = base_url.rstrip("/")
    url = f"{base}/pair/confirm"
    body: dict[str, Any] = {"code": code.strip().upper(), "tenant_id": tenant_id}
    if confirm_secret:
        body["confirm_secret"] = confirm_secret
    headers: dict[str, str] = {}
    if confirm_secret:
        headers["X-Pairing-Confirm"] = confirm_secret
    status, payload = _http_json("POST", url, body, headers)
    if status != 200 or not isinstance(payload, dict):
        print(f"pair-confirm failed: HTTP {status} {payload}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(
        "\nexport OPENHARNESS_DEMO_TOKEN=" + payload.get("access_token", ""),
        "\nexport OPENHARNESS_DEMO_SESSION_ID=" + payload.get("session_id", ""),
        file=sys.stderr,
    )
    return 0
