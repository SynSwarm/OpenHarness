# Adapters (optional Shell-side code)

**Status:** Informative. **Does not** change **[PROTOCOL.md](../docs/PROTOCOL.md)**. The **normative** contract remains the wire JSON + **[Schema](../schema/openharness-v1.draft.json)**.

**Language:** English first · [中文](#中文)

---

## What belongs here

This directory is for **optional** projects that run **on the Shell side** (desktop, CLI, TV, mobile, embedded) and:

- **Emit** conformant OpenHarness **`request`** messages toward a **Harness Engine**, and  
- **Consume** **`response`** / **`action_directives`** (render, execute, degrade per PROTOCOL §11).

Typical reasons to build an adapter:

- The **host environment** (e.g. a third-party agent runtime, legacy CLI, or TV OS) does **not** natively speak OpenHarness JSON; you need a **thin bridge** (library, daemon, or app) that maps local APIs ↔ wire format.
- You want a **reference** implementation others can copy or fork.

**Adapters are not part of protocol conformance testing.** Correctness is still defined by **PROTOCOL + Schema + examples**.

---

## Naming (suggested)

Use predictable names so discoverability stays high:

| Pattern | Example |
|---------|---------|
| `openharness-adapter-<platform>` | `openharness-adapter-android-tv` |
| `OpenHarness-<language>-<target>` (community style) | `OpenHarness-py-claw` (Python bridge to a specific runtime) |

Pick **one** convention per product line and document it in the adapter’s own README.

---

## Monorepo here vs separate repository

| Situation | Suggestion |
|-----------|------------|
| **Thin** library, shared with docs/CI in one place, few dependencies | May live under **`adapters/<name>/`** in this repo (subfolder per adapter). |
| **Heavy** apps (full Android TV APK, large Python stacks, frequent releases) | Prefer a **dedicated repository** per adapter; link it from this README or from **[shell-at-scale.md](../docs/guides/shell-at-scale.md)**. Keeps the protocol repo’s PR noise and CI time manageable. |

Nothing prevents starting **in-tree** and **graduating** to a new repo when the codebase grows.

---

## Illustrative scenarios (not commitments)

- **Python bridge:** A process that sits next to a **third-party agent runtime** that exposes its own IPC or HTTP; the bridge translates between that surface and OpenHarness JSON (still Shell-side responsibility to fill **`context`**, **`shell`**, **`capabilities`** per **[im-bot-shell.md](../docs/profiles/im-bot-shell.md)**).
- **Android TV Shell:** An APK that acts as the **Shell**: captures remote / UI / leanback context, sends **`request`**, renders **`render_ui`** / **`render_message`** (or degrades per §11).

Engine deployment (base URL, TLS, **`credential_ref`** resolution) remains **outside** these adapters — see profiles and Engine docs.

---

## Contributing an adapter

1. Keep **PROTOCOL** authoritative; do not fork the wire semantics inside adapter code comments as “the spec.”  
2. Prefer **validating** outbound/inbound JSON against the **Schema** in CI (same idea as **`scripts/validate_examples.py`**).  
3. Add a **short row** to the table below (or open a PR that only updates this README with a link to an external repo).

### Registry (informative)

| Adapter / repo | Platform / language | Notes |
|----------------|---------------------|--------|
| **[openharness-adapter-openclaw](./openharness-adapter-openclaw/)** | Python (Shell-side helper) | **Integrator-owned** OpenClaw ↔ OpenHarness: **`bridge-*`**, optional **`pair-server`** (SQLite pairing example), **`demo-*`**; pairing → **[device-pairing-session.md](../docs/guides/device-pairing-session.md)**. |
| **[openharness-adapter-android-tv](./openharness-adapter-android-tv/)** | Android TV (guidance only) | README: reading order + Shell checklist; implement APK in a **separate repo** and link here. |

---

## 中文

**性质：** 资料性；**不修改** **[PROTOCOL.md](../docs/PROTOCOL.md)**。规范性仍以 **线格式 + Schema** 为准。

### 这里放什么

**可选** 的、跑在 **Shell 侧** 的工程：在各类终端上把本地能力 **对接** 成 OpenHarness **`request`** / **`response`**（例如第三方运行时没有原生 OpenHarness、需要 **桥接**；或 **Android 电视 APK** 作为 Shell 采集上下文并执行指令）。

**适配器代码不参与** 协议符合性测试；符合性仍由 **PROTOCOL + Schema + 金样** 定义。

### 命名建议

如 `openharness-adapter-android-tv`、`OpenHarness-py-<target>` 等，保持可发现、可搜索。

### 本仓子目录 vs 独立仓库

- **薄库**、依赖少、与文档一起维护 → 可放在 **`adapters/<name>/`**。  
- **重应用**（完整 APK、大型 Python 栈、独立发版）→ 建议 **独立仓库**，在此 **README** 或 **[shell-at-scale.md](../docs/guides/shell-at-scale.md)** 里 **挂链接**。

可先在本仓落地，再 **毕业** 到独立仓库。

### 说明性场景（非承诺）

- **Python 桥**：旁路第三方智能体运行时，做 IPC/HTTP ↔ OpenHarness JSON。  
- **Android TV**：APK 作为 Shell，填 **`context`**、处理 **`action_directives`**。

访问 Engine 的方式（URL、TLS、密钥）仍由 **Engine 部署文档** 与 **[http-transport.md](../docs/profiles/http-transport.md)** 等资料性说明约束，不在适配器里“私造协议”。

### 登记（资料性）

上表 **Registry**：有 **in-tree** 或 **外链** 项目时在此登记一行即可。当前 in-tree：**[openharness-adapter-openclaw](./openharness-adapter-openclaw/)**（Python CLI；**对接由集成方自建**，上游不自带 OpenHarness）、**[openharness-adapter-android-tv](./openharness-adapter-android-tv/)**（指引文档；具体开发另建仓库后在此挂链）。
