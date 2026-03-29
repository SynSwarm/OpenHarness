# AI-assisted & third-party integration guide (Informative)

**Status:** Informative. **Normative** text remains **[PROTOCOL.md](../PROTOCOL.md)**. Boundaries: **[SCOPE.md](../SCOPE.md)**. Layering: **[OVERVIEW.md](../OVERVIEW.md)**.

**Audience:** OpenHarness maintainers, **third-party Harness** teams (e.g. fastClaw), **Shell** builders (e.g. Feishu/Lark CLI), and **coding assistants** (LLMs) used to implement adapters.

**Language:** English first · [中文](#中文)

---

## 1. What to read, in order

| Order | Document | Why |
|-------|----------|-----|
| 1 | **[PROTOCOL.md](../PROTOCOL.md)** | Wire format, §11 unknown `action_type`, errors, capabilities |
| 2 | **[schema/openharness-v1.draft.json](../../schema/openharness-v1.draft.json)** | Validatable shape for request vs response messages |
| 3 | **[examples/README.md](../../examples/README.md)** | Golden JSON + validation notes |
| 4 | **[SCOPE.md](../SCOPE.md)** | What belongs in the protocol repo vs your product adapter |
| 5 | **Feishu/Lark profile** (when added under `docs/profiles/`) | Informative mapping: tenant/chat/thread → `session_id` / `conversation_id` |

Skipping (2) and fixtures often causes **valid-looking** but **non-interoperable** clients.

---

## 2. Golden fixtures (contract tests & AI context)

The repository includes **machine-readable examples** under **`examples/`**:

- **`examples/minimal/`** — smallest valid request/response pair.
- **`examples/feishu-cli/`** — illustrative Shell facing IM-style CLI: `shell_kind`, `task_hint`, `continuation`, attachment **refs** (no base64 in body).

**Use them to:**

- **Contract-test** your serializer/parser (CI: validate JSON against the Schema).
- **Ground LLMs**: paste file paths + key excerpts into the project context so the model does not invent fields.

**Rule:** Generated code MUST produce JSON that **validates** as either `requestMessage` or `responseMessage` per the Schema `oneOf` (validate each file separately).

---

## 3. Implementation checklist (Shell → Engine)

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

## 4. Implementation checklist (Engine / third-party Harness)

- [ ] Echo **`request_id`** and **`correlation_id`** when present.
- [ ] Return **`supported_protocol_versions`** when multiple versions are supported; else reject with **`error.code`** (e.g. `protocol_version_unsupported`).
- [ ] Populate **`supported_capabilities`** / **`capability_denials`** when the Shell asks for features you cannot honor.
- [ ] Emit **`response.error`** with **`code`**, safe **`message`**, optional **`retryable`**, **`details`** on failure (PROTOCOL §13).
- [ ] Do **not** return secrets in **`error`** payloads.

---

## 5. Anti-patterns (teach your AI to avoid these)

| Anti-pattern | Why it breaks interop |
|--------------|------------------------|
| Embedding **screenshot/base64** or huge blobs in **`context`** | Violates PROTOCOL §9.1; use **`attachments`** refs or uploads. |
| Ignoring **`capability_denials`** and still rendering “rich” UI | Silent mismatch; user sees broken experience. |
| Executing **unknown `action_type`** with real side effects | Violates PROTOCOL §11; security and consistency. |
| Reusing unstable strings as **`session_id`** | Breaks resume and analytics; document your mapping (future Feishu profile). |
| Assuming **HTTP headers** are normative for all transports | PROTOCOL is transport-agnostic; headers belong in an optional **transport profile**. |

---

## 6. Suggested “context block” for AI coding tools

You can paste the following into a Cursor rule, Copilot chat, or custom instruction when asking the model to implement a Shell or Engine adapter:

```text
You are implementing an OpenHarness client or server.
Source of truth: docs/PROTOCOL.md (normative) and schema/openharness-v1.draft.json.
Validate outgoing/incoming JSON against the Schema (request message vs response message separately).
Follow PROTOCOL §11 for unknown action_type: never execute side effects for unknown types.
Do not put base64 blobs or long-lived API secrets in the JSON body; use attachment refs and credential_ref / transport auth.
Use examples/minimal/ and examples/feishu-cli/ as golden references.
```

Adjust paths if your monorepo nests OpenHarness as a submodule.

---

## 7. Feishu / Lark CLI (fastClaw, etc.)

**Protocol does not** standardize Feishu Open Platform APIs. For **fast** integration:

1. Implement the **OpenHarness wire** first (this repo).
2. In **your** product repo, maintain an adapter: Feishu events ↔ OpenHarness **`request.context`** (tenant/chat/thread mapping — future **`docs/profiles/feishu-lark.md`**).
3. Set **`shell_kind`** (e.g. `feishu_cli`) so Engines can tune behavior.

DeskHarness or other Engines remain **separate**; OpenHarness only ensures the **JSON contract** is consistent.

---

## 8. Roadmap (may move into separate files)

- **HTTP transport profile** (informative): recommended headers mapping to `correlation_id` / tracing.
- **Integration tests** in CI validating `examples/**/*.json` against the Schema (contributions welcome).
- **OpenAPI** for a chosen HTTP mapping (optional; not required by core protocol).

---

## 中文

**性质：** 资料性；**权威规范** 仍为 **[PROTOCOL.md](../PROTOCOL.md)**。边界见 **[SCOPE.md](../SCOPE.md)**，分层见 **[OVERVIEW.md](../OVERVIEW.md)**。

### 面向谁

第三方 **Harness**（如 fastClaw）、**Shell/CLI**（如飞书 CLI）实现者，以及用 **AI 写对接代码** 的开发者。

### 核心建议

1. **阅读顺序**：先 PROTOCOL → 再 Schema → 再 **`examples/`** 金样；避免「字段看起来像」但不合规。  
2. **金样 JSON**：用于契约测试与 **给 AI 当上下文**，减少瞎编字段。  
3. **清单**：上文 Shell / Engine 检查表可直接当作 **人类或 LLM 的任务列表**。  
4. **反模式表**：训练 AI 或 Code Review 时重点核对（base64、未知指令副作用、能力静默失败等）。  
5. **可复制提示块**：第六节英文块可贴进 Cursor / Copilot 的项目说明。  
6. **飞书**：开放平台 API **不在** OpenHarness 规范内；飞书 ↔ `context` 映射由 **各产品适配器 + 未来 Profile** 文档承担；协议层保证 **JSON 契约**一致。

### 我们（OpenHarness 维护者）还能补什么

- 在 `examples/` 增加更多场景金样；CI 里跑 **Schema 校验**（欢迎 PR）。  
- 增补 **`docs/profiles/feishu-lark.md`**（资料性）：会话键与 `session_id` / `conversation_id` 推荐映射。  
- 可选：**HTTP Profile**、OpenAPI 片段 —— 仍保持与 **传输无关** 的核心一致。
