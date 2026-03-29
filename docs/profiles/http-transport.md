# Profile: HTTP transport (Informative, draft)

**Status:** Informative only. **Does not** change **[PROTOCOL.md](../PROTOCOL.md)**. The core protocol is **transport-agnostic**; this document is for teams that **choose HTTP(S)** and want **shared conventions** instead of ad hoc headers.

**Language:** English first · [中文](#中文)

---

## Purpose

- Align **`correlation_id`** / **tracing** with HTTP headers where gateways and proxies expect them.
- Document **recommended** (not mandatory) patterns so Shell and Engine teams argue less during integration.

---

## Recommended mappings (HTTP)

When using HTTP, implementations MAY use:

| OpenHarness field | Suggested HTTP header | Notes |
|-------------------|----------------------|--------|
| `correlation_id` | `X-Correlation-ID` or `traceparent` (W3C Trace Context) | Pick one per deployment; propagate through proxies. |
| `request_id` | May mirror `correlation_id` or use `X-Request-ID` | Idempotency keys are often separate from tracing; document your choice. |

**Authentication:** Prefer **TLS** + **`Authorization`** (or mTLS) per deployment policy. **Do not** put long-lived secrets in JSON bodies (PROTOCOL §7).

**Timeouts / retries:** Out of scope for the wire JSON; document in Engine deployment guides. **`error.retryable`** in PROTOCOL §13 hints at client behavior.

---

## What this is not

- A **normative** requirement that all OpenHarness implementations use HTTP.
- A replacement for **OpenAPI** — if you publish an OpenAPI document for your HTTP surface, keep it **beside** this profile.

---

## 中文

**性质：** 资料性草案；**不修改** **[PROTOCOL.md](../PROTOCOL.md)**。核心协议 **传输无关**；本文仅面向 **选用 HTTP(S)** 的集成方。

### 建议映射（HTTP）

可将 **`correlation_id`** 与 **`X-Correlation-ID`** 或 W3C **`traceparent`** 等对齐；**`request_id`** 是否与之一致由部署约定。**鉴权** 优先 TLS + `Authorization`；勿在 JSON 正文放长期密钥（PROTOCOL §7）。

### 非规范内容

不强制所有实现使用 HTTP；**OpenAPI** 若有时与本文并列维护即可。
