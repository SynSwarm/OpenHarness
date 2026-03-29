# Implementer orientation (for humans, OpenClaw, and other AI agents)

**Status:** Informative. **Does not** change **[PROTOCOL.md](../PROTOCOL.md)**. Use this file when **onboarding** onto OpenHarness so questions about **scope** and **where code lives** are answered before implementation starts.

**Language:** English first · [中文](#中文)

---

## 1. What the protocol defines vs what you decide

| Layer | Defined by OpenHarness | Defined by your product |
|-------|------------------------|-------------------------|
| **Wire JSON** | `request` / `response`, `context`, `action_directives`, errors, §11 unknown types | — |
| **Who is Shell vs Engine** | Roles (Shell sends intent; Engine returns directives) | Which binary is which in *your* deployment |
| **TV / phone OS** | Not specified | Android TV, Apple TV, web, etc. — any client that can speak HTTP(S) + JSON can be a Shell |
| **IM platform** | Not specified | Feishu, DingTalk, Slack, … — each needs a **platform adapter** mapping IDs → `context` |
| **Pairing, OAuth, URLs** | Guidance (e.g. PROTOCOL §7, [device-pairing-session.md](./device-pairing-session.md)) | Your gateway and security model |
| **Programming language** | Not specified | Server adapter in this repo is **Python**; TV Shell is often **Kotlin/Java** (Android TV) or other |

**Takeaway:** The protocol is **one JSON contract**. Hardware brand, OS, and language are **integration choices**, not spec gaps.

---

## 2. “Simple Shell client” vs “full Harness Engine”

- **Simple Shell client** (typical v1): a client that (1) builds or forwards a conformant **`request`**, (2) **POSTs** it to **your** HTTP endpoint, (3) parses **`response`**, displays **`render_message`** (or equivalent text directive), and (4) applies **PROTOCOL §11** for unknown `action_type`. **Difficulty: moderate** if you already have HTTP on the device.

- **Full Harness Engine** (SOP state machines, multi-tool orchestration, enterprise HA): **large product**. You do **not** need this on day one for **basic Q&A**.

- **Middle path (OpenClaw + this repo):** Run **`bridge-server`** from **[adapters/openharness-adapter-openclaw](../../adapters/openharness-adapter-openclaw/)** next to OpenClaw. The TV (or CLI) posts **OpenHarness JSON** to `bridge-server`; the bridge calls **OpenClaw’s HTTP API** and wraps the reply in **`render_message`**. In that topology, **OpenClaw + bridge = your “engine-shaped” endpoint** for dialogue — no separate monolithic Engine required until you outgrow it.

---

## 3. Where things live in this repository

| Need | Location |
|------|----------|
| Normative wire semantics | **[PROTOCOL.md](../PROTOCOL.md)**, **Schema**, **examples/** |
| Server-side Python beside OpenClaw (CLI, bridge, pairing **examples**) | **[adapters/openharness-adapter-openclaw/README.md](../../adapters/openharness-adapter-openclaw/README.md)** |
| TV Shell **guidance** (no APK in-tree) | **[adapters/openharness-adapter-android-tv/README.md](../../adapters/openharness-adapter-android-tv/README.md)** |
| IM/bot mapping responsibilities | **[profiles/im-bot-shell.md](../profiles/im-bot-shell.md)** |
| Pairing patterns (long-lived device, `session_id`) | **[device-pairing-session.md](./device-pairing-session.md)** |

**Important:** **`adapters/openharness-adapter-openclaw/`** does **not** contain the TV app. It contains **tools and examples** for the **server** next to OpenClaw. The **TV Shell** is a **separate** codebase (e.g. Android Studio project).

---

## 4. Pre-answers to common “discovery” questions

These are **product** answers; defaults assume a **minimal dialogue v1** on **LAN** (no TLS required for first lab iteration per your policy).

| Question | Default framing |
|----------|-----------------|
| What TV type? | Your choice; **Android TV** is a common target. The protocol only needs **HTTP + JSON** from the Shell. |
| Remote control / playback state? | Optional **later** via new `action_type` / `environment_state`; v1 can be **text Q&A only**. |
| Language on server? | This adapter is **Python**; OpenClaw may use any stack for its HTTP API. |
| Language on TV? | Typically **Kotlin/Java** for Android TV; not constrained by OpenHarness. |
| Same LAN as OpenClaw? | Typical for v1 lab; **pairing** flow is optional — see **pair-server** example and pairing guide. |
| Need pairing codes? | Only if **you** want device binding; see **[device-pairing-session.md](./device-pairing-session.md)**. |

---

## 5. Minimal checklist (Shell implementer)

1. Read **[PROTOCOL.md](../PROTOCOL.md)** §9 (`context`), §10–§11 (`action_directives`).
2. Send **`protocol_version`**, **`request_id`**, **`request.auth`**, **`request.context`** (`session_id`, `user_intent` at minimum for Q&A).
3. **POST** to the URL your ops team assigns (e.g. `bridge-server` behind reverse proxy).
4. On success, read **`response.action_directives`**, handle **`render_message`** for text.
5. On unknown **`action_type`**, **no side effects** (§11).

---

## 中文

**性质：** 资料性；**不修改** **[PROTOCOL.md](../PROTOCOL.md)**。给 **人类、OpenClaw 或其它 AI 助手** 做 **范围与目录** 的快速对齐，减少「协议没写清」的误解。

### 协议规定 vs 你们自定

| 层面 | OpenHarness 规定 | 由产品决定 |
|------|------------------|------------|
| **线格式 JSON** | `request`/`response`、`context`、指令、错误、§11 | — |
| **Shell / Engine 角色** | 职责划分 | 你们部署里哪个进程当 Shell、哪个当「引擎形」端点 |
| **电视/手机系统** | 不规定 | Android TV、Apple TV、Web 等，只要能 **HTTP(S)+JSON** 即可当 Shell |
| **飞书/钉钉等 IM** | 不规定 | 各平台做 **适配器**，把会话 ID 等映射进 `context` |
| **配对、鉴权、URL** | 原则性指引 | 网关与安全策略 |
| **语言** | 不规定 | 本仓适配器为 **Python**；电视端多为 **Kotlin/Java** |

### 「简单 Shell」与「完整 Engine」

- **简单 Shell：** 组 **`request`** → **POST** → 解析 **`render_message`** → §11 处理未知指令。  
- **完整 Harness Engine（SOP/多工具/高可用）：** 大工程；**v1 对话不必先做**。  
- **中间路线：** 电视 POST 到 **`bridge-server`**，桥接 **OpenClaw HTTP**，返回 **`render_message`** — 对 **纯对话 v1** 往往足够。

### 本仓库里有什么、没有什么

- **`adapters/openharness-adapter-openclaw/`**：**服务端** Python（CLI、桥、配对**示例**），**不是** 电视 APK。  
- **电视客户端**：**另起工程**（如 Android TV）；指引见 **[openharness-adapter-android-tv](../../adapters/openharness-adapter-android-tv/README.md)**。

### 实现清单（Shell）

同上文第 5 节，对照 **PROTOCOL** §9–§11 与 **[AI_INTEGRATION.md](./AI_INTEGRATION.md)** 清单即可。
