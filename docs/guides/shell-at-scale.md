# Shell integrations at scale — where guides live (Informative)

**Status:** Informative meta-guide. **Does not** change **[PROTOCOL.md](../PROTOCOL.md)**. For scope boundaries, see **[SCOPE.md](../SCOPE.md)**.

**Language:** English first · [中文](#中文)

---

## Why this document

Some **Shell** teams ship a **broad surface area**: CLIs, bots, multi-tenant chat, rich cards, attachment pipelines. They need **readable, end-to-end** material beyond the normative wire spec. This page explains **where** such material belongs in **this** repository and how it stays **vendor-neutral** at the protocol core.

---

## Principles

1. **PROTOCOL + Schema** remain the **only** normative contract — **no** vendor-specific APIs or field matrices in `PROTOCOL.md`.
2. **Vendor-neutral** patterns (IM bot Shell, HTTP hints) live in `**docs/profiles/`** — see **[im-bot-shell.md](../profiles/im-bot-shell.md)**, **[http-transport.md](../profiles/http-transport.md)**.
3. **Integration narrative**, checklists, and pointers for AI-assisted implementers live in `**docs/guides/`** — see **[AI_INTEGRATION.md](./AI_INTEGRATION.md)**.
4. **Platform-specific** ID mappings (tenant / chat / thread → `session_id` / `conversation_id`), Open Platform endpoint names, and CLI flags are **product documentation**. Prefer publishing them in the **Shell product** or **adapter** repository. If a **redacted, non-normative** appendix is contributed here, it must be clearly labeled **informative**, **optional**, and **not** part of conformance testing against the core protocol.

---

## When extra guidance is warranted

Consider adding or extending **informative** docs (here or in your product repo) when:

- The Shell exposes a **CLI** or **bot** used across many tenants or teams.
- **Session stability**, **attachment upload**, and **capability negotiation** are easy to get wrong at scale.
- You want **one place** for “how we fill `request.context`” without duplicating PROTOCOL text.

This is **documentation ergonomics**, not a new protocol tier.

---

## Suggested placement


| Content type                                                                                         | Suggested location in this repo                                                                                                                  | Notes                                                                                     |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Responsibility split (who maps IDs, who owns transport, attachments, Engine truth table)             | `**docs/profiles/im-bot-shell.md`**                                                                                                              | Already vendor-neutral.                                                                   |
| HTTP header hints                                                                                    | `**docs/profiles/http-transport.md**`                                                                                                            | Optional; core remains transport-agnostic.                                                |
| AI / third-party checklists, golden JSON pointers                                                    | `**docs/guides/AI_INTEGRATION.md**`                                                                                                              | Already linked from README.                                                               |
| **Platform-specific** mapping tables (e.g. a particular chat vendor’s `chat_id` → `conversation_id`) | **Prefer** Shell/adapter product repo; **or** an optional `**docs/profiles/`** appendix PR, clearly marked **informative** and **non-normative** | Avoid turning the OpenHarness repo into a full mirror of a vendor’s Open Platform manual. |


---

## Relationship to readability at scale

- **Yes**, it is **useful** to give teams operating **Shells at scale** (CLI, bots, multi-tenant surfaces) a **clear reading path**: PROTOCOL → profiles → guides → examples → (optional) your product’s mapping doc.
- **No**, the core repo does **not** need to host every vendor’s field-level appendix — **im-bot-shell** + **AI_INTEGRATION** already establish the split; vendor detail can stay **outside** or in **optional** contributed appendices.

---

## 中文

**性质：** 资料性**元指引**；**不修改** **[PROTOCOL.md](../PROTOCOL.md)**。边界见 **[SCOPE.md](../SCOPE.md)**。

### 为何需要这篇

部分 **Shell** 团队交付 **CLI / 机器人 / 多租户 IM** 等**较大表面**，除规范性线格式外，还需要**可读、端到端**的说明。本文说明：这类材料在**本仓库**里**放在哪**、如何与 **PROTOCOL** 划界、**核心协议如何保持厂商中立**。

### 原则

1. **PROTOCOL + Schema** 仍是**唯一**规范性契约；**不在** `PROTOCOL.md` 写各厂商 API 或字段对照表。
2. **与厂商无关** 的模式放在 `**docs/profiles/`**（如 **[im-bot-shell.md](../profiles/im-bot-shell.md)**、**[http-transport.md](../profiles/http-transport.md)**）。
3. **集成叙事、清单、AI 辅助** 放在 `**docs/guides/`**（如 **[AI_INTEGRATION.md](./AI_INTEGRATION.md)**）。
4. **平台特有** 的 ID 映射（租户/会话/话题 → `session_id` / `conversation_id`）、开放平台端点、CLI 参数等，**优先**放在 **Shell/适配器产品文档**；若向本仓库贡献**脱敏、非规范性**附录，须标明 **资料性、可选**，且**不参与**对核心协议的符合性测试。

### 何时值得写「额外指引」

CLI/机器人**规模大**、会话与附件易错、希望有「如何填 `context`」的**单一说明**时，适合在**本仓库或产品仓库**增加资料性文档——这是**文档可读性**，不是新协议层级。

### 建议落点（表意与英文一致）


| 内容                        | 本仓库建议位置                                                | 说明                  |
| ------------------------- | ------------------------------------------------------ | ------------------- |
| 职责划分（映射、传输、附件、Engine 真值表） | `**profiles/im-bot-shell.md`**                         | 已存在，厂商中立。           |
| HTTP 头与追踪                 | `**profiles/http-transport.md**`                       | 可选。                 |
| AI/第三方清单与金样               | `**guides/AI_INTEGRATION.md**`                         | 已有。                 |
| **某厂商** 字段级映射表            | **优先** 产品仓；或 **可选** 的 `**profiles/`** 附录 PR，标明 **非规范** | 避免本仓变成某开放平台手册的全量镜像。 |


### 与「规模化 Shell 集成」的可读性

- **有必要** 为**高覆盖面 / 规模化** Shell 团队（CLI、机器人、多租户等）提供**清晰阅读路径**：PROTOCOL → profiles → guides → examples →（可选）产品侧映射文档。  
- **不必** 在核心仓库收齐**所有厂商**的附录；**im-bot-shell + AI_INTEGRATION** 已划清分工；厂商细节可**外置**或以**可选附录**贡献。

