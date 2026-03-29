# Device pairing & long-lived sessions (informative recommendations)

**Status:** Informative. **Does not** change **[PROTOCOL.md](../PROTOCOL.md)**. It records **recommended product patterns** for Shell teams (e.g. Android TV + server-side CLI) that need **one-time pairing** and **long-term** use without re-entering codes on every chat.

**Language:** English first · [中文](#中文)

---

## 1. Why this guide exists

OpenHarness defines **wire JSON** between Shell and Engine (**`auth`**, **`context.session_id`**, transport-agnostic messages). It does **not** standardize:

- how a TV and a user account are **linked** (pairing UX), or  
- how **device credentials** are issued and stored.

Those are **deployment / product** concerns. This document gives **implementation-agnostic suggestions** so teams can document a **small, consistent** approach aligned with **[PROTOCOL §7](../PROTOCOL.md)** (authentication and secrets) and **[§9](../PROTOCOL.md)** (`context`).

---

## 2. Example pairing UX (not normative)

A common pattern (e.g. TV + OpenClaw server):

1. User opens “conversation” on **Android TV**; the TV displays a **short human-readable code** (letters + digits), with a **time limit**.
2. On the **server / CLI** (next to OpenClaw), the user runs a command and **enters the same code** to approve linking **this TV** to **this account / tenant**.

**Length:** pick one fixed length (e.g. 6 or 8 characters) in product docs; avoid mixing lengths.

This flow is **compatible** with OpenHarness: the **pairing step** is usually implemented as your **own HTTPS (or internal) pairing API**, not as a required global standard inside every `request` body.

---

## 3. Where OpenHarness starts

After pairing succeeds:

- Issue a **long-lived device credential** (opaque token, refresh token, or **mTLS client certificate**) and store it in **secure storage** on the TV (e.g. Android Keystore, EncryptedSharedPreferences).
- For every OpenHarness call, prefer **transport-layer authentication** (TLS + `Authorization` / mTLS) per **PROTOCOL §7**.
- Put stable references in **`request.request.auth`** (e.g. **`tenant_id`**, **`credential_ref`**) as your gateway resolves them — **do not** rely on plaintext long-lived secrets in the JSON body when avoidable.
- Use a **stable `context.session_id`** for the **user ↔ Engine conversation line** (recommended in PROTOCOL §9). Persist it on the device after pairing so “one pairing” maps to “one long-lived dialogue line” unless the user explicitly starts a **new** conversation.

**Optional:** the first OpenHarness `request` after pairing may carry pairing metadata in **`extensions`** — only if your Engine understands it; many teams keep pairing **fully outside** the Harness JSON for simplicity.

---

## 4. “Pair once, use for a long time” (simplest shape)

| Concern | Suggested approach |
|--------|---------------------|
| **Identity** | One-time pairing → server returns **device token** (or cert); gateway validates on every request. |
| **Silent renewal** | Short-lived access tokens + **refresh** on the device so users rarely re-pair; revoke on server if device is lost. |
| **Conversation line** | Stable **`session_id`** stored on TV after pairing; reuse for ongoing Q&A. |
| **Revocation** | Server-side device blocklist / credential rotation; document in ops guides. |

This keeps the **user-visible** flow “pair once,” while the system may still **rotate secrets** under the hood.

---

## 5. Security checklist (product; not exhaustive)

- Short **TTL** for the **on-screen pairing code**; rate-limit verification attempts.
- **Do not** log pairing codes or raw long-lived tokens.
- Prefer **TLS** for all pairing and Harness traffic.
- Align with **PROTOCOL §7** and your **`privacy_tier`** policy for **`environment_state`** if the Shell sends UI or device metadata.

---

## 6. Related documents

| Document | Why |
|----------|-----|
| **[PROTOCOL.md](../PROTOCOL.md)** §7, §9 | `auth`, `session_id`, secrets |
| **[profiles/im-bot-shell.md](../profiles/im-bot-shell.md)** | Who owns platform IDs → `context`; Engine truth tables |
| **[profiles/http-transport.md](../profiles/http-transport.md)** | Optional `X-Correlation-ID` / tracing with HTTP |
| **[shell-at-scale.md](./shell-at-scale.md)** | Where to host Shell-specific docs and external repo links |
| **[adapters/openharness-adapter-openclaw/README.md](../../adapters/openharness-adapter-openclaw/README.md)** | Optional **local `demo-server`** walk-through (reference only; not a production pairing service) |

---

## 7. Reference demo in this repository (optional)

The **`openharness-adapter-openclaw`** adapter includes a **stdlib-only** local HTTP demo: create pairing code → confirm → issue Bearer token → POST JSON to a **mock** Harness endpoint (`demo-server`, …). It also includes an optional **SQLite example** (`pair-server`, `pair-create`, `pair-confirm`) for a slightly more durable pairing store — still **reference only**; **replace** with your own HTTPS + storage + Engine for production. See the adapter README; **you are not required** to keep pairing code in this repository.

---

## 中文

**性质：** 资料性建议；**不修改** **[PROTOCOL.md](../PROTOCOL.md)**。面向需要在 **电视等设备** 与 **服务器/CLI（如 OpenClaw 侧）** 之间做 **一次性配对** 并 **长期使用** 的 Shell 团队。

### 要点

- **配对（电视展示验证码、服务器上输入命令确认）** 属于 **你们自己的账号/设备服务**，通常用 **独立 HTTPS 接口** 完成即可；OpenHarness **不要求** 把验证码写进规范正文。
- **配对完成后**，用 **TLS + `Authorization` / mTLS** 建立传输层身份（**PROTOCOL §7**），JSON 里用 **`tenant_id`、`credential_ref`** 等 **引用**；在电视上 **安全存储** 长期设备凭证。
- **长期对话线**：为 **`context.session_id`** 制定 **稳定、可复现** 的规则（与 **[im-bot-shell.md](../profiles/im-bot-shell.md)** 一致），配对成功后写入电视并复用，直到用户主动「新会话」或你们策略重置。
- **用户侧「只配对一次」**：可在后台做 **token 刷新 / 轮换**，避免频繁让用户重新输入验证码。

### 与协议的关系

OpenHarness 管 **配对之后** 每条 **`request` / `response`** 的线格式与行为；**谁和谁绑定、验证码几位** 由 **产品约定** 写在 **Shell/网关文档** 中，并与本文建议一并维护即可。

### 本仓参考演示（可选）

**`openharness-adapter-openclaw`** 提供本机 **`demo-server`** 与可选 **`pair-server`**（SQLite 示例）等命令，仅用于开发者走通「发码 → 确认 → Bearer」；**不能** 替代生产环境的 HTTPS、账号库与真实 Harness；**不** 要求配对逻辑长期留在本仓库。命令见 **[adapters/openharness-adapter-openclaw/README.md](../../adapters/openharness-adapter-openclaw/README.md)**。
