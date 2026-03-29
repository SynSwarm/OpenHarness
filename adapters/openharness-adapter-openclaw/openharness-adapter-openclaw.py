#!/usr/bin/env python3
"""
OpenHarness ↔ OpenClaw (Shell-side bridge).

Normative contract: ../../docs/PROTOCOL.md and ../../schema/openharness-v1.draft.json
Golden JSON: ../../examples/

Informative pairing / long-lived session patterns (TV codes, device tokens, stable
session_id): ../../docs/guides/device-pairing-session.md — demo pairing is optional.

OpenClaw does not emit OpenHarness JSON natively: see openclaw_harness_bridge.py
(bridge-once, bridge-server) to wrap your OPENCLAW_HTTP_URL and return render_message.

Map your OpenClaw IPC/HTTP into outbound request messages and handle response /
action_directives per PROTOCOL §11. This module provides CLI helpers only.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import openclaw_harness_bridge
import openharness_paths
import pairing_demo
import pairing_example_server

# Repo root when cloned as OpenHarness/adapters/openharness-adapter-openclaw/
_REPO_ROOT = openharness_paths.repo_root()
_MINIMAL_REQUEST = _REPO_ROOT / "examples" / "minimal" / "request.json"
_IM_CLI_REQUEST = _REPO_ROOT / "examples" / "im-cli" / "request.json"

_DEFAULT_PROTOCOL_VERSION = "1.0.0"

_FALLBACK_MINIMAL_REQUEST = """{
  "protocol_version": "1.0.0",
  "request_id": "req_minimal_001",
  "request": {
    "auth": {
      "tenant_id": "tenant_demo",
      "credential_ref": "cred_ref_demo"
    },
    "context": {
      "session_id": "sess_demo",
      "user_intent": "Hello, OpenHarness."
    }
  }
}
"""


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("empty stdin")
    return json.loads(raw)


def get_schema_validator():
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None
    sp = openharness_paths.resolve_schema_path()
    if sp is None or not sp.is_file():
        return None
    schema = json.loads(sp.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_message(obj: dict[str, Any]) -> tuple[bool, str]:
    validator = get_schema_validator()
    if validator is None:
        return True, "skipped (pip install jsonschema; set OPENHARNESS_SCHEMA_PATH or install inside OpenHarness repo)"
    try:
        validator.validate(obj)
    except Exception as e:
        return False, str(e)
    return True, "ok"


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(base)
    for k, v in patch.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_minimal_request_text() -> str:
    if _MINIMAL_REQUEST.is_file():
        return _MINIMAL_REQUEST.read_text(encoding="utf-8")
    return _FALLBACK_MINIMAL_REQUEST


def cmd_emit_minimal() -> int:
    text = load_minimal_request_text()
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def cmd_emit_im() -> int:
    if _IM_CLI_REQUEST.is_file():
        text = _IM_CLI_REQUEST.read_text(encoding="utf-8")
    else:
        print("examples/im-cli/request.json not found; use emit-minimal.", file=sys.stderr)
        return 2
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def cmd_validate(path: Path | None) -> int:
    if path is not None and path.name == "-":
        path = None
    if path is None:
        try:
            obj = read_json_stdin()
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Invalid JSON from stdin: {e}", file=sys.stderr)
            return 1
        label = "stdin"
    else:
        raw = path.read_text(encoding="utf-8")
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            return 1
        label = str(path)

    ok, detail = validate_message(obj)
    if ok and detail.startswith("skipped"):
        print(f"OK: JSON parses ({label}). {detail}", file=sys.stderr)
        return 0
    if ok:
        sp = openharness_paths.resolve_schema_path()
        name = sp.name if sp else "schema"
        print(f"OK: {label} validates against {name}.")
        return 0
    print(f"Schema validation failed ({label}): {detail}", file=sys.stderr)
    return 1


def build_request_envelope(
    *,
    tenant_id: str,
    session_id: str,
    user_intent: str,
    request_id: str | None,
    correlation_id: str | None,
    credential_ref: str | None,
    conversation_id: str | None,
    shell_kind: str | None,
    shell_version: str | None,
    capabilities_json: str | None,
) -> dict[str, Any]:
    rid = request_id or f"req_{uuid.uuid4().hex[:12]}"
    auth: dict[str, Any] = {"tenant_id": tenant_id}
    if credential_ref:
        auth["credential_ref"] = credential_ref
    ctx: dict[str, Any] = {
        "session_id": session_id,
        "user_intent": user_intent,
    }
    if conversation_id:
        ctx["conversation_id"] = conversation_id
    if shell_kind:
        sh: dict[str, Any] = {"shell_kind": shell_kind}
        if shell_version:
            sh["shell_version"] = shell_version
        ctx["shell"] = sh

    envelope: dict[str, Any] = {
        "protocol_version": _DEFAULT_PROTOCOL_VERSION,
        "request_id": rid,
        "request": {
            "auth": auth,
            "context": ctx,
        },
    }
    if correlation_id:
        envelope["correlation_id"] = correlation_id
    if capabilities_json:
        envelope["capabilities"] = json.loads(capabilities_json)

    return envelope


def cmd_build_request(ns: argparse.Namespace) -> int:
    try:
        env = build_request_envelope(
            tenant_id=ns.tenant_id,
            session_id=ns.session_id,
            user_intent=ns.user_intent,
            request_id=ns.request_id,
            correlation_id=ns.correlation_id,
            credential_ref=ns.credential_ref,
            conversation_id=ns.conversation_id,
            shell_kind=ns.shell_kind,
            shell_version=ns.shell_version,
            capabilities_json=ns.capabilities_json,
        )
        if ns.patch:
            patch = load_json_file(ns.patch)
            env = deep_merge(env, patch)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"build-request failed: {e}", file=sys.stderr)
        return 1

    if ns.validate:
        ok, detail = validate_message(env)
        if not ok:
            print(f"Validation failed: {detail}", file=sys.stderr)
            return 1

    sys.stdout.write(json.dumps(env, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0


def summarize_message(obj: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    pv = obj.get("protocol_version", "?")
    lines.append(f"protocol_version: {pv}")
    rid = obj.get("request_id")
    if rid:
        lines.append(f"request_id: {rid}")
    cid = obj.get("correlation_id")
    if cid:
        lines.append(f"correlation_id: {cid}")

    if "request" in obj:
        lines.append("kind: request")
        return lines

    if "response" in obj:
        lines.append("kind: response")
        spv = obj.get("supported_protocol_versions")
        if spv:
            lines.append(f"supported_protocol_versions: {spv}")
        resp = obj.get("response") or {}
        st = resp.get("status")
        if st:
            lines.append(f"response.status: {st}")
        err = resp.get("error")
        if err:
            lines.append(f"response.error.code: {err.get('code', '?')}")
            if err.get("message"):
                lines.append(f"response.error.message: {err['message']}")
        ads = resp.get("action_directives") or []
        lines.append(f"action_directives: {len(ads)}")
        for i, ad in enumerate(ads):
            at = ad.get("action_type", "?")
            lines.append(f"  [{i}] action_type={at}")
        denials = obj.get("capability_denials") or []
        if denials:
            lines.append(f"capability_denials: {len(denials)}")
        return lines

    lines.append("kind: unknown (no top-level request/response)")
    return lines


def cmd_inspect(path: Path | None) -> int:
    if path is not None and path.name == "-":
        path = None
    try:
        if path is None:
            obj = read_json_stdin()
        else:
            obj = load_json_file(path)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1

    for line in summarize_message(obj):
        print(line)
    return 0


def cmd_post(ns: argparse.Namespace) -> int:
    if ns.file:
        body = ns.file.read_text(encoding="utf-8")
    else:
        body = sys.stdin.read()
    if not body.strip():
        print("post: empty body (use --file or pipe JSON on stdin)", file=sys.stderr)
        return 1

    headers: dict[str, str] = {"Content-Type": "application/json"}
    for h in ns.header:
        if ":" not in h:
            print(f"post: bad header (expected 'Name: value'): {h!r}", file=sys.stderr)
            return 2
        name, value = h.split(":", 1)
        headers[name.strip()] = value.strip()

    try:
        msg = json.loads(body)
    except json.JSONDecodeError as e:
        print(f"post: invalid JSON: {e}", file=sys.stderr)
        return 1

    cid = msg.get("correlation_id")
    if cid and not ns.no_correlation_header:
        headers.setdefault(ns.correlation_header, cid)

    req = Request(
        ns.url,
        data=body.encode("utf-8"),
        method="POST",
        headers=headers,
    )
    try:
        with urlopen(req, timeout=ns.timeout) as resp:
            out = resp.read().decode("utf-8", errors="replace")
            sys.stdout.write(out)
            if out and not out.endswith("\n"):
                sys.stdout.write("\n")
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"post: HTTP {e.code} {e.reason}", file=sys.stderr)
        if err_body:
            sys.stderr.write(err_body)
            if not err_body.endswith("\n"):
                sys.stderr.write("\n")
        return 1
    except URLError as e:
        print(f"post: request failed: {e.reason}", file=sys.stderr)
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="OpenHarness ↔ OpenClaw bridge CLI. "
        "Wire format: PROTOCOL.md + schema/openharness-v1.draft.json.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("emit-minimal", help="Print minimal OpenHarness request JSON (from examples/ if present).")
    sub.add_parser("emit-im", help="Print im-cli example request JSON (from examples/im-cli/ if present).")

    v = sub.add_parser("validate", help="Validate JSON against the OpenHarness schema (needs jsonschema).")
    v.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="JSON file, or omit / use '-' for stdin.",
    )

    b = sub.add_parser(
        "build-request",
        help="Build a request envelope from flags; optional --patch merge and --validate.",
    )
    b.add_argument("--tenant-id", required=True, help="request.request.auth.tenant_id")
    b.add_argument("--session-id", required=True, help="request.context.session_id")
    b.add_argument("--user-intent", required=True, help="request.context.user_intent")
    b.add_argument("--request-id", default=None, help="Top-level request_id (default: random).")
    b.add_argument("--correlation-id", default=None)
    b.add_argument("--credential-ref", default=None, help="request.request.auth.credential_ref")
    b.add_argument("--conversation-id", default=None)
    b.add_argument("--shell-kind", default=None, help="Sets request.context.shell.shell_kind")
    b.add_argument("--shell-version", default=None)
    b.add_argument(
        "--capabilities-json",
        default=None,
        metavar="JSON",
        help='Object JSON for top-level "capabilities" (e.g. \'{"openharness.ui.rich_cards":true}\')',
    )
    b.add_argument(
        "--patch",
        type=Path,
        default=None,
        help="JSON file merged into the envelope (deep merge).",
    )
    b.add_argument(
        "--validate",
        action="store_true",
        help="Validate built JSON against schema before printing.",
    )
    b.set_defaults(func=cmd_build_request)

    ins = sub.add_parser(
        "inspect",
        help="Print a short summary of a request or response JSON (file or stdin).",
    )
    ins.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="JSON file, or omit / use '-' for stdin.",
    )

    po = sub.add_parser(
        "post",
        help="POST JSON body to URL (stdlib). Adds X-Correlation-ID from body when --correlation-header is set.",
    )
    po.add_argument("--url", required=True, help="Engine HTTP endpoint (https://...)")
    po.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Request body file (default: stdin).",
    )
    po.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="H",
        help="Extra header 'Name: value' (repeatable). E.g. --header 'Authorization: Bearer ...'",
    )
    po.add_argument(
        "--correlation-header",
        default="X-Correlation-ID",
        metavar="NAME",
        help="If body has correlation_id, also send it in this header (default: X-Correlation-ID).",
    )
    po.add_argument(
        "--no-correlation-header",
        action="store_true",
        help="Do not mirror correlation_id into an HTTP header.",
    )
    po.add_argument("--timeout", type=float, default=60.0, help="Socket timeout seconds (default: 60).")
    po.set_defaults(func=cmd_post)

    ds = sub.add_parser(
        "demo-server",
        help="Run local pairing + mock Harness HTTP demo (stdlib only; NOT for production).",
    )
    ds.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1).")
    ds.add_argument("--port", type=int, default=8765, help="Port (default: 8765).")
    ds.add_argument(
        "--store",
        type=Path,
        default=Path(".openharness-demo-store.json"),
        help="JSON file for pending codes and issued tokens (default: ./.openharness-demo-store.json).",
    )
    ds.add_argument("--ttl", type=int, default=300, metavar="SEC", help="Pairing code TTL (default: 300).")

    dpc = sub.add_parser(
        "demo-pair-create",
        help="Call demo server POST /demo/pair/create (simulates TV fetching a code).",
    )
    dpc.add_argument("--base-url", default="http://127.0.0.1:8765", help="demo-server base URL.")

    dpf = sub.add_parser(
        "demo-pair-confirm",
        help="Call demo server POST /demo/pair/confirm (simulates CLI entering the code).",
    )
    dpf.add_argument("code", help="8-character code from demo-pair-create.")
    dpf.add_argument("--tenant-id", required=True, help="Tenant id after pairing.")
    dpf.add_argument("--base-url", default="http://127.0.0.1:8765", help="demo-server base URL.")

    dch = sub.add_parser(
        "demo-chat",
        help="POST OpenHarness request to demo /demo/harness (needs token + session from pairing).",
    )
    dch.add_argument("--base-url", default="http://127.0.0.1:8765", help="demo-server base URL.")
    dch.add_argument("--tenant-id", required=True, help="request.request.auth.tenant_id")
    dch.add_argument("--user-intent", required=True, help="request.context.user_intent")
    dch.add_argument("--token", default=None, help="Bearer token (or env OPENHARNESS_DEMO_TOKEN).")
    dch.add_argument("--session-id", default=None, help="context.session_id (or env OPENHARNESS_DEMO_SESSION_ID).")
    dch.add_argument("--credential-ref", default=None, help="Optional auth.credential_ref.")
    dch.add_argument(
        "--validate",
        action="store_true",
        help="Validate request JSON against schema before POST (needs jsonschema).",
    )

    bo = sub.add_parser(
        "bridge-once",
        help="Read one OpenHarness request JSON (file or stdin); call OpenClaw HTTP or stub; print response JSON.",
    )
    bo.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="Request JSON file, or omit / '-' for stdin.",
    )
    bo.add_argument(
        "--validate",
        action="store_true",
        help="Validate output against schema (needs jsonschema).",
    )

    bs = sub.add_parser(
        "bridge-server",
        help="HTTP server: POST /v1/openharness accepts OpenHarness request; returns response (OpenClaw behind OPENCLAW_HTTP_URL).",
    )
    bs.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1).")
    bs.add_argument("--port", type=int, default=8788, help="Port (default: 8788).")
    bs.add_argument(
        "--validate",
        action="store_true",
        help="Validate successful responses against schema if jsonschema is installed.",
    )

    ps = sub.add_parser(
        "pair-server",
        help="EXAMPLE: SQLite pairing gateway (POST /pair/create, /pair/confirm). Not required for production.",
    )
    ps.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1).")
    ps.add_argument("--port", type=int, default=8790, help="Port (default: 8790).")
    ps.add_argument(
        "--db",
        type=Path,
        default=Path(".openharness-pair-example.sqlite3"),
        help="SQLite file (default: ./.openharness-pair-example.sqlite3).",
    )
    ps.add_argument("--ttl", type=int, default=300, metavar="SEC", help="Pairing code TTL (default: 300).")
    ps.add_argument(
        "--confirm-secret",
        default=None,
        help="If set, confirm must send same value as body confirm_secret or X-Pairing-Confirm header.",
    )

    pc = sub.add_parser(
        "pair-create",
        help="Call pair-server POST /pair/create (same shape as demo-pair-create, different default URL).",
    )
    pc.add_argument("--base-url", default="http://127.0.0.1:8790", help="pair-server base URL.")

    pf = sub.add_parser(
        "pair-confirm",
        help="Call pair-server POST /pair/confirm.",
    )
    pf.add_argument("code", help="Code from pair-create.")
    pf.add_argument("--tenant-id", required=True, help="Tenant id.")
    pf.add_argument("--base-url", default="http://127.0.0.1:8790", help="pair-server base URL.")
    pf.add_argument(
        "--confirm-secret",
        default=None,
        help="Must match pair-server --confirm-secret if server requires it.",
    )

    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)

    if args.command == "emit-minimal":
        return cmd_emit_minimal()
    if args.command == "emit-im":
        return cmd_emit_im()
    if args.command == "validate":
        return cmd_validate(args.path)
    if args.command == "build-request":
        return args.func(args)
    if args.command == "inspect":
        return cmd_inspect(args.path)
    if args.command == "post":
        return args.func(args)
    if args.command == "demo-server":
        pairing_demo.run_demo_server(
            host=args.host,
            port=args.port,
            store_path=args.store,
            pair_ttl_sec=args.ttl,
        )
        return 0
    if args.command == "demo-pair-create":
        return pairing_demo.cmd_demo_pair_create(args.base_url)
    if args.command == "demo-pair-confirm":
        return pairing_demo.cmd_demo_pair_confirm(args.base_url, args.code, args.tenant_id)
    if args.command == "demo-chat":
        return pairing_demo.cmd_demo_chat(
            base_url=args.base_url,
            tenant_id=args.tenant_id,
            user_intent=args.user_intent,
            token=args.token,
            session_id=args.session_id,
            credential_ref=args.credential_ref,
            validate=args.validate,
        )
    if args.command == "bridge-once":
        return openclaw_harness_bridge.cmd_bridge_once(args.path, args.validate)
    if args.command == "bridge-server":
        openclaw_harness_bridge.run_bridge_server(host=args.host, port=args.port, validate_out=args.validate)
        return 0
    if args.command == "pair-server":
        pairing_example_server.run_pair_server(
            host=args.host,
            port=args.port,
            db_path=args.db,
            pair_ttl_sec=args.ttl,
            confirm_secret=args.confirm_secret,
        )
        return 0
    if args.command == "pair-create":
        return pairing_example_server.cmd_pair_create(args.base_url)
    if args.command == "pair-confirm":
        return pairing_example_server.cmd_pair_confirm(
            args.base_url,
            args.code,
            args.tenant_id,
            args.confirm_secret,
        )

    raise AssertionError("unhandled command")


if __name__ == "__main__":
    raise SystemExit(main())
