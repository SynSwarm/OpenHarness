# OpenHarness 协议规范

**版本：** v1.0.0-draft  
**说明：** 中文译文供阅读便利；与英文不一致时，以 **[PROTOCOL.md](./PROTOCOL.md)** 为准。

**仓库范围**（规范性正文与各 Engine 产品分工）见 **[SCOPE.md](./SCOPE.md)**（资料性）。**分层叙事**（核心 / Profile / 传输与执行反馈）见 **[OVERVIEW.md](./OVERVIEW.md)**（资料性）。

集成方可以发布 **Wishlist** 或 **实现映射**；此类文档**不替代**本规范。

---

## 1. 目标与非目标

**目标**

- 任意技术栈可实现的 **与传输无关的 JSON** 载荷。
- **向前兼容**：未知字段 **必须** 忽略（见 §4）；**未知 `action_type` 取值** 的处理见 §11。
- **清晰的版本** 与 **能力协商**（尽可能双向）。
- 对 LLM 厂商、运行时与工具实现细节 **保持中立**。

**非目标**

- 规定 UI 框架、组件库或具体模型 API。
- v1 中规定 **流式分块** 的完整格式（见 §15）。
- 为每种 Shell 变体列出 **环境字段白名单**（见 §8；细则见实现指南）。
- 商标策略（如需另文说明）。

---

## 2. 术语

| 术语 | 含义 |
|------|------|
| **Shell** | 采集用户意图与环境状态的一端；负责渲染或执行 **行动指令**。 |
| **Harness Engine** | 服务端逻辑：路由、SOP/状态机、工具、安全与指令生成。 |
| **行动指令（action directive）** | 一条结构化的工作或输出单元（UI 渲染、自动化步骤等）。 |

---

## 3. 版本

- **`protocol_version`**（字符串，必填）：本消息所符合的 **线格式** 语义化版本（如 `1.0.0`）。
- **兼容规则**  
  - **主版本**：不兼容变更。  
  - **次版本**：向后兼容扩展。  
  - **修订版**：以澄清与文档为主，除非明确标注影响线上格式。

若 Engine 支持多条主版本线，**应当** 在响应中包含 **`supported_protocol_versions`**。

Shell **应当** 使用其实现的最高 **`protocol_version`**。若 Engine 无法满足，**必须** 返回 **`status`: `error`** 及合适的 **`error.code`**（例如 `protocol_version_unsupported`）。

---

## 4. 扩展性

- 任意层级出现的 **未知字段**，接收方 **必须** 忽略。（**未知 `action_type` 取值** 的处理见 §11，与「忽略未知 JSON 键」不同。）
- **厂商扩展** 建议使用单一对象键 `extensions`；键名建议反向域名或 URI 前缀。

---

## 5. 消息外壳

### 5.1 请求（Shell → Engine）

| 字段 | 必填 | 说明 |
|------|------|------|
| `protocol_version` | 是 | 线格式版本（semver 字符串）。 |
| `request_id` | 建议 | **幂等** 与请求/响应配对；响应中回显。 |
| `correlation_id` | 否 | **分布式追踪**、与日志对齐；可与 `request_id` 不同；响应回显。 |
| `capabilities` | 否 | Shell 声明的能力（见 §5.3）。 |
| `request` | 是 | 载荷：`auth`、`context`、可选 `extensions`。 |

### 5.2 响应（Engine → Shell）

| 字段 | 必填 | 说明 |
|------|------|------|
| `protocol_version` | 是 | 响应对应的线格式版本。 |
| `request_id` | 建议 | 与请求对应。 |
| `correlation_id` | 否 | 与请求对应。 |
| `supported_protocol_versions` | 否 | Engine 接受的版本（见 §3）。 |
| `supported_capabilities` | 否 | Engine **提供**的能力（对象，键风格与 `capabilities` 一致）。 |
| `capability_denials` | 否 | 对 Shell 所求能力的 **明确拒绝**（见 §5.3）。 |
| `response` | 是 | `status`、可选 `error`、指标与指令等。 |

### 5.3 能力（capabilities）

Shell → Engine 的 **`capabilities`** 与 Engine → Shell 的 **`supported_capabilities`** 均为对象：键为稳定功能标识符，值由实现定义。

**示例键**（说明用，可扩展）：

| 键 | 典型含义 |
|----|----------|
| `openharness.streaming` | 参与流式（具体 profile 见 §15）。 |
| `openharness.actions.parallel` | 可并行执行兼容指令。 |
| `openharness.attachments.upload` | Shell 可提供附件引用。 |
| `openharness.ui.rich_cards` | 可渲染富卡片。 |
| `openharness.ui.approval` | 可展示审批 UI。 |

接收方 **必须** 忽略无法识别的能力键。

**`capability_denials`**（可选）：对象数组，每项含 `capability`（必填）、`code`（建议）、`message`（可选），避免 **半套能力静默失败**。

---

## 6. Shell 身份（`request.context.shell`）

可选对象，描述 Shell 实现，便于 Engine 选择回复 **形态**（卡片 / 纯文本 / 大屏大字短句等）。

| 字段 | 必填 | 说明 |
|------|------|------|
| `shell_kind` | 建议 | Shell 族稳定标识；可用约定字符串（如 `im_bot`、`command_shell`、`tv`、`vehicle_hmi`）或命名空间字符串。 |
| `shell_version` | 否 | Shell 软件版本。 |
| `locale` | 否 | BCP 47 语言标签（如 `zh-CN`）。 |
| `timezone` | 否 | IANA 时区（如 `Asia/Shanghai`）。 |

---

## 7. 认证与密钥（规范性指引）

- 生产环境不要将长期 API 密钥作为 JSON **必填** 正文；优先传输层认证。
- **`auth`** 可仅含 **稳定引用**（`tenant_id`、`credential_ref` 等），而非明文长期密钥。
- **`error`** 中不得回显令牌。
- Engine **不得** 在可用引用或传输层认证时仍要求协议正文中的 **明文长期密钥**。

---

## 8. 隐私与环境状态

- 使用 **`privacy_tier`** 标注 **`environment_state`**（`public` / `restricted` / `secret`），含义与英文表一致。
- 优先 **派生/哈希** 表示，而非原始屏幕内容（除非策略允许）。
- **各 Shell 允许上送哪些 `environment_state` 字段** 属于 **部署/产品策略**，在实现指南中维护；协议只定义 **语义**，不穷举 OEM 矩阵。

---

## 9. 上下文（`request.context`）

| 字段 | 必填 | 说明 |
|------|------|------|
| `session_id` | 建议 | 用户 ↔ Engine **长期会话线**。 |
| `conversation_id` | 否 | 同一会话内子线程 / 多 tab。 |
| `user_intent` | 建议 | 自然语言或结构化意图。 |
| `task_hint` | 否 | 路由提示（如 `sop_id`、`plugin_id`、业务键）；Engine 映射到内部任务/SOP。 |
| `continuation` | 否 | **续跑**（见 §9.2）。 |
| `environment_state` | 否 | 设备/OS/UI；可含 `privacy_tier`。 |
| `attachments` | 否 | 附件 **引用**（见 §9.1）。 |
| `shell` | 否 | Shell 身份（见 §6）。 |
| `extensions` | 否 | 额外上下文。 |

### 9.1 附件

`attachments` **必须** 为 **引用** 对象数组；**禁止** 在协议正文中嵌套大块 base64 二进制。

每项至少包含其一：不透明 **`ref_id`**、**`uri`**、**`asset_id`** 等；可选 `mime_type`、`filename`、`size_bytes`。

### 9.2 续跑（SOP / run）

`continuation` 可选，用于 **同一 SOP run** 的续跑（如 IM 客户端中「继续」）：

| 字段 | 必填 | 说明 |
|------|------|------|
| `run_id` | 否 | Engine 颁发的 run 标识。 |
| `sop_id` | 否 | SOP/工作流标识。 |
| `continuation_token` | 否 | Engine 颁发的下一步不透明令牌。 |

具体语义由 Engine 定义；协议只传 **不透明标识**。

---

## 10. 行动指令（`response.action_directives`）

| 字段 | 必填 | 说明 |
|------|------|------|
| `action_type` | 是 | 已注册或命名空间类型（见 §12）。 |
| `priority` | 否 | 如 `low` / `normal` / `high` / `critical`。 |
| `execution` | 否 | `sequential`（默认）或 `parallel`。 |
| `risk_tier` | 否 | `safe` / `caution` / `dangerous`。 |
| `requires_user_approval` | 否 | 为 `true` 时 Shell **必须** 先取得用户明确同意。 |
| `deadline_ms` | 否 | 自收到起的相对截止（毫秒，Shell 尽力而为）。 |
| `payload` | 否 | 类型相关数据。 |
| `extensions` | 否 | 单条指令扩展。 |

**顺序**：除非 `execution` 另有说明，Shell **应当** 按数组顺序处理。

---

## 11. 未知 `action_type`（规范性）

Shell 维护其实现的 **`action_type`** 集合。若某条指令的 `action_type` **未知**：

1. Shell **不得** 对该条执行 **有副作用** 的行为（系统自动化、支付、破坏性文件操作、除遥测外的网络调用等）。
2. Shell **应当** **跳过** 该条并继续处理后续项，或在 `payload` 含 **`message`** / **`fallback_message`**（Engine 约定）时 **降级** 为对用户可见的纯文本提示。
3. Shell **可以** 产生本地诊断/遥测，码如 `unknown_action_type`（实现定义）。

默认 **互操作** 配置下，不得默认执行未知类型的副作用。

---

## 12. 行动类型注册表

- **核心** 类型示例：`render_ui`、`simulate_action`、`render_message`、`request_approval`、`noop`。
- **命名空间** 类型建议反向域名或点分前缀，如 `com.example.sop.start`、`com.example.plugin.invoke`。
- 可在注册条目中说明 **semver**；除非另行标准化，否则不必把 semver 写进线格式字符串本身。

---

## 13. 错误模型

失败时 **`response.status`** **必须** 为 `error`，**`response.error`** **应当** 存在：

| 字段 | 必填 | 说明 |
|------|------|------|
| `code` | 是 | 稳定机器可读码。 |
| `message` | 否 | 安全的人类可读信息。 |
| `retryable` | 否 | 为 `true` 时客户端 **可以** 退避重试；为 `false` 时多半需改请求再试。 |
| `details` | 否 | 可记录的结构化信息。 |

---

## 14. 成功响应

当 **`response.status`** 为 `success` 时，**`action_directives`** 可为空。可选 **`engine_latency_ms`**。

---

## 15. 流式（资料性）

v1 规范性正文为 **非流式** 请求/响应。SSE/WebSocket 分块、`stream_id` 等可通过 **`capabilities`**（如 `openharness.streaming`）约定 **单独流式 profile**，不宜仅从 v1 正文推断流式语义。

---

## 16. Schema

[`../schema/openharness-v1.draft.json`](../schema/openharness-v1.draft.json)

---

## 17. 示例（说明性）

与英文版 [PROTOCOL.md §17](./PROTOCOL.md#17-example-illustrative) 一致：

**请求：**

```json
{
  "protocol_version": "1.0.0",
  "request_id": "req_01jqxyz",
  "correlation_id": "corr_8f3a",
  "capabilities": {
    "openharness.actions.parallel": true,
    "openharness.ui.rich_cards": true
  },
  "request": {
    "auth": {
      "tenant_id": "usr_9527",
      "credential_ref": "cred_opaque_abc"
    },
    "context": {
      "session_id": "sess_8848",
      "conversation_id": "conv_tab_2",
      "user_intent": "Continue the onboarding SOP.",
      "task_hint": {
        "sop_id": "sop_onboard",
        "business_key": "deal_42"
      },
      "continuation": {
        "run_id": "run_7d2",
        "continuation_token": "ctok_aq9"
      },
      "shell": {
        "shell_kind": "im_bot",
        "shell_version": "2.1.0",
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai"
      },
      "attachments": [
        {
          "ref_id": "att_01",
          "mime_type": "image/png"
        }
      ],
      "environment_state": {
        "privacy_tier": "restricted",
        "os": "macOS",
        "active_window": "Excel",
        "screen_hash": "a1b2c3d4"
      }
    }
  }
}
```

**响应：**

```json
{
  "protocol_version": "1.0.0",
  "request_id": "req_01jqxyz",
  "correlation_id": "corr_8f3a",
  "supported_protocol_versions": ["1.0.0"],
  "supported_capabilities": {
    "openharness.actions.parallel": true,
    "openharness.ui.rich_cards": true
  },
  "capability_denials": [],
  "response": {
    "status": "success",
    "engine_latency_ms": 120,
    "action_directives": [
      {
        "action_type": "render_ui",
        "priority": "high",
        "risk_tier": "safe",
        "deadline_ms": 5000,
        "payload": { "component": "DataChart", "data": [] }
      },
      {
        "action_type": "simulate_action",
        "priority": "critical",
        "risk_tier": "dangerous",
        "requires_user_approval": true,
        "payload": { "macro": "cmd+c", "target": "cell_B2" }
      }
    ]
  }
}
```

---

## 18. 许可

除非文件头另有说明，本仓库中的规范文本与 Schema 与项目根目录 `LICENSE` 相同。
