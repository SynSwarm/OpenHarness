"""
Reference pairing + mock Harness demo (stdlib HTTP only).

NOT FOR PRODUCTION — no real crypto, file-backed store, single-process demo.
See docs/guides/device-pairing-session.md for product-level guidance.
"""
from __future__ import annotations

import json
import secrets
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


def _load_store(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"pending": {}, "tokens": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"pending": {}, "tokens": {}}


def _save_store(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _prune_pending(store: dict[str, Any]) -> None:
    pending = store.get("pending") or {}
    now = _now()
    dead = [c for c, v in pending.items() if float(v.get("expires_at", 0)) < now]
    for c in dead:
        del pending[c]


class PairingDemoHandler(BaseHTTPRequestHandler):
    store_path: Path = Path(".openharness-demo-store.json")
    pair_ttl_sec: int = 300
    harness_path: str = "/demo/harness"
    pair_create_path: str = "/demo/pair/create"
    pair_confirm_path: str = "/demo/pair/confirm"

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

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == self.pair_create_path:
            self._handle_pair_create()
        elif path == self.pair_confirm_path:
            self._handle_pair_confirm()
        elif path == self.harness_path:
            self._handle_harness()
        else:
            self._json(404, {"error": "not_found", "message": path})

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") in ("", "/demo", "/demo/health"):
            self._json(200, {"status": "ok", "service": "openharness-pairing-demo"})
            return
        self._json(404, {"error": "not_found"})

    def _handle_pair_create(self) -> None:
        store = _load_store(self.store_path)
        _prune_pending(store)
        pending = store.setdefault("pending", {})
        for _ in range(20):
            code = _generate_code(8)
            if code not in pending:
                break
        else:
            self._json(500, {"error": "could_not_allocate_code"})
            return
        pairing_id = f"p_{uuid4().hex[:12]}"
        exp = _now() + self.pair_ttl_sec
        store.setdefault("pending", {})[code] = {
            "pairing_id": pairing_id,
            "expires_at": exp,
        }
        _save_store(self.store_path, store)
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

        store = _load_store(self.store_path)
        _prune_pending(store)
        pending = store.get("pending") or {}
        entry = pending.get(code)
        if not entry:
            self._json(400, {"error": "invalid_or_expired_code"})
            return

        del pending[code]
        access_token = f"demo_{uuid4().hex}"
        session_id = f"sess_{uuid4().hex[:16]}"
        credential_ref = f"cred_demo_{uuid4().hex[:12]}"
        device_id = f"dev_{uuid4().hex[:12]}"

        store.setdefault("tokens", {})[access_token] = {
            "tenant_id": tenant_id,
            "session_id": session_id,
            "credential_ref": credential_ref,
            "device_id": device_id,
            "paired_at": _now(),
        }
        _save_store(self.store_path, store)

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

    def _handle_harness(self) -> None:
        auth = self.headers.get("Authorization", "")
        token = None
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
        if not token:
            self._json(401, {"error": "unauthorized", "hint": "Authorization: Bearer <token>"})
            return

        store = _load_store(self.store_path)
        tokens = store.get("tokens") or {}
        rec = tokens.get(token)
        if not rec:
            self._json(401, {"error": "invalid_token"})
            return

        body = self._read_json()
        if body is None:
            self._json(400, {"error": "invalid_json"})
            return

        req_inner = body.get("request") or {}
        ctx = req_inner.get("context") or {}
        user_intent = ctx.get("user_intent") or ""
        rid = body.get("request_id") or "req_unknown"

        # Minimal conformant response (informative mock).
        response = {
            "protocol_version": "1.0.0",
            "request_id": rid,
            "supported_protocol_versions": ["1.0.0"],
            "response": {
                "status": "success",
                "engine_latency_ms": 1,
                "action_directives": [
                    {
                        "action_type": "render_message",
                        "priority": "normal",
                        "risk_tier": "safe",
                        "payload": {
                            "text": f"[demo-engine] You said: {user_intent!r}",
                        },
                    }
                ],
            },
        }
        self._json(200, response)


def run_demo_server(host: str, port: int, store_path: Path, pair_ttl_sec: int) -> None:
    PairingDemoHandler.store_path = store_path
    PairingDemoHandler.pair_ttl_sec = pair_ttl_sec

    httpd = HTTPServer((host, port), PairingDemoHandler)
    print(
        f"OpenHarness pairing demo listening on http://{host}:{port}/\n"
        f"  POST {PairingDemoHandler.pair_create_path}\n"
        f"  POST {PairingDemoHandler.pair_confirm_path}\n"
        f"  POST {PairingDemoHandler.harness_path}\n"
        f"Store: {store_path.resolve()}",
        file=sys.stderr,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


def _http_json(method: str, url: str, body: dict[str, Any] | None, headers: dict[str, str]) -> tuple[int, dict[str, Any] | str]:
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


def cmd_demo_pair_create(base_url: str) -> int:
    base = base_url.rstrip("/")
    url = f"{base}/demo/pair/create"
    code, payload = _http_json("POST", url, {}, {})
    if code != 200 or not isinstance(payload, dict):
        print(f"demo-pair-create failed: HTTP {code} {payload}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nShow this code on TV: {payload.get('code', '?')}", file=sys.stderr)
    return 0


def cmd_demo_pair_confirm(base_url: str, code: str, tenant_id: str) -> int:
    base = base_url.rstrip("/")
    url = f"{base}/demo/pair/confirm"
    code_u = code.strip().upper()
    body = {"code": code_u, "tenant_id": tenant_id}
    status, payload = _http_json("POST", url, body, {})
    if status != 200 or not isinstance(payload, dict):
        print(f"demo-pair-confirm failed: HTTP {status} {payload}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(
        "\nExport for demo-chat:\n"
        f"  export OPENHARNESS_DEMO_TOKEN={payload.get('access_token', '')}\n"
        f"  export OPENHARNESS_DEMO_SESSION_ID={payload.get('session_id', '')}",
        file=sys.stderr,
    )
    return 0


def _repo_schema_path() -> Path | None:
    from openharness_paths import resolve_schema_path

    return resolve_schema_path()


def _validate_request_message(obj: dict[str, Any]) -> tuple[bool, str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return True, "skipped (pip install jsonschema)"
    sp = _repo_schema_path()
    if sp is None or not sp.is_file():
        return True, "skipped (schema not found)"
    schema = json.loads(sp.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(obj)
    except Exception as e:
        return False, str(e)
    return True, "ok"


def _demo_build_request(
    tenant_id: str,
    session_id: str,
    user_intent: str,
    credential_ref: str | None,
) -> dict[str, Any]:
    rid = f"req_{uuid4().hex[:12]}"
    auth: dict[str, Any] = {"tenant_id": tenant_id}
    if credential_ref:
        auth["credential_ref"] = credential_ref
    return {
        "protocol_version": "1.0.0",
        "request_id": rid,
        "request": {
            "auth": auth,
            "context": {
                "session_id": session_id,
                "user_intent": user_intent,
                "shell": {"shell_kind": "openclaw_demo", "shell_version": "0.1.0"},
            },
        },
    }


def cmd_demo_chat(
    base_url: str,
    tenant_id: str,
    user_intent: str,
    token: str | None,
    session_id: str | None,
    credential_ref: str | None,
    validate: bool,
) -> int:
    import os

    tok = token or os.environ.get("OPENHARNESS_DEMO_TOKEN")
    sid = session_id or os.environ.get("OPENHARNESS_DEMO_SESSION_ID")
    if not tok or not sid:
        print(
            "demo-chat: set --token and --session-id or env OPENHARNESS_DEMO_TOKEN / OPENHARNESS_DEMO_SESSION_ID",
            file=sys.stderr,
        )
        return 2

    env = _demo_build_request(tenant_id, sid, user_intent, credential_ref)
    if validate:
        ok, detail = _validate_request_message(env)
        if not ok:
            print(f"Validation failed: {detail}", file=sys.stderr)
            return 1
        if not detail.startswith("ok"):
            print(f"demo-chat: {detail}", file=sys.stderr)

    base = base_url.rstrip("/")
    url = f"{base}/demo/harness"
    body_raw = json.dumps(env, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=body_raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tok}",
        },
    )
    try:
        with urlopen(req, timeout=60.0) as resp:
            out = resp.read().decode("utf-8", errors="replace")
            sys.stdout.write(out)
            if not out.endswith("\n"):
                sys.stdout.write("\n")
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"demo-chat: HTTP {e.code}", file=sys.stderr)
        if err_body:
            sys.stderr.write(err_body)
        return 1
    except URLError as e:
        print(f"demo-chat: {e.reason}", file=sys.stderr)
        return 1

    return 0
