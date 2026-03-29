# OpenHarness Protocol Specification

**Version:** v1.0.0-draft  
**Language:** English (authoritative). See [PROTOCOL.zh.md](./PROTOCOL.zh.md) for Chinese.

This document defines the **normative** JSON message contract between a **Shell** (UI, device, or client) and a **Harness Engine** (orchestration, models, tools). Transport (HTTP, WebSocket, gRPC, etc.) is out of scope for v1 except where noted as recommendations.

---

## 1. Goals and non-goals

**Goals**

- **Transport-agnostic JSON** payloads that any stack can implement.
- **Forward compatibility**: unknown fields MUST be ignored (see §4).
- **Clear versioning** and optional **capability negotiation**.
- **Neutral** to LLM vendor, runtime, and tool implementation details.

**Non-goals**

- Defining UI frameworks, widget libraries, or specific model APIs.
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

- **Unknown fields** at any object level MUST be **ignored** by the recipient (JSON merge / parse-and-ignore). This applies to top-level keys and nested objects.
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
| `request_id` | recommended | Opaque ID for tracing; echoed in the response. |
| `capabilities` | no | Features the Shell supports (see §5.3). |
| `request` | yes | Payload: `auth`, `context`, optional `extensions`. |

### 5.2 Response (Engine → Shell)

| Field | Required | Description |
|-------|----------|-------------|
| `protocol_version` | yes | Wire format version used for this response. |
| `request_id` | recommended | Echo of `request_id` when present. |
| `supported_protocol_versions` | no | Versions this Engine accepts (see §3). |
| `response` | yes | `status`, optional `error`, optional metrics and directives. |

### 5.3 Capabilities

`capabilities` is an object whose keys are **feature identifiers** (stable strings). Values are implementation-defined (boolean, string, or object). Example:

```json
"capabilities": {
  "openharness.actions.parallel": true,
  "openharness.stream.events": { "max_events_per_second": 20 }
}
```

Recipients MUST ignore capability keys they do not understand.

---

## 6. Authentication and secrets (normative guidance)

- **Do not** define long-lived API secrets as a required part of the JSON body in production integrations. Prefer transport-layer authentication (e.g. TLS + `Authorization` header, mTLS, or signed requests).
- When the transport already establishes identity, **`auth`** MAY carry only **stable references** (e.g. `tenant_id`, `credential_ref`, `session_id`) rather than raw tokens.
- If a token must appear in JSON for a specific deployment, treat it as **opaque**, short-lived, and never log or return it in **`error`** payloads.

---

## 7. Privacy and environment state

- **`environment_state`** SHOULD be classified by the Shell using **`privacy_tier`** when sending potentially sensitive data:

  | Value | Meaning |
  |-------|---------|
  | `public` | Safe to log and share under your product policy. |
  | `restricted` | May contain PII or sensitive metadata; minimize retention. |
  | `secret` | Must not be logged or sent to third parties without explicit policy. |

- Shells SHOULD prefer **derived** or **hashed** representations (e.g. screen fingerprint) over raw screen contents unless the user and policy allow.

---

## 8. Context (`request.context`)

| Field | Required | Description |
|-------|----------|-------------|
| `session_id` | recommended | Correlates multi-turn work. |
| `user_intent` | recommended | Natural-language or structured intent. |
| `environment_state` | no | Device/OS/UI state; may include `privacy_tier`. |
| `extensions` | no | Additional context (see §4). |

---

## 9. Action directives (`response.action_directives`)

Each item:

| Field | Required | Description |
|-------|----------|-------------|
| `action_type` | yes | Registered or namespaced type (see §10). |
| `priority` | no | Hint: e.g. `low`, `normal`, `high`, `critical`. |
| `execution` | no | `sequential` (default) or `parallel` with siblings where applicable. |
| `risk_tier` | no | `safe`, `caution`, `dangerous` — Shell may require user confirmation for higher tiers. |
| `requires_user_approval` | no | If `true`, Shell MUST obtain explicit user approval before execution. |
| `payload` | no | Type-specific data. |
| `extensions` | no | Per-directive extensions. |

**Ordering**: Unless `execution` indicates otherwise, Shells SHOULD process directives **in array order**.

---

## 10. Action type registry

- **Core** types (examples, not exhaustive): `render_ui`, `simulate_action`, `noop`.
- **Namespaced** types SHOULD use reverse-DNS or URIs, e.g. `com.deskharness.render.dashboard`.
- Implementations MAY publish an optional public registry; the protocol does not require a central authority for v1.

---

## 11. Error model

On failure, **`response.status`** MUST be `error` and **`response.error`** SHOULD be present:

| Field | Required | Description |
|-------|----------|-------------|
| `code` | yes | Stable machine-readable code (e.g. `invalid_request`, `engine_timeout`). |
| `message` | no | Safe human-readable message; MUST NOT echo secrets or raw PII. |
| `details` | no | Structured diagnostic info safe for logs. |

---

## 12. Success response

When **`response.status`** is `success`, **`response.action_directives`** MAY be empty. Optional fields:

| Field | Description |
|-------|-------------|
| `engine_latency_ms` | Round-trip processing time at the Engine (hint). |

---

## 13. Schema

Normative JSON Schema (draft): [`../schema/openharness-v1.draft.json`](../schema/openharness-v1.draft.json).

---

## 14. Example (minimal)

```json
{
  "protocol_version": "1.0.0",
  "request_id": "req_01jqxyz",
  "capabilities": {
    "openharness.actions.parallel": true
  },
  "request": {
    "auth": {
      "tenant_id": "usr_9527",
      "credential_ref": "cred_opaque_abc"
    },
    "context": {
      "session_id": "sess_8848",
      "user_intent": "Analyze the current screen and extract key metrics.",
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
  "supported_protocol_versions": ["1.0.0"],
  "response": {
    "status": "success",
    "engine_latency_ms": 120,
    "action_directives": [
      {
        "action_type": "render_ui",
        "priority": "high",
        "risk_tier": "safe",
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

## 15. License

Specification text and schemas in this repository are licensed under the same terms as the project (see `LICENSE` in the repository root), unless a file header states otherwise.
