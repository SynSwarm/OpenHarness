# OpenHarness — Protocol Scope and Maintainer Boundaries

**Language:** English first. [中文](#中文) below.

This document clarifies **what OpenHarness is**, **what belongs in this repository**, and **what stays with Shell or Engine products** (third-party or in-house **Harness Engine** implementations). It is **informative**; the **normative** wire format remains **[PROTOCOL.md](./PROTOCOL.md)**. For a **three-layer narrative** (core vs profiles vs transport/feedback), see **[OVERVIEW.md](./OVERVIEW.md)**.

---

## What OpenHarness is

OpenHarness is a **transport-agnostic JSON message contract** between:

- **Shell** — any client, CLI, IM bot, device, or OS node that sends intent and environment context; renders or executes **action directives**.
- **Harness Engine** — any server-side implementation that performs routing, SOP/state machines, tools, safety, and returns directives.

The protocol does **not** depend on a specific commercial Engine, operating system, or agent stack. Replacing one Engine implementation with another **does not** require a different OpenHarness “flavor” — only that the Engine **honors the same wire semantics** (or explicitly declares a supported subset / profile).

---

## Hard boundaries

| In scope for this repository (maintainers) | Out of scope (integrators / product teams) |
|--------------------------------------------|---------------------------------------------|
| **Normative wire JSON**: envelope, `context`, `action_directives`, errors, unknown `action_type` behavior, versioning, capabilities | **Engine internals**: model routing, tool runtime, SOP code, whether the stack is lightweight or monolithic |
| **Schema** (`schema/openharness-v1.draft.json`) aligned with **PROTOCOL.md** | **Concrete APIs**: REST paths, gRPC services, process names, deployment topology |
| **Privacy / credential guidance** in the spec (`privacy_tier`, `credential_ref`, no large secrets or raw binaries in the body) | **Operational policies**: which fields a given Shell may upload, audit logs, compliance programs |
| **Optional, non-normative docs**: integration guides, informative profiles (IM/CLI/etc.), fixtures, capability catalogs — they **must not** redefine normative meaning | **Adapters**: OpenHarness JSON ↔ product-internal DTOs/HTTP; **versioned mapping tables** to legacy APIs |
| **Wishlists / mappings** from collaborators and integrators | Those documents **do not override** **PROTOCOL.md** (stated there as well) |

**One line:** OpenHarness defines **what the JSON looks like and how to negotiate and fail**; it does **not** define **how your Engine is built or which brand ships it**.

---

## Maintainer work (OpenHarness)

**Core (ongoing)**

- Keep **PROTOCOL.md** (English, authoritative), **PROTOCOL.zh.md**, and the **JSON Schema** consistent and versioned.
- Evolve compatibility rules and schema; decide what becomes **normative** vs **informative**.

**Ecosystem (optional but valuable)**

- Integration guides, informative profiles, **examples/fixtures**, registries of recommended `shell_kind` / capability IDs (recommendations, not closed enums).
- Transport “profiles” as **recommendations** (e.g. HTTP headers aligned with `correlation_id`), separate from wire semantics.

**Not assumed by default**

- Shipping or maintaining **third-party Engine product code** inside this repo unless the project explicitly chooses to host a reference implementation.

---

## When swapping or integrating a different Engine

| Party | Typical responsibility |
|-------|------------------------|
| **OpenHarness maintainers** | Stable spec + schema; optional generic notes for Engine implementers (e.g. filling `supported_capabilities`, emitting compliant directives, §11 unknown types). |
| **Engine team** | Implement Harness Engine semantics behind their gateway: parse requests, emit valid responses; map internally to their runtime. |
| **Shell** | Send conforming requests; if the Engine supports only a **subset**, expect explicit **`capability_denials`** or **errors**, not silent partial behavior. |

The **OpenHarness repository’s responsibility table does not change** when the Engine vendor changes — only **who implements the Engine** changes.

---

## 中文

本文说明 **OpenHarness 是什么**、**本仓库负责什么**、**哪些工作属于 Shell 或各 Harness Engine 产品实现**（第三方或自研 **Engine**）。本文为 **资料性**；**规范性**线格式仍以 **[PROTOCOL.md](./PROTOCOL.md)** 为准。**三层叙事**（核心 / Profile / 传输与反馈）见 **[OVERVIEW.md](./OVERVIEW.md)**。

### OpenHarness 是什么

OpenHarness 是 **Shell** 与 **Harness Engine** 之间的 **与传输无关的 JSON 消息契约**，**不**绑定某一商业 Engine、某一操作系统或某一套 Agent 栈。更换 **Engine 实现**（例如换供应商或换自研版本）**不需要** 另起一套「OpenHarness 变体」；只要 Engine **遵守同一套线格式语义**（或声明所支持的子集 / profile）即可。

### 边界（简表）

| 本仓库（OpenHarness 维护者） | 外部（集成方 / 产品团队） |
|------------------------------|----------------------------|
| 规范性 **wire JSON**、**Schema**、隐私与密钥指引 | Engine **内部实现**、具体 **HTTP/gRPC/进程** 形态 |
| 可选 **非规范性** 文档：集成指南、Profile、fixtures、能力词典 | **适配器**、与内部 API 的 **版本化映射表** |
| 协作者的 Wishlist / 映射文 **不替代** PROTOCOL | 各产品自建 |

**一句话：** OpenHarness 管 **JSON 长什么样、如何协商、如何失败**；**不管** Engine 用哪家技术栈实现、品牌叫什么。

### 维护者工作内容

- **核心**：维护 PROTOCOL、中文对照、Schema 与版本演进。  
- **生态（可选）**：集成指南、informative Profile、示例与注册表推荐值。  
- **默认不包含**：在仓库内长期维护某一第三方 Engine 的完整产品代码（除非项目明确纳入）。

### 更换或对接不同 Engine 时

| 角色 | 职责 |
|------|------|
| **OpenHarness 维护者** | 规范与 Schema；可选通用实现提示。 |
| **Engine 方** | 在自身网关中实现 Engine 语义并做内部映射。 |
| **Shell** | 按协议发请求；子集能力应通过 **`capability_denials`** 或 **错误** 显式体现。 |

**换 Engine 供应商不改变 OpenHarness 仓库的职责划分**，只改变 **谁来实现 Engine**。
