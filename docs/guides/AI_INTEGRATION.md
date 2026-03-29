# AI-assisted & third-party integration guide (Informative)

**Status:** Informative. **Normative** text remains **[PROTOCOL.md](../PROTOCOL.md)**. Boundaries: **[SCOPE.md](../SCOPE.md)**. Layering: **[OVERVIEW.md](../OVERVIEW.md)**.

**Audience:** OpenHarness maintainers, **third-party Harness** teams, **Shell** builders (CLI, IM/bot adapters, devices), and **coding assistants** (LLMs) used to implement adapters.

**Language:** English first · [中文](#中文)

---

## 1. What to read, in order

| Order | Document | Why |
|-------|----------|-----|
| 1 | **[PROTOCOL.md](../PROTOCOL.md)** | Wire format, §11 unknown `action_type`, errors, capabilities |
| 2 | **[schema/openharness-v1.draft.json](../../schema/openharness-v1.draft.json)** | Validatable shape for request vs response messages |
| 3 | **[examples/README.md](../../examples/README.md)** | Golden JSON + validation notes |
| 4 | **[SCOPE.md](../SCOPE.md)** | What belongs in the protocol repo vs your product adapter |
| 5 | **[shell-at-scale.md](./shell-at-scale.md)** | Where to put guides vs profiles for Shells **at scale** (CLI, bots, multi-tenant); keeps PROTOCOL vendor-neutral |
| 6 | **[profiles/im-bot-shell.md](../profiles/im-bot-shell.md)** | Vendor-neutral: who maps platform IDs into `context`, who documents transport to the Engine, attachment pipelines, Engine truth tables |
| 7 | **[profiles/feishu-lark-cli.md](../profiles/feishu-lark-cli.md)** | Optional: [larksuite/cli](https://github.com/larksuite/cli) (Lark/Feishu Open Platform CLI) → OpenHarness field mapping |
| 8 | **[device-pairing-session.md](./device-pairing-session.md)** | Optional: TV/device pairing codes, long-lived device tokens, stable `session_id` — **informative**; does not change PROTOCOL |
| 9 | **[implementer-orientation.md](./implementer-orientation.md)** | **Shell vs Engine**, what lives in `adapters/openharness-adapter-openclaw/` vs TV APK, v1 Q&A without a monolithic Engine — for **humans and AI agents** (e.g. OpenClaw) |
| 10 | **[openclaw-operator-kit.md](./openclaw-operator-kit.md)** | **Gateway + OpenClaw skill pack**: `openharness_server` / `tv_client` drafts → **`bridge-server` + `pair-server`**; generic **Shell ↔ Engine** gateway; **`pair-confirm`**; example **`deskharness.com`** URLs; **§8** Android TV / Shell handoff |

Skipping (2) and fixtures often causes **valid-looking** but **non-interoperable** clients.

---

## 2. Responsibility matrix (summary)

Full detail: **[profiles/im-bot-shell.md](../profiles/im-bot-shell.md)**. Short form:

| Topic | Primary owner |
|-------|----------------|
| **Platform/chat IDs → `request.context`** (`session_id`, `conversation_id`, …) | **Shell / adapter** (the code that talks to the platform API) — document rules in Shell product docs. |
| **How to reach the Engine** (URL, TLS, keys, `credential_ref` resolution) | **Engine deployment / gateway / ops** documentation. |
| **Attachments** (upload → `ref_id` → bytes) | **Shell + Engine** (or shared service) — **joint** contract. |
| **Capabilities & directives** (what the Engine really supports) | **Engine** (published truth table). |

The **OpenHarness spec** does not standardize third-party Open Platform APIs or a single global HTTP surface for all Engines.

---

## 3. Golden fixtures (contract tests & AI context)

The repository includes **machine-readable examples** under **`examples/`**:

- **`examples/minimal/`** — smallest valid request/response pair.
- **`examples/im-cli/`** — illustrative IM-style Shell: `shell_kind`, `task_hint`, `continuation`, attachment **refs** (no base64 in body).

**Use them to:**

- **Contract-test** your serializer/parser (CI: validate JSON against the Schema).
- **Ground LLMs**: paste file paths + key excerpts into the project context so the model does not invent fields.

**Rule:** Generated code MUST produce JSON that **validates** as either `requestMessage` or `responseMessage` per the Schema `oneOf` (validate each file separately).

---

## 4. Implementation checklist (Shell → Engine)

Use this as a human or **LLM task list** when building a Shell or CLI that calls a Harness.

- [ ] Send **`protocol_version`** and top-level **`request`** (see Schema).
- [ ] Set **`request_id`** (and optionally **`correlation_id`**) for tracing and idempotency pairing.
- [ ] Declare **`capabilities`** honestly; handle **`capability_denials`** and **`supported_capabilities`** in responses (no silent “half UI”).
- [ ] Put long-lived secrets in **transport** or **`credential_ref`**, not raw tokens in logs (PROTOCOL §7).
- [ ] Use **`attachments`** as **references** only — **no** large base64 in the body (PROTOCOL §9.1).
- [ ] Classify **`environment_state`** with **`privacy_tier`** when sensitive.
- [ ] On **`action_directives`**: process in order unless `execution` says otherwise; respect **`requires_user_approval`** and **`risk_tier`**.
- [ ] On **unknown `action_type`**: **no side effects**; skip or degrade per PROTOCOL **§11**.

---

## 5. Implementation checklist (Engine / third-party Harness)

- [ ] Echo **`request_id`** and **`correlation_id`** when present.
- [ ] Return **`supported_protocol_versions`** when multiple versions are supported; else reject with **`error.code`** (e.g. `protocol_version_unsupported`).
- [ ] Populate **`supported_capabilities`** / **`capability_denials`** when the Shell asks for features you cannot honor.
- [ ] Emit **`response.error`** with **`code`**, safe **`message`**, optional **`retryable`**, **`details`** on failure (PROTOCOL §13).
- [ ] Do **not** return secrets in **`error`** payloads.
- [ ] Publish a **truth table** for your build: capabilities, `action_type` sets, payload conventions — Shells depend on it.

---

## 6. Anti-patterns (teach your AI to avoid these)

| Anti-pattern | Why it breaks interop |
|--------------|------------------------|
| Embedding **screenshot/base64** or huge blobs in **`context`** | Violates PROTOCOL §9.1; use **`attachments`** refs or uploads. |
| Ignoring **`capability_denials`** and still rendering “rich” UI | Silent mismatch; user sees broken experience. |
| Executing **unknown `action_type`** with real side effects | Violates PROTOCOL §11; security and consistency. |
| Reusing unstable strings as **`session_id`** | Breaks resume and analytics; document your mapping (Shell/adapter docs or **[im-bot-shell.md](../profiles/im-bot-shell.md)**). |
| Assuming **HTTP headers** are normative for all transports | PROTOCOL is transport-agnostic; headers belong in an optional **transport profile**. |

---

## 7. Suggested “context block” for AI coding tools

You can paste the following into a Cursor rule, Copilot chat, or custom instruction when asking the model to implement a Shell or Engine adapter:

```text
You are implementing an OpenHarness client or server.
Source of truth: docs/PROTOCOL.md (normative) and schema/openharness-v1.draft.json.
Validate outgoing/incoming JSON against the Schema (request message vs response message separately).
Follow PROTOCOL §11 for unknown action_type: never execute side effects for unknown types.
Do not put base64 blobs or long-lived API secrets in the JSON body; use attachment refs and credential_ref / transport auth.
Use examples/minimal/ and examples/im-cli/ as golden references.
Read docs/guides/shell-at-scale.md for where guides vs profiles go (CLI, bots, multi-tenant).
Read docs/profiles/im-bot-shell.md for Shell vs Engine responsibilities on IM/bot integrations.
If integrating via the official Lark/Feishu CLI (larksuite/cli), also read docs/profiles/feishu-lark-cli.md.
```

Adjust paths if your monorepo nests OpenHarness as a submodule.

---

## 8. Ecosystem roadmap (non-normative)

**Done in-repo**

- **CI:** `.github/workflows/validate-examples.yml` runs **`python scripts/validate_examples.py`** on every push/PR (`pip install -r requirements-dev.txt`). This prevents **golden JSON drifting** from **`schema/openharness-v1.draft.json`**.
- **Fixtures:** `examples/minimal/response-error.json`, `response-protocol-unsupported.json`, `im-cli/response-capability-denials.json` cover common **error** and **negotiation** paths (not only success).
- **HTTP hints (informative):** **[profiles/http-transport.md](../profiles/http-transport.md)** — optional correlation/header mapping; wire JSON remains transport-agnostic.

**Enhancements (TBD — contributions welcome)**

These items **do not** block a correct **wire** implementation or conformance to **PROTOCOL + Schema**; they improve ergonomics and interop documentation.

- **OpenAPI** for a chosen HTTP mapping (per Engine deployment) — convenience for codegen, not required by the core protocol.
- **Streaming profile** for `openharness.streaming` — see PROTOCOL §15; product-specific until a shared profile lands.
- **More golden fixtures** under `examples/` — additional scenarios welcome; CI validates every `examples/**/*.json` against the Schema.
- **Central registry** of every `action_type` worldwide — not required; interoperability relies on **Engine truth tables** + **namespaced** types (PROTOCOL §12).

---

## 中文

**性质：** 资料性；**权威规范** 仍为 **[PROTOCOL.md](../PROTOCOL.md)**。边界见 **[SCOPE.md](../SCOPE.md)**，分层见 **[OVERVIEW.md](../OVERVIEW.md)**。

**生态路线图（与 §8 对应）：** 仓库已含 **CI Schema 校验**、**错误/协商类金样**、**HTTP 传输提示**（[http-transport.md](../profiles/http-transport.md)）。**OpenAPI、流式 profile、更多金样** 等标为 **增强项（TBD，欢迎 PR）**，**不**构成协议或 wire 正确性的前置条件。

### 面向谁

OpenHarness 维护者、第三方 **Harness**、**Shell/CLI/机器人适配器** 实现者，以及用 **AI 写对接代码** 的开发者。

### 职责矩阵（摘要）

完整说明见 **[profiles/im-bot-shell.md](../profiles/im-bot-shell.md)**：**平台 ID → `context`** 主要由 **Shell/适配器** 编码并写文档；**如何连上 Engine** 由 **Engine 部署/网关** 文档定义；**附件流水线** 需 **Shell 与 Engine（或共享服务）联合约定**；**能力与指令真值** 由 **Engine** 发布。

### 核心建议

1. **阅读顺序**：先 PROTOCOL → 再 Schema → 再 **`examples/`** → **[shell-at-scale.md](./shell-at-scale.md)**（规模化 Shell 资料放哪）→ **`im-bot-shell` profile**；若使用 **官方 Lark/Feishu CLI**（[larksuite/cli](https://github.com/larksuite/cli)），可加 **[feishu-lark-cli.md](../profiles/feishu-lark-cli.md)**；若涉及 **电视/设备配对与长期会话**，见 **[device-pairing-session.md](./device-pairing-session.md)**；**AI 助手或 OpenClaw 先读** **[implementer-orientation.md](./implementer-orientation.md)** 再写代码，避免把「服务端适配器目录」当成电视 APK。  
2. **金样 JSON**：契约测试与 **AI 上下文**；含 **成功 / 错误 / capability_denials** 等（见 **`examples/README.md`**）。**CI** 已用 Schema 校验全部金样。  
3. **清单**：第四节、第五节可作任务列表。  
4. **反模式表**：第六节。  
5. **可复制提示块**：第七节英文块可贴进 Cursor / Copilot。

### 我们（OpenHarness 维护者）还能补什么

- 见 **§8**：**增强项**（OpenAPI、流式 profile、更多金样等）为 **TBD / 欢迎 PR**；**HTTP 提示** 已有 **[http-transport.md](../profiles/http-transport.md)**。
