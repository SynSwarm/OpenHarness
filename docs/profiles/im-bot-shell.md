# Profile: IM / bot-platform Shell (Informative)

**Status:** Informative only. **Does not** change **[PROTOCOL.md](../PROTOCOL.md)**. For layering, see **[OVERVIEW.md](../OVERVIEW.md)**.

**Scope:** Shells that connect to an **instant-messaging or bot platform** (tenant isolation, chats, threads, message events) and forward work to a **Harness Engine** using OpenHarness JSON. **No** specific vendor APIs are normative here.

**Language:** English first · [中文](#中文)

---

## 1. Why this profile exists

Bot platforms expose their **own** concepts (tenant identifiers, chat/thread IDs, user IDs, message payloads). OpenHarness exposes **`request.context`** (`session_id`, `conversation_id`, `task_hint`, `continuation`, etc.). **Mapping between the two is not defined by the core protocol**; this profile records **typical responsibilities** and **recommended practices** so Shell and Engine teams do not guess.

---

## 2. Responsibility matrix (who owns what)

| Topic | Primary owner | Notes |
|-------|----------------|-------|
| **Platform IDs → OpenHarness `context`** | **Shell** (CLI, bot adapter, or thin client next to the platform SDK) | The side that **talks to the platform API** should **encode** stable `session_id` / `conversation_id` (and related fields) using a **documented, versioned rule** in **Shell/CLI product docs** or this profile’s conventions. The Engine usually **consumes** already-filled `context`; it does **not** define how platform IDs are shaped. |
| **Transport to the Engine** (base URL, TLS, API keys, how `credential_ref` is resolved) | **Engine deployment / gateway / ops** | Documented in **Engine or infrastructure** docs. The Shell is a **client** that sends OpenHarness-shaped JSON per that deployment’s contract. The bot platform’s own HTTP API is **separate** from “how to call the Harness.” |
| **Attachment pipeline** (upload → `ref_id` → Engine can fetch bytes) | **Joint Shell + Engine** (or a **shared service**) | Rarely one side only. Typical split: Shell uploads via platform file API or object storage and puts a **ref** in `attachments`; Engine documents how **`ref_id` / `uri` / `asset_id`** resolve. If resolution depends on platform file APIs, Shell docs must say so; if it depends on Engine-side storage, Engine docs must say so — **align both**. |
| **Capability & directive truth** (`supported_capabilities`, `action_type` sets, payload shapes, `supported_protocol_versions`, error habits) | **Engine** | The Engine publishes what it **actually** supports; Shell implements rendering, approval UI, and **§11** degradation from that truth table. |

**One line:** **Shell** maps the chat platform into **`context`**; **Engine deployment** defines how to **reach** the Engine and what it **emits**; **attachments** need a **cross-team** contract; the **Engine** publishes **capabilities and directives**.

---

## 3. Mapping conventions (recommended, not mandatory)

Implementations SHOULD use **stable, deterministic** strings for:

- **`session_id`** — correlate a **long-lived user ↔ Engine** line (may combine tenant + user principal, per your privacy model).
- **`conversation_id`** — sub-thread within that line (e.g. per-chat or per-topic), if the platform distinguishes it.

Store the mapping rule in **Shell product documentation** or a versioned appendix. Use **`continuation`** / **`continuation_token`** for **resume** flows when the platform supports “continue from last card” semantics.

Set **`shell_kind`** to a stable string (namespaced if needed) so Engines can tune response shape without normative coupling to one vendor.

---

## 4. What the OpenHarness repo does *not* provide

- Normative **Open Platform** REST/WebSocket specifications.
- A single global **HTTP mapping** for all Engines (transport-agnostic core); optional **transport profiles** may be added separately.
- Guaranteed **attachment** storage — only **reference** shapes in PROTOCOL §9.1.

---

## 5. Related materials in this repository

- **[../guides/AI_INTEGRATION.md](../guides/AI_INTEGRATION.md)** — checklists, anti-patterns, AI context block.
- **`examples/im-cli/`** — illustrative request/response JSON for IM-style Shells (vendor-neutral filenames).

---

## 中文

**性质：** 资料性；**不修改** **[PROTOCOL.md](../PROTOCOL.md)**。分层见 **[OVERVIEW.md](../OVERVIEW.md)**。

**适用范围：** 对接 **即时通讯 / 机器人平台**（租户、会话、话题、消息事件等），并把工作交给 **Harness Engine** 的 Shell。本文**不**规范任何特定厂商的开放平台 API。

### 职责矩阵（谁负责什么）

| 事项 | 主责 | 说明 |
|------|------|------|
| **平台侧 ID → OpenHarness `context`** | **Shell**（CLI、机器人适配器、贴近平台 SDK 的薄客户端） | 与平台 API 打交道的一方负责把租户/会话/线程等 **编码** 进 `session_id`、`conversation_id` 等，规则写在 **Shell/CLI 产品文档** 或本文惯例；**Engine 通常只消费已填好的 context**，一般不定义平台 ID 长什么样。 |
| **访问 Engine 的传输**（base URL、TLS、密钥、`credential_ref` 如何解析） | **Engine 部署 / 网关 / 运维** | 写在 **Engine 或基础设施** 文档；Shell 按该约定作为 **客户端** 发 OpenHarness JSON。**机器人平台的 HTTP** 与 **如何调用 Harness** 是两件事。 |
| **附件流水线**（上传 → `ref_id` → Engine 能取内容） | **Shell + Engine（或共享服务）联合** | 很少单归一方。常见：Shell 经平台文件能力或对象存储上传，正文只放 **引用**；Engine 说明 **ref 如何解析**。绑平台能力则 Shell 文档要写清；绑 Engine 存储则 Engine 文档要写清，**两边对齐**。 |
| **能力与指令真值表** | **Engine** | Engine 发布真实 **capabilities**、**action_type**、**payload** 习惯、**supported_protocol_versions**、错误习惯；Shell 据此渲染与 **§11** 降级。 |

**一句话：** Shell 把 **聊天平台世界** 装进 **`context`**；**Engine 部署方** 定义 **怎么连上 Engine、发什么指令**；**附件** 要 **联合约定**；**Engine** 给出 **能力与指令真值**。

### 映射惯例（建议，非强制）

对 **`session_id`**、**`conversation_id`**、**`continuation`** 等使用 **稳定、可复现** 的编码规则，并写在 **Shell 产品文档** 中。为 Engine 区分回复形态，设置稳定的 **`shell_kind`**（必要时用命名空间）。

### 本仓库**不提供**什么

- 各厂商 **开放平台** 的规范性 HTTP 全文。  
- 适用所有 Engine 的 **唯一** HTTP 规范（核心协议传输无关）。  
- 统一的附件存储实现 —— 协议层只有 **引用** 形状（PROTOCOL §9.1）。

### 相关链接

- **[../guides/AI_INTEGRATION.md](../guides/AI_INTEGRATION.md)**  
- **`examples/im-cli/`** 示例 JSON
