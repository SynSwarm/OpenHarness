"""
OpenHarness request → OpenClaw (or any HTTP agent) → OpenHarness response.

OpenClaw does not speak OpenHarness JSON natively; this module is a small **Harness
adapter** you run beside your OpenClaw HTTP API. Configure URL + body template +
response path via environment variables.

Normative wire: ../../docs/PROTOCOL.md
"""
from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import openharness_paths
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _get_path(obj: Any, dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if part == "":
            continue
        if isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur[part]
        else:
            raise KeyError(dotted)
    return cur


def _extract_reply_text(resp: dict[str, Any], text_path: str | None) -> str:
    if text_path:
        v = _get_path(resp, text_path)
        return v if isinstance(v, str) else str(v)
    for k in ("reply", "text", "message", "output", "content"):
        v = resp.get(k)
        if isinstance(v, str) and v:
            return v
    return json.dumps(resp, ensure_ascii=False)[:4000]


def _format_body_json(
    template: str,
    tenant_id: str,
    session_id: str,
    user_intent: str,
) -> str:
    """Fill {tenant_id_json}, {session_id_json}, {user_intent_json} (JSON-encoded strings)."""
    return template.format(
        tenant_id=tenant_id,
        session_id=session_id,
        user_intent=user_intent,
        tenant_id_json=json.dumps(tenant_id),
        session_id_json=json.dumps(session_id),
        user_intent_json=json.dumps(user_intent),
    )


class OpenClawBackend:
    def complete(self, request_envelope: dict[str, Any]) -> str:
        raise NotImplementedError


class StubBackend(OpenClawBackend):
    """Echo backend when OPENCLAW_HTTP_URL is unset."""

    def complete(self, request_envelope: dict[str, Any]) -> str:
        inner = request_envelope.get("request") or {}
        ctx = inner.get("context") or {}
        intent = ctx.get("user_intent") or ""
        return f"[stub-openclaw] {intent!r}"


class HttpOpenClawBackend(OpenClawBackend):
    def __init__(
        self,
        url: str,
        body_template: str,
        text_path: str | None,
        headers: dict[str, str],
        timeout: float,
    ) -> None:
        self.url = url
        self.body_template = body_template
        self.text_path = text_path
        self.headers = headers
        self.timeout = timeout

    def complete(self, request_envelope: dict[str, Any]) -> str:
        inner = request_envelope.get("request") or {}
        auth = inner.get("auth") or {}
        ctx = inner.get("context") or {}
        tenant_id = str(auth.get("tenant_id") or "")
        session_id = str(ctx.get("session_id") or "")
        user_intent = str(ctx.get("user_intent") or "")
        body_str = _format_body_json(self.body_template, tenant_id, session_id, user_intent)
        data = body_str.encode("utf-8")
        hdrs = {"Content-Type": "application/json", **self.headers}
        req = Request(self.url, data=data, method="POST", headers=hdrs)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
            raise RuntimeError(f"OpenClaw HTTP {e.code}: {raw[:500]}") from e
        except URLError as e:
            raise RuntimeError(f"OpenClaw request failed: {e.reason}") from e

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip()[:4000]
        if not isinstance(parsed, dict):
            return str(parsed)
        return _extract_reply_text(parsed, self.text_path)


def build_openharness_response(request_envelope: dict[str, Any], reply_text: str, latency_ms: float) -> dict[str, Any]:
    rid = request_envelope.get("request_id") or "req_unknown"
    cid = request_envelope.get("correlation_id")
    out: dict[str, Any] = {
        "protocol_version": "1.0.0",
        "request_id": rid,
        "supported_protocol_versions": ["1.0.0"],
        "response": {
            "status": "success",
            "engine_latency_ms": latency_ms,
            "action_directives": [
                {
                    "action_type": "render_message",
                    "priority": "normal",
                    "risk_tier": "safe",
                    "payload": {"text": reply_text},
                }
            ],
        },
    }
    if cid:
        out["correlation_id"] = cid
    return out


def build_error_response(request_id: str | None, message: str) -> dict[str, Any]:
    return {
        "protocol_version": "1.0.0",
        "request_id": request_id or "req_unknown",
        "response": {
            "status": "error",
            "error": {"code": "bridge_error", "message": message[:2000], "retryable": False},
        },
    }


def get_backend_from_env() -> OpenClawBackend:
    url = os.environ.get("OPENCLAW_HTTP_URL", "").strip()
    if not url:
        return StubBackend()
    body_template = os.environ.get(
        "OPENCLAW_HTTP_BODY_TEMPLATE",
        '{"user_intent": {user_intent_json}, "session_id": {session_id_json}, "tenant_id": {tenant_id_json}}',
    )
    text_path = os.environ.get("OPENCLAW_RESPONSE_TEXT_PATH") or None
    timeout = float(os.environ.get("OPENCLAW_HTTP_TIMEOUT", "120"))
    headers: dict[str, str] = {}
    auth = os.environ.get("OPENCLAW_HTTP_AUTHORIZATION", "").strip()
    if auth:
        headers["Authorization"] = auth
    extra = os.environ.get("OPENCLAW_HTTP_HEADERS_JSON", "").strip()
    if extra:
        headers.update(json.loads(extra))
    return HttpOpenClawBackend(
        url=url,
        body_template=body_template,
        text_path=text_path,
        headers=headers,
        timeout=timeout,
    )


def bridge_request_to_response(request_envelope: dict[str, Any], backend: OpenClawBackend) -> dict[str, Any]:
    if "request" not in request_envelope:
        raise ValueError("not an OpenHarness request (missing top-level 'request')")
    t0 = time.perf_counter()
    text = backend.complete(request_envelope)
    ms = (time.perf_counter() - t0) * 1000.0
    return build_openharness_response(request_envelope, text, ms)


def cmd_bridge_once(path: Path | None, validate: bool) -> int:
    if path is not None and path.name == "-":
        path = None
    if path is None:
        raw = sys.stdin.read()
    else:
        raw = path.read_text(encoding="utf-8")
    try:
        req = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"bridge-once: invalid JSON: {e}", file=sys.stderr)
        return 1
    try:
        backend = get_backend_from_env()
        out = bridge_request_to_response(req, backend)
    except Exception as e:
        print(f"bridge-once: {e}", file=sys.stderr)
        return 1
    if validate:
        sp = openharness_paths.resolve_schema_path()
        if sp is None:
            print("bridge-once: no schema (set OPENHARNESS_SCHEMA_PATH)", file=sys.stderr)
            return 1
        try:
            from jsonschema import Draft202012Validator

            schema = json.loads(sp.read_text(encoding="utf-8"))
            Draft202012Validator(schema).validate(out)
        except Exception as ve:
            print(f"bridge-once: output validation: {ve}", file=sys.stderr)
            return 1
    sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0


class BridgeHTTPHandler(BaseHTTPRequestHandler):
    validate_out: bool = False

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") in ("", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"openharness-openclaw-bridge"}\n')
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0].rstrip("/") not in ("/v1/openharness", "/openharness"):
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        req_id: str | None = None
        try:
            req = json.loads(raw.decode("utf-8"))
            req_id = req.get("request_id")
            backend = get_backend_from_env()
            out = bridge_request_to_response(req, backend)
        except Exception as e:
            out = build_error_response(req_id, str(e))
            raw_out = json.dumps(out, ensure_ascii=False).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw_out)))
            self.end_headers()
            self.wfile.write(raw_out)
            return
        if self.validate_out:
            sp = openharness_paths.resolve_schema_path()
            if sp is not None:
                try:
                    from jsonschema import Draft202012Validator

                    schema = json.loads(sp.read_text(encoding="utf-8"))
                    Draft202012Validator(schema).validate(out)
                except Exception:
                    pass
        raw_out = json.dumps(out, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw_out)))
        self.end_headers()
        self.wfile.write(raw_out)


def run_bridge_server(host: str, port: int, validate_out: bool) -> None:
    BridgeHTTPHandler.validate_out = validate_out
    httpd = HTTPServer((host, port), BridgeHTTPHandler)
    print(
        f"OpenHarness→OpenClaw bridge on http://{host}:{port}/v1/openharness\n"
        f"OPENCLAW_HTTP_URL={'set' if os.environ.get('OPENCLAW_HTTP_URL') else 'unset (stub echo)'}",
        file=sys.stderr,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
