# openharness-adapter-openclaw

**Status:** Informative Shell-side helper. **Normative** wire format: **[PROTOCOL.md](../../docs/PROTOCOL.md)** + **[schema](../../schema/openharness-v1.draft.json)** + **[examples](../../examples/)**.

**Language:** English first · [中文](#中文)

---

## Start here (OpenClaw, AI coding agents, humans)

Read **[implementer-orientation.md](../../docs/guides/implementer-orientation.md)** before asking “what’s missing?” — it pre-answers scope questions.

| Question | Answer in one line |
|----------|-------------------|
| Is this folder the **TV Shell app**? | **No.** This is **server-side** Python beside OpenClaw (`bridge-server`, pairing **examples**, CLI). The **TV client** is a **separate** codebase → **[openharness-adapter-android-tv](../openharness-adapter-android-tv/README.md)**. |
| Must I build a **full Harness Engine** (SOP, huge orchestration)? | **No** for v1 dialogue. **`bridge-server` + OpenClaw HTTP** is enough to return **`render_message`**. |
| **TV type / OS** (Android TV, Linux TV, …)? | **Not part of protocol conformance** — any Shell that can **HTTP(S) + JSON** works. Details: **[implementer-orientation.md §4.1](../../docs/guides/implementer-orientation.md)**. |
| **Internet vs LAN**? | **Internet-accessible gateways are common** in production; **LAN-only** is fine for lab. Not mandated by the spec — **[§4.2](../../docs/guides/implementer-orientation.md)**. |
| **Pairing** (hardcoded token vs code on TV vs fingerprint)? | All **product choices**: minimal token, or **TV shows code + server confirms**, or add **opaque device fingerprint** with confirm — **[§4.3](../../docs/guides/implementer-orientation.md)**, **[device-pairing-session.md](../../docs/guides/device-pairing-session.md)**, optional **`pair-server`** here. |
| **Python on TV** vs **Kotlin**? | This adapter is **Python** on the **server**. TV is often **Kotlin/Java**; **irrelevant** to wire validity. |

---

## Where this runs (important)

This adapter is **not** a service operated by the OpenHarness project. It is meant to be **installed by each operator** on **their own machine** next to their **OpenClaw** (or compatible) server — same host, same container network, or a nearby VM — so **your users’ infrastructure**, not a central “our server,” runs the bridge.

### Standalone install (without cloning the full OpenHarness repo)

1. Copy this folder (or install from a **separate git repository** / release tarball you publish).
2. **Schema:** either set **`OPENHARNESS_SCHEMA_PATH`** to a local copy of **`openharness-v1.draft.json`**, or place that file **next to these scripts** as **`./openharness-v1.draft.json`** (same directory as `openharness-adapter-openclaw.py`). Copy the schema from the **OpenHarness** protocol repository (path **`schema/openharness-v1.draft.json`**) or your fork.
3. Optional: `pip install jsonschema` for **`validate`** / **`--validate`**.
4. Run **`bridge-server`**, **`demo-server`**, optional **`pair-server`** (example SQLite pairing), or your process manager pointing at **`openharness-adapter-openclaw.py`**.

### Monorepo vs independent repository

| Approach | When to use |
|----------|-------------|
| **Stay in OpenHarness under `adapters/openharness-adapter-openclaw/`** | Contributors and protocol releases; simplest for CI that already validates examples. |
| **Split into an independent repo** (e.g. `openharness-adapter-openclaw`) | You want **version tags**, **PyPI**, or **issue trackers** separate from the protocol; operators **`git clone`** only the adapter. **Recommended** if your distribution story is “download this kit beside OpenClaw.” Keep README links to **PROTOCOL.md** and the **schema** as the single source of truth (copy schema into releases or document `OPENHARNESS_SCHEMA_PATH`). |

Graduating to a new repo is already suggested in **[adapters/README.md](../README.md)** (“thin in-tree → dedicated repo when releases grow”).

---

## Purpose

Shell-side **bridge** between an **OpenClaw** (or similar) runtime and OpenHarness **`request`** / **`response`** JSON. The Python CLI helps you **emit** golden examples, **build** requests from flags, **validate** against the schema, **inspect** responses, and **POST** JSON to an Engine over HTTP (**stdlib** only).

### Who ships the integration (production)

**OpenClaw does not adapt to OpenHarness for you.** Upstream runtimes stay agnostic; **your product** owns the adapter: map OpenClaw’s process/IPC/events into conformant **`request`** JSON, call your **Harness Engine** (or gateway), and apply **`response`** / **`action_directives`** on the way back. This folder is a **starting point** (CLI + patterns), not an official OpenClaw plugin.

### v1 scope: basic dialogue

A reasonable **first production** cut is **minimal Q&A**: stable **`session_id`** + **`user_intent`**, transport auth per PROTOCOL §7, and an Engine that returns at least one text-capable directive (e.g. **`render_message`**). Negotiate **`capabilities`** honestly; defer rich cards, attachments, and multi-step SOPs until you publish Engine support.

### OpenClaw is an agent stack, not an OpenHarness speaker

If **OpenClaw** already exposes answers over **HTTP** (or you add a thin HTTP façade), you can run **`openclaw_harness_bridge`** as a **Harness-shaped adapter**: it accepts OpenHarness **`request`** JSON, forwards **`user_intent` / `session_id` / `tenant_id`** to your OpenClaw endpoint, and wraps the reply in a conformant **`response`** with **`render_message`**. Commands: **`bridge-once`** (stdin/file → stdout) and **`bridge-server`** (`POST /v1/openharness`). Configure with environment variables (see table below). If **`OPENCLAW_HTTP_URL`** is unset, the bridge uses a **stub** echo (for wiring tests only).

| Environment variable | Meaning |
|---------------------|---------|
| **`OPENCLAW_HTTP_URL`** | POST target for your OpenClaw (or façade) API. If empty → stub backend. |
| **`OPENCLAW_HTTP_BODY_TEMPLATE`** | Python `.format` template; defaults to JSON with `{user_intent_json}`, `{session_id_json}`, `{tenant_id_json}` (already JSON-escaped). |
| **`OPENCLAW_RESPONSE_TEXT_PATH`** | Optional dotted path into the JSON response for the reply string (e.g. `choices.0.message.content`). If unset, tries `reply`, `text`, `message`, … |
| **`OPENCLAW_HTTP_AUTHORIZATION`** | Optional `Authorization` header value (e.g. `Bearer …`). |
| **`OPENCLAW_HTTP_HEADERS_JSON`** | Optional extra headers as JSON object. |
| **`OPENCLAW_HTTP_TIMEOUT`** | Seconds (default `120`). |

### Example pairing / account gateway (SQLite) — **reference only**

The OpenHarness protocol **does not** require a specific pairing implementation. This folder includes an **optional example**: **`pair-server`** stores pending codes and issued device tokens in **SQLite** (stdlib), with **`POST /pair/create`** and **`POST /pair/confirm`**. Helpers **`pair-create`** and **`pair-confirm`** match the demo flow but default to **`http://127.0.0.1:8790`**.

**You are not obligated to keep pairing logic in this repository forever.** Treat it as a **starting point** for operators who deploy beside OpenClaw: **fork it**, **replace it** with your IdP/OAuth service, or **move it** to a separate product repository when your account/device requirements grow. Tokens are **opaque demo strings** — use hashed storage, rotation, and audit in real systems.

| Command | Role |
|---------|------|
| **`pair-server`** | `--db`, `--ttl`, optional **`--confirm-secret`** (confirm endpoint must send the same via body `confirm_secret` or header `X-Pairing-Confirm`) |
| **`pair-create`** / **`pair-confirm`** | HTTP clients for the above (default base URL **8790**) |

**Not** a substitute for: multi-region HA, rate limiting at scale, compliance programs — add those in **your** deployment.

### What to implement on the OpenClaw side (for AI / agent developers)

OpenClaw **does not need to parse OpenHarness JSON**. Your team implements a **normal HTTP API** in front of the OpenClaw runtime (or inside your fork) that this bridge can call. Minimum expectations:

1. **HTTP POST endpoint** — Accepts **`application/json`** on the URL you set in **`OPENCLAW_HTTP_URL`**. Method must be POST (or put a reverse proxy that translates).
2. **Request body fields** — The bridge sends JSON derived from **`OPENCLAW_HTTP_BODY_TEMPLATE`**. By default it includes **`user_intent`** (user message), **`session_id`**, and **`tenant_id`** (JSON-encoded strings). **OpenClaw / your agent** should:
   - Feed **`user_intent`** into the model / tool pipeline as the user message.
   - Use **`session_id`** (and **`tenant_id`** if multi-tenant) to **load or create** conversation state / memory so multi-turn dialogue stays coherent.
3. **Response JSON** — Return a JSON object that contains the assistant reply as a **string** in one of: top-level **`reply`**, **`text`**, **`message`**, **`output`**, **`content`**, or a path you configure with **`OPENCLAW_RESPONSE_TEXT_PATH`** (e.g. nested LLM output). Non-JSON or plain text bodies are treated as the raw reply string.
4. **Auth** — If the endpoint is protected, set **`OPENCLAW_HTTP_AUTHORIZATION`** or **`OPENCLAW_HTTP_HEADERS_JSON`** so the bridge can authenticate. OpenClaw validates tokens; **OpenHarness does not** define OAuth details.
5. **Errors** — Prefer HTTP **4xx/5xx** with a JSON body when the model fails; the bridge surfaces failures as **`response.status: error`** when the upstream call fails. For production, document your error codes separately.
6. **Scope** — OpenClaw remains responsible for **routing, tools, safety, and model choice**; this adapter only **translates** OpenHarness ↔ your chat HTTP contract.

**Summary for AI implementers:** implement a **single chat/completion HTTP API** that takes **session + user text** and returns **assistant text**; align field names with **`OPENCLAW_HTTP_BODY_TEMPLATE`** and **`OPENCLAW_RESPONSE_TEXT_PATH`**.

### Relationship to device pairing & long-lived use

Production pairing (your own HTTPS APIs, Android TV APK, account system) stays **outside** this repo. See **[device-pairing-session.md](../../docs/guides/device-pairing-session.md)** for recommended patterns.

This folder also includes a **local reference demo** (`demo-server`, `demo-pair-create`, `demo-pair-confirm`, `demo-chat`) — **stdlib HTTP only**, file-backed store, **not for production**. It exists so you can walk through **pair code → confirm → Bearer token → OpenHarness POST to a mock `/demo/harness`** on one machine.

**After** real pairing succeeds, this adapter is enough to exercise the wire path:

- Use **`build-request`** with stable **`--session-id`**, **`--tenant-id`**, and optional **`--credential-ref`** consistent with your gateway.
- Use **`post`** with **`--header 'Authorization: Bearer …'`** (or mTLS at a lower layer) so long-lived secrets stay in **transport**, not in the JSON body when possible.

## Contents

| File | Role |
|------|------|
| `openharness-adapter-openclaw.py` | CLI: emit, build-request, validate, inspect, post, **demo-***, **bridge-*** |
| `openclaw_harness_bridge.py` | OpenHarness ↔ OpenClaw HTTP adapter (`bridge-once`, `bridge-server`) |
| `pairing_demo.py` | Reference pairing + mock Harness HTTP handler (imported by the CLI) |
| `openharness_paths.py` | Resolves schema path (`OPENHARNESS_SCHEMA_PATH` or file beside this folder) |
| `pairing_example_server.py` | **Example** SQLite pairing gateway (`pair-server`, `pair-create`, `pair-confirm`) |

## Usage

From this directory (or with `python3` path adjusted):

```bash
python3 openharness-adapter-openclaw.py --help

# Golden examples
python3 openharness-adapter-openclaw.py emit-minimal
python3 openharness-adapter-openclaw.py emit-im

# Build a request envelope (optional --patch JSON merge, --validate)
python3 openharness-adapter-openclaw.py build-request \
  --tenant-id tenant_demo --session-id sess_1 --user-intent "Hello" \
  --shell-kind openclaw_cli --shell-version 0.1.0 --validate

# Validate JSON (file or stdin)
python3 openharness-adapter-openclaw.py validate path/to/message.json
cat message.json | python3 openharness-adapter-openclaw.py validate

# Summarize a request or response
python3 openharness-adapter-openclaw.py inspect examples/im-cli/response-success.json

# POST body to Engine (pipe or --file); mirrors correlation_id to X-Correlation-ID by default
python3 openharness-adapter-openclaw.py emit-minimal | \
  python3 openharness-adapter-openclaw.py post --url https://engine.example/harness/v1

# After pairing: same session line + transport auth (example)
python3 openharness-adapter-openclaw.py build-request --tenant-id t1 --session-id sess_tv_paired \
  --user-intent "Hello" --credential-ref cred_from_gateway --validate | \
  python3 openharness-adapter-openclaw.py post --url https://engine.example/harness/v1 \
  --header "Authorization: Bearer $DEVICE_ACCESS_TOKEN"
```

Schema validation uses **`jsonschema`** if installed (same as `scripts/validate_examples.py`).

### OpenHarness ↔ OpenClaw bridge (dialogue)

```bash
# Stub (no OPENCLAW_HTTP_URL): echo OpenClaw
python3 openharness-adapter-openclaw.py build-request --tenant-id t1 --session-id s1 --user-intent "Hello" | \
  python3 openharness-adapter-openclaw.py bridge-once --validate

# Point at your OpenClaw HTTP API (body/response shape via env)
export OPENCLAW_HTTP_URL="https://your-host/openclaw/v1/chat"
export OPENCLAW_RESPONSE_TEXT_PATH="data.reply"
python3 openharness-adapter-openclaw.py bridge-server --port 8788
# Clients POST OpenHarness JSON to http://127.0.0.1:8788/v1/openharness
```

### Example pairing gateway (SQLite, reference)

```bash
# Terminal 1
python3 openharness-adapter-openclaw.py pair-server --port 8790
# Terminal 2 — same flow as demo-pair-* but with SQLite and /pair/create
python3 openharness-adapter-openclaw.py pair-create --base-url http://127.0.0.1:8790
python3 openharness-adapter-openclaw.py pair-confirm AB12CD34 --tenant-id tenant_demo --base-url http://127.0.0.1:8790
```

Optional: **`--confirm-secret`** on **`pair-server`** and **`pair-confirm`** for a shared secret on the confirm step. **Not** required to keep this in this repo in production — see **Example pairing / account gateway** above.

### Local reference demo (pair → chat)

Terminal 1:

```bash
python3 openharness-adapter-openclaw.py demo-server --port 8765
```

Terminal 2 — simulate **TV** getting a code:

```bash
python3 openharness-adapter-openclaw.py demo-pair-create --base-url http://127.0.0.1:8765
```

Terminal 2 — simulate **server CLI** confirming the code (use the printed `code` and your tenant):

```bash
python3 openharness-adapter-openclaw.py demo-pair-confirm AB12CD34 --tenant-id tenant_demo --base-url http://127.0.0.1:8765
```

Export the printed `access_token` / `session_id` (or use the stderr hints), then:

```bash
export OPENHARNESS_DEMO_TOKEN=...
export OPENHARNESS_DEMO_SESSION_ID=...
python3 openharness-adapter-openclaw.py demo-chat --tenant-id tenant_demo --user-intent "Hello" \
  --base-url http://127.0.0.1:8765 --validate
```

The mock Engine returns a minimal **`render_message`** directive. Your real TV app would call **`POST …/demo/pair/create`** over HTTPS to the same API shape you deploy in production.

---

## 中文

**运行位置：** 本适配器 **不是** OpenHarness 官方替你托管的服务；应由 **各使用方** 在 **自有 OpenClaw 服务器旁**（同机、同 Docker 网络或相邻 VM）**本地下载/安装**。规范与 Schema 仍以 **OpenHarness 协议仓库** 为准。

**独立安装：** 可复制本目录，设置 **`OPENHARNESS_SCHEMA_PATH`**，或将 **`openharness-v1.draft.json`** 放在与本脚本 **同一目录**；可选 **`pip install jsonschema`**。详见上文 **Standalone install**。

**是否独立仓库：** 若面向「用户只拉适配器、不克隆整个协议仓」，建议 **单独建仓库** 并发 release / PyPI；协议与 Schema 通过 README **链接 + 拷贝 schema** 对齐。亦可持续放在 OpenHarness 的 **`adapters/`** 下维护。

**配对 / 账号网关（示例）：** **`pair-server`**（SQLite + **`/pair/create`** / **`/pair/confirm`**）为 **资料性参考实现**，**不**要求长期必须留在本仓库；生产可 **自建服务**、**fork** 或 **迁出独立仓**。详见上文 **Example pairing / account gateway**。

---

**性质：** 资料性 Shell 侧工具；线格式以 **PROTOCOL + Schema + 金样** 为准。

**OpenClaw / AI 请先读：** **[implementer-orientation.md](../../docs/guides/implementer-orientation.md)** — 说明 **本目录不是电视 APK**（电视端另工程）、**v1 对话不必先做完整 Harness Engine**（**`bridge-server` + OpenClaw** 即可）、**电视品牌/系统为产品自选**。

**谁来做对接：** **OpenClaw 不会替你们接 OpenHarness**；**你们自建适配层**——把 OpenClaw 侧的事件/IPC 映射成 **`request`**，把 Engine 的 **`response`** 执行回去。本目录是 **起点**（CLI 与约定），不是 OpenClaw 官方插件。

**v1 范围：** 生产第一版可以只做 **最基本对话**（稳定 **`session_id`**、**`user_intent`**、传输层鉴权；Engine 至少返回可展示文本的指令，例如 **`render_message`**）。能力以后再扩。

**OpenClaw 与协议：** OpenClaw 本质是 **智能体/运行时**，**不会**自带 OpenHarness；若已有 **HTTP 接口**，可用 **`openclaw_harness_bridge`**（**`bridge-once` / `bridge-server`**）把 OpenHarness **`request`** 转成对你方 API 的 POST，并把返回文本包成 **`render_message`**。见上文 **Environment variable** 表。

**OpenClaw / 智能体侧要实现什么（给 AI 与后端实现者）：** OpenClaw **不必解析 OpenHarness JSON**。你们实现的是 **普通 HTTP 对话接口**：**POST**、**`application/json`**，请求体里至少能收到 **`user_intent`**（用户话）、**`session_id`**、**`tenant_id`**（与 **`OPENCLAW_HTTP_BODY_TEMPLATE`** 对齐）；用 **`session_id`/`tenant_id`** 做会话与多租户状态；返回 JSON，且回复文本在 **`reply`/`text`/`message`** 等字段之一，或通过 **`OPENCLAW_RESPONSE_TEXT_PATH`** 指向嵌套字段。鉴权用 **`OPENCLAW_HTTP_AUTHORIZATION`** 等由你们校验。路由、工具、模型、安全策略仍在 **OpenClaw 侧**；本桥只负责 **OpenHarness ↔ 你们聊天 API** 的字段搬运。

**用途：** 本脚本提供 **发样例、拼 request、校验、读 response 摘要、HTTP POST、配对 demo、OpenClaw 桥**（标准库）。Engine 地址、鉴权、重试由部署侧配置（参见 **[http-transport.md](../../docs/profiles/http-transport.md)** 等）。

**设备配对与长期使用：** 产品级配对见 **[device-pairing-session.md](../../docs/guides/device-pairing-session.md)**。本目录提供 **本地参考演示**（**`demo-server`** / **`demo-pair-create`** / **`demo-pair-confirm`** / **`demo-chat`**）：仅用于本机走通「发码 → 确认 → Bearer → 调 mock Engine」，**不可用于生产**。正式环境需自建 HTTPS、账号库与真实 Harness Engine。配对完成后仍可用 **`build-request`** + **`post --header`** 对接真实端点。
