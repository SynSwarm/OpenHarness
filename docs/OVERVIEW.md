# OpenHarness — Architecture Overview (Informative)

**Status:** Informative narrative companion to the normative specification. **Does not replace** **[PROTOCOL.md](./PROTOCOL.md)** or the **[JSON Schema](../schema/openharness-v1.draft.json)**. For repository boundaries, see **[SCOPE.md](./SCOPE.md)**.

**Language:** English first · [中文](#中文)

---

## Why this document

Building OpenHarness is, in essence, maintaining a **cross-platform agent communication contract**: **what** JSON means, not **how** any particular Engine (DeskHarness, fastClaw, etc.) executes it. This page groups that work into **three layers** so we do not overfit one product (e.g. desktop automation) into the **only** core protocol.

---

## Three layers

| Layer | What it is | Where it lives |
|-------|------------|----------------|
| **1. Normative core** | Wire envelope, `context`, `action_directives`, errors, versioning, capabilities, privacy/credential rules | **[PROTOCOL.md](./PROTOCOL.md)** + **Schema** |
| **2. Profiles (informative)** | Recommended `action_type` names and `payload` shapes for a **class** of Shells (desktop automation, IM, TV, …). Shells/Engines opt in via **`capabilities`**. | Future appendices under `docs/profiles/` (to be added); not a single global primitive set for all deployments |
| **3. Transport & execution feedback** | HTTP header conventions (optional profile), streaming, post-execution state push | **§15** of PROTOCOL (streaming informative today); **roadmap** — follow-up requests with `continuation` / `environment_state` vs future **event** channels |

**Rule of thumb:** If a feature only applies to **some** Shells (mouse, rich cards, outbound HTTP), it belongs in **Layer 2 or 3**, not as a universal MUST in Layer 1 unless it is truly cross-cutting (e.g. `request_id`, `privacy_tier`).

---

## Layer 1 — Northbound: how Shells speak (“input dictionary”)

The protocol defines **structured** context, not one fixed sensor format.

- **`user_intent`** — how the user’s command is expressed (natural language or structured).
- **`environment_state`** — device/UI/surroundings with **`privacy_tier`** (`public` / `restricted` / `secret`).
- **`attachments`** — **references** (`ref_id`, `uri`, `asset_id`); **no** large base64 blobs in the message body (see PROTOCOL §9.1).
- **`task_hint`**, **`continuation`**, **`session_id`**, **`conversation_id`** — routing and resume without stuffing everything into a raw prompt.

So we standardize **what classes of data** may appear and **how they are labeled**, not “everyone must send a full-screen Base64 screenshot.” Different Shells (Feishu, desktop agent, TV) choose what they can legally send.

---

## Layer 1 — Southbound: action directives (“action primitives”)

The **core** defines:

- **`action_type`** + **`payload`**, with a **registry** and **namespaced** types (PROTOCOL §10–12).
- **Unknown types** — Shells MUST NOT run side effects for unknown `action_type` values (§11).

**Optional profiles** (Layer 2) can spell out **recommended** types for a vertical, for example:

- **Desktop automation profile** — e.g. mouse/keyboard/window operations with agreed payload shapes (names to be prefixed, e.g. `openharness.desktop.*`, to avoid implying every Shell supports mice).
- **IM profile** — e.g. `render_message`, card payloads, `noop`.

Defining **`CALL_API`-style** primitives in a profile requires extreme care (security, consent, auditing); such types should remain **profile-specific** and **capability-gated**, not global MUSTs.

---

## Layer 3 — State handshake and execution feedback

v1 **normative** text is primarily **request → response** (including `action_directives`). Full **normative** “after `simulate_action`, push new screenshot/state back in one standard event JSON” is **not** yet part of the core.

Practical paths today:

- **Next OpenHarness request** carrying updated **`environment_state`** and/or **`continuation`**.
- Future **streaming / event profile** (PROTOCOL §15) for chunked or push feedback.

Document roadmap items in **profiles** or a **separate execution-feedback note** when ready — without claiming they are already normative v1.

---

## Auth & metadata (“slots”, not billing logic)

- **JSON body**: **`auth`** (`tenant_id`, `credential_ref`, …), **`context.session_id`**, **`correlation_id`**, **`request_id`** — transport-agnostic and suitable for multi-tenant and tracing.
- **HTTP**: OpenHarness does **not** require specific headers for **all** transports; an optional **HTTP transport profile** may **recommend** mapping `correlation_id` / tenant to headers for gateways that use HTTP. **Billing/commercial policy** stays outside the protocol.

---

## How to read the repo

1. **[PROTOCOL.md](./PROTOCOL.md)** — authoritative wire format.  
2. **[SCOPE.md](./SCOPE.md)** — what belongs in this repository vs Engine products.  
3. **This OVERVIEW** — narrative and layering; use for onboarding and whitepaper-style explanations.  
4. **Profiles** (as they appear) — optional, scenario-specific recommendations.

---

## 中文

**性质：** 资料性导读，**不替代** **[PROTOCOL.md](./PROTOCOL.md)** 与 **Schema**。仓库边界见 **[SCOPE.md](./SCOPE.md)**。

### 三层结构

| 层级 | 含义 | 位置 |
|------|------|------|
| **1. 规范核心** | 线格式、`context`、`action_directives`、错误、版本、能力、隐私与密钥规则 | **PROTOCOL.md** + **Schema** |
| **2. Profile（资料性）** | 面向某类 Shell 的 **推荐** `action_type` 与 `payload`；通过 **`capabilities`** 声明支持 | 未来 `docs/profiles/` 等附录；**不是**全球统一的唯一「原子指令表」 |
| **3. 传输与执行反馈** | HTTP 头惯例（可选 Profile）、流式、执行后状态回传 | PROTOCOL **§15**；路线图：下一轮请求带 `continuation`/`environment_state` 或未来 **事件通道** |

**经验法则：** 只适用于 **部分** Shell（鼠标、富卡片、外呼 HTTP）的能力，放在 **第 2/3 层**；除非真正跨场景，否则不抬成 **第 1 层** 的全局 MUST。

### 北向（Shell → Engine）

规定 **结构化上下文** 与 **隐私/引用**，**不**规定「全世界必须同一种采集方式」（如一律 Base64 全屏截图）。详见 PROTOCOL **`user_intent`**、**`environment_state` + `privacy_tier`**、**`attachments` 引用**、**`task_hint` / `continuation`** 等。

### 南向（Engine → Shell）

**核心** 为 **`action_type` + `payload`**、注册表、**§11 未知类型** 行为。桌面鼠标键盘、IM 卡片等 **细粒度「原子」** 宜放在 **Profile**，并用 **capabilities** 协商，避免把单一场景绑死成唯一标准。

### 握手与执行回传

v1 **正文** 以 **请求—响应** 为主；「执行完再推一帧标准事件 JSON」若要做，放在 **路线图 / 独立 Profile**，与 **§15** 流式衔接，**勿**与当前 normative 核心混为一谈。

### 鉴权与元数据

**正文** 内 **`auth`、`session_id`、`correlation_id`** 等槽位，**传输无关**；HTTP Header 强制方案仅适合 **可选传输 Profile**。**计费/商业策略** 不在协议层定义。

### 阅读顺序

1. **PROTOCOL.md**（权威）  
2. **SCOPE.md**（边界）  
3. **本文**（叙事与分层）  
4. **各 Profile**（随仓库增补）
