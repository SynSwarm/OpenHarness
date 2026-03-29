# OpenHarness Protocol Specification

**Version:** v1.0.0-draft  
**Language:** English (authoritative). See [PROTOCOL.zh.md](./PROTOCOL.zh.md) for Chinese.

This document defines the **normative** JSON message contract between a **Shell** (UI, device, or client) and a **Harness Engine** (orchestration, models, tools). Transport (HTTP, WebSocket, gRPC, etc.) is out of scope for v1 except where noted as recommendations.

For **repository scope** — what is normative here versus what belongs to Shell/Engine products (e.g. DeskHarness, **fastClaw**, any other Engine) — see **[SCOPE.md](./SCOPE.md)** (informative). For a **layered narrative** (core wire format vs optional profiles vs transport/execution feedback), see **[OVERVIEW.md](./OVERVIEW.md)** (informative).

DeskHarness / Fangcun and other integrators MAY publish **wishlists** or **implementation mappings**; those documents do **not** override this specification.

---

## 1. Goals and non-goals

**Goals**

- **Transport-agnostic JSON** payloads that any stack can implement.
- **Forward compatibility**: unknown fields MUST be ignored (see §4).
- **Clear versioning** and **capability negotiation** (bidirectional where possible).
- **Neutral** to LLM vendor, runtime, and tool implementation details.

**Non-goals**

- Defining UI frameworks, widget libraries, or specific model APIs.
- Normative **streaming chunk** formats in v1 (see §15).
- Per-product field allowlists for every Shell variant (see §8 and implementation guides outside this spec).
- Trademark policy (handled separately if needed).

---

## 2. Terminology

| Term | Meaning |
|------|---------|
| **Shell** | Endpoint that captures user intent and environment state; renders or executes **action directives**. |
| **Harness Engine** | Server-side logic: routing, SOP/state machines, tools, safety, and generation of directives. |
| **Action directive** | One structured unit of work or output (UI render, automation step, etc.). |

---

## 3. Versioning

- **`protocol_version`** (string, required): Semantic version of the **wire format** this message conforms to (e.g. `1.0.0`).  
- **Compatibility rule**  
  - **Major**: incompatible changes (removing required fields, changing types, redefining semantics).  
  - **Minor**: backward-compatible additions (new optional fields, new `action_type` values in the registry).  
  - **Patch**: clarifications and documentation-only unless explicitly marked as wire-affecting.

Engines SHOULD include **`supported_protocol_versions`** in responses (array of strings) when they support more than one major line.

Shells SHOULD send the highest **`protocol_version`** they implement. If the Engine cannot satisfy the request, it MUST respond with **`status`: `error`** and an appropriate **`error.code`** (e.g. `protocol_version_unsupported`).

---

## 4. Extensibility

- **Unknown fields** at any object level MUST be **ignored** by the recipient (JSON merge / parse-and-ignore). This applies to top-level keys and nested objects. (Handling of an **unknown `action_type` value** is separate; see §11.)
- **Vendor extensions** SHOULD use a single object key:

  ```json
  "extensions": {
    "com.example": { "foo": 1 }
  }
  ```

  Keys inside `extensions` SHOULD use reverse-DNS or URI prefixes to avoid collisions.

---

## 5. Message envelope

### 5.1 Request (Shell → Engine)

| Field | Required | Description |
|-------|----------|-------------|
| `protocol_version` | yes | Wire format version (semver string). |
| `request_id` | recommended | Opaque ID for **idempotency** and request/response pairing; echoed in the response. |
| `correlation_id` | optional | Opaque ID for **distributed tracing** and log correlation (may differ from `request_id`). Echoed in the response when present. |
| `capabilities` | no | Features the Shell supports (see §5.3). |
| `request` | yes | Payload: `auth`, `context`, optional `extensions`. |

### 5.2 Response (Engine → Shell)

| Field | Required | Description |
|-------|----------|-------------|
| `protocol_version` | yes | Wire format version used for this response. |
| `request_id` | recommended | Echo of `request_id` when present. |
| `correlation_id` | optional | Echo of `correlation_id` when present. |
| `supported_protocol_versions` | no | Versions this Engine accepts (see §3). |
| `supported_capabilities` | no | Capabilities this Engine **offers** for this session or build (object; same key shape style as `capabilities`). |
| `capability_denials` | no | Explicit **rejections** of Shell-asked capabilities (see §5.3). |
| `response` | yes | `status`, optional `error`, optional metrics and directives. |

### 5.3 Capabilities

`capabilities` (Shell → Engine) and `supported_capabilities` (Engine → Shell) are objects whose keys are **feature identifiers** (stable strings). Values are implementation-defined (boolean, string, or object).

**Example keys** (illustrative; implementations MAY define more):

| Key | Typical meaning |
|-----|-----------------|
| `openharness.streaming` | Shell or Engine can participate in streaming (profile TBD outside v1 normative body). |
| `openharness.actions.parallel` | Parallel execution of compatible directives. |
| `openharness.attachments.upload` | Shell can supply attachment references. |
| `openharness.ui.rich_cards` | Shell can render rich cards. |
| `openharness.ui.approval` | Shell can show approval UI for `requires_user_approval`. |

Recipients MUST ignore capability keys they do not understand.

**`capability_denials`** (optional, Engine → Shell): array of objects:

| Field | Required | Description |
|-------|----------|---------------|
| `capability` | yes | Feature identifier that is not available or rejected. |
| `code` | recommended | Machine-readable reason (e.g. `not_supported`, `disabled_by_policy`). |
| `message` | no | Safe human-readable explanation. |

This avoids **silent half-features** when a Shell asks for a capability the Engine cannot honor.

---

## 6. Shell identity (`request.context.shell`)

Optional object describing the Shell implementation so the Engine can tailor response **shape** (cards vs plain text vs large-font short lines, etc.).

| Field | Required | Description |
|-------|----------|-------------|
| `shell_kind` | recommended | Stable identifier for the Shell family. MAY use well-known strings (`feishu_bot`, `lark_cli`, `command_shell`, `tv`, `vehicle_hmi`, …) or **namespaced** strings (`com.example.kiosk`). |
| `shell_version` | optional | Shell software version string. |
| `locale` | optional | BCP 47 language tag (e.g. `zh-CN`, `en-US`). |
| `timezone` | optional | IANA time zone name (e.g. `Asia/Shanghai`). |

---

## 7. Authentication and secrets (normative guidance)

- **Do not** define long-lived API secrets as a required part of the JSON body in production integrations. Prefer transport-layer authentication (e.g. TLS + `Authorization` header, mTLS, or signed requests).
- When the transport already establishes identity, **`auth`** MAY carry only **stable references** (e.g. `tenant_id`, `credential_ref`, `session_id`) rather than raw tokens.
- If a token must appear in JSON for a specific deployment, treat it as **opaque**, short-lived, and never log or return it in **`error`** payloads.
- Engines MUST NOT require **plaintext long-lived secrets** in the protocol body when a reference or transport auth suffices.

---

## 8. Privacy and environment state

- **`environment_state`** SHOULD be classified by the Shell using **`privacy_tier`** when sending potentially sensitive data:

  | Value | Meaning |
  |-------|---------|
  | `public` | Safe to log and share under your product policy. |
  | `restricted` | May contain PII or sensitive metadata; minimize retention. |
  | `secret` | Must not be logged or sent to third parties without explicit policy. |

- Shells SHOULD prefer **derived** or **hashed** representations (e.g. screen fingerprint) over raw screen contents unless the user and policy allow.
- **Per-Shell field allowlists** (which `environment_state` keys a given Shell may send) are **deployment / product policy** concerns. Document them in implementation guides; the protocol defines **semantics**, not every OEM matrix.

---

## 9. Context (`request.context`)

| Field | Required | Description |
|-------|----------|-------------|
| `session_id` | recommended | Long-lived **user ↔ Engine** conversation line. |
| `conversation_id` | optional | Sub-thread within a session (e.g. multi-tab or branched topic). |
| `user_intent` | recommended | Natural-language or structured intent. |
| `task_hint` | optional | Structured hints for routing (e.g. `sop_id`, `plugin_id`, business keys). Engines map these to internal `task_params` / SOP context. |
| `continuation` | optional | Resume a prior **run** (see below). |
| `environment_state` | no | Device/OS/UI state; may include `privacy_tier`. |
| `attachments` | no | References to **files / images / card payloads** (see §9.1). |
| `shell` | no | Shell identity (see §6). |
| `extensions` | no | Additional context (see §4). |

### 9.1 Attachments

`attachments` MUST be an array of **reference** objects. Implementations MUST **not** embed large binary blobs (e.g. base64) in the protocol message body.

Each item SHOULD include at least one of: opaque **`ref_id`** (previously uploaded), **`uri`** (https or app-specific), or **`asset_id`**. Optional: `mime_type`, `filename`, `size_bytes`.

### 9.2 Continuation (SOP / run resume)

`continuation` is an optional object for **idempotent resume** of a workflow (e.g. “Continue” in Feishu):

| Field | Required | Description |
|-------|----------|-------------|
| `run_id` | optional | Engine-issued run identifier. |
| `sop_id` | optional | SOP / workflow identifier. |
| `continuation_token` | optional | Opaque token issued by the Engine for the next step. |

Exact semantics are engine-specific; the protocol carries **opaque identifiers** only.

---

## 10. Action directives (`response.action_directives`)

Each item:

| Field | Required | Description |
|-------|----------|-------------|
| `action_type` | yes | Registered or namespaced type (see §12). |
| `priority` | no | Hint: e.g. `low`, `normal`, `high`, `critical`. |
| `execution` | no | `sequential` (default) or `parallel` with siblings where applicable. |
| `risk_tier` | no | `safe`, `caution`, `dangerous` — Shell may require user confirmation for higher tiers. |
| `requires_user_approval` | no | If `true`, Shell MUST obtain explicit user approval before execution. |
| `deadline_ms` | optional | Relative deadline from receipt for time-sensitive directives (Shell best-effort). |
| `payload` | no | Type-specific data. |
| `extensions` | no | Per-directive extensions. |

**Ordering**: Unless `execution` indicates otherwise, Shells SHOULD process directives **in array order**.

---

## 11. Unknown `action_type` (normative)

Shells maintain a set of **`action_type`** values they implement. If a directive’s `action_type` is **unknown** to the Shell:

1. The Shell MUST **not** execute **side-effecting** behavior (OS automation, payments, destructive file ops, network calls beyond telemetry, etc.) for that directive.
2. The Shell SHOULD **skip** the directive and continue processing later items **or** **degrade** to a user-visible message when `payload` contains a portable string field such as **`message`** or **`fallback_message`** (convention for Engines).
3. The Shell MAY emit a **local** diagnostic / telemetry event with code `unknown_action_type` (implementation-defined).

Deployments that intentionally execute unknown types MUST NOT do so by default; such behavior is **out of profile** for interoperable clients.

---

## 12. Action type registry

- **Core** types (examples, not exhaustive): `render_ui`, `simulate_action`, `render_message`, `request_approval`, `noop`.
- **Namespaced** types SHOULD use reverse-DNS or dotted prefixes with **stable semantics**, e.g. `fangcun.sop.start`, `fangcun.plugin.invoke`, `com.deskharness.render.dashboard`. Where semver is embedded, document it in the registry entry, not in the wire string unless explicitly standardized.
- Implementations MAY publish an optional public registry; the protocol does not require a central authority for v1.

---

## 13. Error model

On failure, **`response.status`** MUST be `error` and **`response.error`** SHOULD be present:

| Field | Required | Description |
|-------|----------|-------------|
| `code` | yes | Stable machine-readable code (e.g. `invalid_request`, `engine_timeout`, `unknown_action_type`). |
| `message` | no | Safe human-readable message; MUST NOT echo secrets or raw PII. |
| `retryable` | no | If `true`, the client MAY retry with backoff; if `false`, retry is unlikely to succeed without changing the request. |
| `details` | no | Structured diagnostic info safe for logs. |

---

## 14. Success response

When **`response.status`** is `success`, **`response.action_directives`** MAY be empty. Optional fields:

| Field | Description |
|-------|-------------|
| `engine_latency_ms` | Round-trip processing time at the Engine (hint). |

---

## 15. Streaming (informative)

Normative **request/response** JSON in v1 is **non-streaming**. Streaming over SSE or WebSocket (chunking, `stream_id`, partial directives) MAY be introduced as a **separate streaming profile** advertised via `capabilities` (e.g. `openharness.streaming`). Shells and Engines SHOULD negotiate that profile explicitly rather than assuming stream semantics from the v1 body alone.

---

## 16. Schema

Normative JSON Schema (draft): [`../schema/openharness-v1.draft.json`](../schema/openharness-v1.draft.json).

---

## 17. Example (illustrative)

```json
{
  "protocol_version": "1.0.0",
  "request_id": "req_01jqxyz",
  "correlation_id": "corr_8f3a",
  "capabilities": {
    "openharness.actions.parallel": true,
    "openharness.ui.rich_cards": true
  },
  "request": {
    "auth": {
      "tenant_id": "usr_9527",
      "credential_ref": "cred_opaque_abc"
    },
    "context": {
      "session_id": "sess_8848",
      "conversation_id": "conv_tab_2",
      "user_intent": "Continue the onboarding SOP.",
      "task_hint": {
        "sop_id": "sop_onboard",
        "business_key": "deal_42"
      },
      "continuation": {
        "run_id": "run_7d2",
        "continuation_token": "ctok_aq9"
      },
      "shell": {
        "shell_kind": "feishu_bot",
        "shell_version": "2.1.0",
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai"
      },
      "attachments": [
        {
          "ref_id": "att_01",
          "mime_type": "image/png"
        }
      ],
      "environment_state": {
        "privacy_tier": "restricted",
        "os": "macOS",
        "active_window": "Excel",
        "screen_hash": "a1b2c3d4"
      }
    }
  }
}
```

```json
{
  "protocol_version": "1.0.0",
  "request_id": "req_01jqxyz",
  "correlation_id": "corr_8f3a",
  "supported_protocol_versions": ["1.0.0"],
  "supported_capabilities": {
    "openharness.actions.parallel": true,
    "openharness.ui.rich_cards": true
  },
  "capability_denials": [],
  "response": {
    "status": "success",
    "engine_latency_ms": 120,
    "action_directives": [
      {
        "action_type": "render_ui",
        "priority": "high",
        "risk_tier": "safe",
        "deadline_ms": 5000,
        "payload": { "component": "DataChart", "data": [] }
      },
      {
        "action_type": "simulate_action",
        "priority": "critical",
        "risk_tier": "dangerous",
        "requires_user_approval": true,
        "payload": { "macro": "cmd+c", "target": "cell_B2" }
      }
    ]
  }
}
```

---

## 18. License

Specification text and schemas in this repository are licensed under the same terms as the project (see `LICENSE` in the repository root), unless a file header states otherwise.
