# Profile: Lark / Feishu Open Platform CLI ↔ OpenHarness (Informative)

**Status:** Informative only. **Does not** change **[PROTOCOL.md](../PROTOCOL.md)**. For vendor-neutral Shell responsibilities, see **[im-bot-shell.md](./im-bot-shell.md)**. For Shell-at-scale documentation placement, see **[../guides/shell-at-scale.md](../guides/shell-at-scale.md)**.

**Upstream tool:** [larksuite/cli](https://github.com/larksuite/cli) — the official **Lark / Feishu** Open Platform command-line tool (`npm` package `@larksuite/cli`), with **Agent Skills**, shortcuts, curated API commands, and raw Open Platform calls. **Feishu**, **Lark**, and related marks are trademarks of their respective owners; this document is **not** the official Open Platform specification.

**Language:** English first · [中文](#中文)

---

## 1. Purpose

This profile helps teams that use **lark-cli** (or embed the same OAuth / API patterns) to produce **conformant OpenHarness** `request` messages for a **Harness Engine** (e.g. routing, SOPs, tools). It maps **typical** CLI concepts to **`request.context`** and related fields. **Platform field names and API versions change** — verify against [larksuite/cli](https://github.com/larksuite/cli) and the current **Lark/Feishu Open Platform** docs before implementation.

---

## 2. What lark-cli provides (summary)

From the upstream project ([larksuite/cli](https://github.com/larksuite/cli)):

- **Install:** `npm install -g @larksuite/cli`; optional **Skills:** `npx skills add larksuite/cli -y -g`.
- **Config & auth:** `lark-cli config init`, `lark-cli auth login` (scopes, `--recommend`, `--no-wait` / device code for agents). Credentials are stored in an **OS-native** way (keychain); see upstream **Security** section.
- **Domains:** Messenger (IM), Docs, Drive, Sheets, Base, Calendar, Mail, Tasks, Meetings, Contacts, Wiki, Events (WebSocket subscriptions), and more.
- **Command layers:** Shortcuts (`+`), curated **API commands** aligned to Open Platform endpoints, and **`lark-cli api`** for arbitrary REST paths.
- **Relevant Skills for Shell-like integrations:** e.g. `lark-im` (messages, chats, media), `lark-drive` (upload/download), `lark-event` (real-time events), `lark-shared` (app config, auth).

OpenHarness does **not** embed these commands; your **Shell** (wrapper, daemon, or agent) invokes them or shares the same tokens and then **builds JSON** for the Engine.

---

## 3. Mapping to OpenHarness (recommended practices)

Platform identifiers named in the tables below (e.g. `chat_id`, `oc_…`) are **illustrative**; confirm names and semantics against current Open Platform and [larksuite/cli](https://github.com/larksuite/cli) documentation (**§1**).

### 3.1 Identity and tenancy

| Goal | OpenHarness field | Notes |
|------|-------------------|--------|
| Stable tenant / app scope | `request.auth.tenant_id` | Use your internal tenant key or the app’s stable identifier as documented for your deployment. **Do not** put long-lived secrets in the JSON body; prefer transport auth or opaque **`credential_ref`** (PROTOCOL §7). |
| Tracing | `request_id`, `correlation_id` | Set per user message or CLI invocation; echo for logs. Optional HTTP header hints: **[http-transport.md](./http-transport.md)**. |

### 3.2 Session and conversation

| Lark / Feishu side (concepts) | OpenHarness field | Notes |
|-------------------------------|-------------------|--------|
| Chat / channel (e.g. `chat_id`, `oc_…`) | `context.conversation_id` and/or part of `context.session_id` | Pick **one deterministic rule** (e.g. hash or prefixed string) and **version it** in your Shell product docs. |
| Thread / topic (if used) | `context.conversation_id` (sub-thread) or `extensions` | Align with your UX: one Engine “line” per chat vs per thread. |
| Long-lived user ↔ Engine line | `context.session_id` | Must be **stable** across turns for resume and analytics; see **[im-bot-shell.md](./im-bot-shell.md)** §3. |

### 3.3 User intent and continuation

| Source | OpenHarness field |
|--------|-------------------|
| Message text, command output, or card callback payload | `context.user_intent` |
| SOP / workflow hints | `context.task_hint` (e.g. `sop_id`, business keys) |
| Engine-issued resume | `context.continuation` (`run_id`, `continuation_token`, …) — opaque round-trip |

See **`examples/im-cli/request.json`** for a shape that matches IM-style Shells.

### 3.4 Shell metadata

Set **`request.context.shell`**, for example:

- `shell_kind`: `"lark_cli"` or `"feishu_cli"` (choose one and keep it stable for your product; namespaced strings are allowed per PROTOCOL §6).
- `shell_version`: your wrapper or `lark-cli` version string.
- `locale`, `timezone`: from user or environment.

### 3.5 Capabilities

Declare only what the Shell **actually** implements (cards, attachments upload, parallel directives, etc.). Handle **`capability_denials`** and **`supported_capabilities`** in the Engine response — no silent half-features (**[AI_INTEGRATION.md](../guides/AI_INTEGRATION.md)**).

### 3.6 Attachments

PROTOCOL requires **references** in the body (§9.1), not large base64 blobs. Typical pattern:

1. Use **Drive / IM file APIs** (via `lark-cli` or direct HTTP) to obtain a **file key**, **resource ID**, or URL your deployment recognizes.
2. Map that to **`attachments[].ref_id`** and/or **`uri`** / **`asset_id`** per your **joint Shell + Engine** contract (**[im-bot-shell.md](./im-bot-shell.md)** §2).

### 3.7 Engine connection

How the Shell **reaches** the Harness Engine (base URL, TLS, API keys, parsing **`credential_ref`**) is defined by **Engine deployment / gateway docs**, not by lark-cli. The Open Platform HTTP API and the Engine HTTP API are **two different things**.

---

## 4. Action directives and unknown types

The Engine returns **`response.action_directives`** with **`action_type`** and **`payload`**. Your Shell must implement **known** types and follow PROTOCOL **§11** for unknown types (no side effects; skip or safe degrade). The Engine should publish a **truth table** of supported types and payloads (**[AI_INTEGRATION.md](../guides/AI_INTEGRATION.md)** §5).

---

## 5. Security and operational risk (read upstream)

[larksuite/cli](https://github.com/larksuite/cli) documents that AI Agents can drive high-privilege actions; default protections exist but **misuse risk remains**. For OpenHarness integrations:

- Treat **`user_intent`** and structured payloads as **untrusted** unless validated.
- Keep **tokens and secrets** out of logs and out of **`error`** payloads (PROTOCOL §7, §13).
- Align with your org’s policy for **bots in groups**, **scope minimization**, and **human approval** for **`requires_user_approval`** / **`risk_tier`** directives.

---

## 6. Conformance

This profile is **not** part of OpenHarness conformance testing. **Normative** behavior remains **[PROTOCOL.md](../PROTOCOL.md)** and **[schema/openharness-v1.draft.json](../../schema/openharness-v1.draft.json)**; validate messages against the Schema (**[examples/README.md](../../examples/README.md)**).

---

## 中文

**性质：** 资料性；**不修改** **[PROTOCOL.md](../PROTOCOL.md)**。通用 Shell 职责见 **[im-bot-shell.md](./im-bot-shell.md)**；文档落点见 **[shell-at-scale.md](../guides/shell-at-scale.md)**。

**上游工具：** 飞书 / Lark 开放平台官方 CLI — 仓库 **[larksuite/cli](https://github.com/larksuite/cli)**，`npm` 包 **`@larksuite/cli`**，含 **Agent Skills**、快捷命令、与开放平台对齐的 API 命令及原始 `api` 调用。**飞书 / Lark** 等为各自商标；本文**不是**开放平台规范性 API 手册。

### 用途

帮助已使用 **lark-cli**（或相同鉴权/API 模式）的团队，把典型 CLI / IM / 事件场景**映射**到符合 OpenHarness 的 **`request`**，再发往 Harness Engine。**开放平台字段与版本会变更**，实现前务必对照 **[larksuite/cli](https://github.com/larksuite/cli)** 与**当前**开放平台文档。

英文 **§3** 表格中的平台标识（如 `chat_id`、`oc_…`）均为**举例**；名称与语义仍以 **用途** 一节及当前文档为准。

### 与 OpenHarness 的对应关系（摘要）

- **租户 / 追踪：** `auth.tenant_id`（按部署约定）、`request_id` / `correlation_id`；HTTP 头惯例见 **[http-transport.md](./http-transport.md)**。  
- **会话：** `session_id` / `conversation_id` 应对 **chat / 话题** 等使用**稳定、可版本化**的编码规则（见 **[im-bot-shell.md](./im-bot-shell.md)**）。  
- **意图与续跑：** `user_intent`、`task_hint`、`continuation`；形状可参考 **`examples/im-cli/`**。  
- **Shell 元数据：** `context.shell`（如 `shell_kind`: `lark_cli` / `feishu_cli`）。  
- **能力：** 诚实声明 **`capabilities`**，并处理 **`capability_denials`**。  
- **附件：** 正文仅 **引用**（§9.1）；上传与 **`ref_id` 解析** 由 **Shell 与 Engine 联合约定**。  
- **访问 Engine：** 与 lark-cli **无关**，以 **Engine 部署/网关** 文档为准。

### 安全

请参阅上游 **[larksuite/cli](https://github.com/larksuite/cli)** 的安全说明；对接 OpenHarness 时仍须遵守 PROTOCOL 对密钥、**`error`** 安全载荷及 **`action_type`** 未知时的行为（§11）。

### 符合性

本文**不参与**核心协议符合性测试；以 **PROTOCOL + Schema + 金样** 为准。
