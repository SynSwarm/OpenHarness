# OpenHarness 协议规范

**版本：** v1.0.0-draft  
**说明：** 中文译文供阅读便利；与英文不一致时，以 **[PROTOCOL.md](./PROTOCOL.md)** 为准。

本文定义 **Shell**（界面、设备或客户端）与 **Harness Engine**（编排、模型、工具）之间的 **规范性** JSON 消息契约。传输层（HTTP、WebSocket、gRPC 等）在 v1 中不作硬性规定（文中推荐除外）。

---

## 1. 目标与非目标

**目标**

- 任意技术栈可实现的 **与传输无关的 JSON** 载荷。
- **向前兼容**：未知字段 **必须** 忽略（见 §4）。
- **清晰的版本** 与可选的 **能力协商**。
- 对 LLM 厂商、运行时与工具实现细节 **保持中立**。

**非目标**

- 规定 UI 框架、组件库或具体模型 API。
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
  - **主版本**：不兼容变更（删除必填字段、改类型、改语义）。  
  - **次版本**：向后兼容扩展（新增可选字段、注册表新增 `action_type`）。  
  - **修订版**：以澄清与文档为主，除非明确标注影响线上格式。

若 Engine 支持多条主版本线，**应当** 在响应中包含 **`supported_protocol_versions`**（字符串数组）。

Shell **应当** 使用其实现的最高 **`protocol_version`**。若 Engine 无法满足，**必须** 返回 **`status`: `error`** 及合适的 **`error.code`**（例如 `protocol_version_unsupported`）。

---

## 4. 扩展性

- 任意层级出现的 **未知字段**，接收方 **必须** 忽略。
- **厂商扩展** 建议使用单一对象键：

  ```json
  "extensions": {
    "com.example": { "foo": 1 }
  }
  ```

  `extensions` 内键名建议使用反向域名或 URI 前缀，避免冲突。

---

## 5. 消息外壳

### 5.1 请求（Shell → Engine）

| 字段 | 必填 | 说明 |
|------|------|------|
| `protocol_version` | 是 | 线格式版本（semver 字符串）。 |
| `request_id` | 建议 | 追踪用不透明 ID；响应中回显。 |
| `capabilities` | 否 | Shell 支持的能力（见 §5.3）。 |
| `request` | 是 | 载荷：`auth`、`context`、可选 `extensions`。 |

### 5.2 响应（Engine → Shell）

| 字段 | 必填 | 说明 |
|------|------|------|
| `protocol_version` | 是 | 响应对应的线格式版本。 |
| `request_id` | 建议 | 与请求中的 `request_id` 对应。 |
| `supported_protocol_versions` | 否 | 该 Engine 接受的版本（见 §3）。 |
| `response` | 是 | `status`、可选 `error`、指标与指令等。 |

### 5.3 能力（capabilities）

`capabilities` 为对象，键为 **稳定的功能标识符**，值由实现定义（布尔、字符串或对象）。示例：

```json
"capabilities": {
  "openharness.actions.parallel": true,
  "openharness.stream.events": { "max_events_per_second": 20 }
}
```

接收方 **必须** 忽略无法识别的能力键。

---

## 6. 认证与密钥（规范性指引）

- **不要** 在生产集成中将长期 API 密钥作为 JSON 正文的必填部分。优先使用传输层认证（如 TLS + `Authorization` 头、mTLS 或签名请求）。
- 若传输已建立身份，**`auth`** 可仅含 **稳定引用**（如 `tenant_id`、`credential_ref`、`session_id`），而非原始令牌。
- 若某部署必须在 JSON 中放令牌，应视为 **不透明、短寿命**，且 **不得** 在 **`error`** 载荷中回显或记录。

---

## 7. 隐私与环境状态

- 发送可能敏感的数据时，Shell **应当** 用 **`privacy_tier`** 标注 **`environment_state`**：

  | 取值 | 含义 |
  |------|------|
  | `public` | 按产品策略可记录与共享。 |
  | `restricted` | 可能含 PII 或敏感元数据；最小化留存。 |
  | `secret` | 未经明确策略不得记录或发往第三方。 |

- Shell **应当** 优先使用 **派生/哈希** 表示（如屏幕指纹），而非原始屏幕内容，除非用户与策略允许。

---

## 8. 上下文（`request.context`）

| 字段 | 必填 | 说明 |
|------|------|------|
| `session_id` | 建议 | 多轮会话关联。 |
| `user_intent` | 建议 | 自然语言或结构化意图。 |
| `environment_state` | 否 | 设备/OS/UI 状态；可含 `privacy_tier`。 |
| `extensions` | 否 | 额外上下文（见 §4）。 |

---

## 9. 行动指令（`response.action_directives`）

每条指令：

| 字段 | 必填 | 说明 |
|------|------|------|
| `action_type` | 是 | 已注册或带命名空间的类型（见 §10）。 |
| `priority` | 否 | 提示：如 `low`、`normal`、`high`、`critical`。 |
| `execution` | 否 | `sequential`（默认）或 `parallel`（在适用时与同级并行）。 |
| `risk_tier` | 否 | `safe`、`caution`、`dangerous` — Shell 可对较高风险要求用户确认。 |
| `requires_user_approval` | 否 | 为 `true` 时 Shell **必须** 在执行前取得用户明确同意。 |
| `payload` | 否 | 类型相关数据。 |
| `extensions` | 否 | 单条指令扩展。 |

**顺序**：除非 `execution` 另有说明，Shell **应当** 按 **数组顺序** 处理指令。

---

## 10. 行动类型注册表

- **核心** 类型（示例，非穷尽）：`render_ui`、`simulate_action`、`noop`。
- **带命名空间** 的类型建议使用反向域名或 URI，例如 `com.deskharness.render.dashboard`。
- 实现可发布可选的公开注册表；v1 不强制中心化权威机构。

---

## 11. 错误模型

失败时 **`response.status`** **必须** 为 `error`，且 **`response.error`** **应当** 存在：

| 字段 | 必填 | 说明 |
|------|------|------|
| `code` | 是 | 稳定机器可读码（如 `invalid_request`、`engine_timeout`）。 |
| `message` | 否 | 安全的人类可读信息；**不得** 回显密钥或原始 PII。 |
| `details` | 否 | 可记录的结构化诊断信息。 |

---

## 12. 成功响应

当 **`response.status`** 为 `success` 时，**`response.action_directives`** 可为空。可选字段：

| 字段 | 说明 |
|------|------|
| `engine_latency_ms` | Engine 侧处理耗时（提示）。 |

---

## 13. Schema

规范性 JSON Schema（草案）：[`../schema/openharness-v1.draft.json`](../schema/openharness-v1.draft.json)。

---

## 14. 示例（精简）

与英文版 [PROTOCOL.md §14](./PROTOCOL.md#14-example-minimal) 相同。

**请求：**

```json
{
  "protocol_version": "1.0.0",
  "request_id": "req_01jqxyz",
  "capabilities": {
    "openharness.actions.parallel": true
  },
  "request": {
    "auth": {
      "tenant_id": "usr_9527",
      "credential_ref": "cred_opaque_abc"
    },
    "context": {
      "session_id": "sess_8848",
      "user_intent": "Analyze the current screen and extract key metrics.",
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
  "supported_protocol_versions": ["1.0.0"],
  "response": {
    "status": "success",
    "engine_latency_ms": 120,
    "action_directives": [
      {
        "action_type": "render_ui",
        "priority": "high",
        "risk_tier": "safe",
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

## 15. 许可

除非文件头另有说明，本仓库中的规范文本与 Schema 与项目根目录 `LICENSE` 相同。
