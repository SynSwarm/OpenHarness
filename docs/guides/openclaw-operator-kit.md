# OpenClaw operator kit (“skill pack”) — mental model & layout

**Status:** Informative. **Does not** change **[PROTOCOL.md](../PROTOCOL.md)**. For **OpenClaw maintainers**, **integrators**, and **AI agents** packaging a “drop-in” experience beside OpenClaw.

**Language:** English first · [中文](#中文)

---

## 1. Where the misunderstanding comes from

A common first draft looks like:

| Draft name | Intended role |
|------------|----------------|
| `openharness_server.py` | Runs next to OpenClaw: pairing API + OpenHarness POST endpoint |
| `openharness_tv_client.py` | Runs on the TV: `--pair`, then chat with token |

That layout is **directionally right** for a **demo**, but two corrections avoid long-term confusion:

1. **In this repository, the “server” is already split into commands** — not one monolithic file. You map **one logical “gateway”** to **`bridge-server`** (OpenHarness ↔ OpenClaw HTTP) and **`pair-server`** (example pairing store). Same HTTP surface as in the draft; different **packaging** (CLI subcommands on `openharness-adapter-openclaw.py`).
2. **A Python file on the TV is not the product default.** Real TVs are often **Kotlin/Java** (Android TV) or another stack. A Python “TV client” should be labeled **reference Shell** or **dev simulator**: it proves the **HTTP contract** (`/pair/create`, `/pair/confirm`, `POST /v1/openharness`), not the shipping TV app.

**Protocol truth:** conformance is **wire JSON + PROTOCOL behavior**. **OS and language are irrelevant** to validity; only your ability to **HTTP(S) + JSON** matters. See **[implementer-orientation.md §4](./implementer-orientation.md)**.

---

## 2. Recommended mapping: “two files” → this repo

| Your draft | Maps to in OpenHarness adapter | Notes |
|------------|--------------------------------|--------|
| Server: pairing + `/v1/openharness` | **`pair-server`** (e.g. port **8790**) + **`bridge-server`** (e.g. port **8788**) | Two processes today; see §5 for a single launcher. |
| `POST /pair/create` | Same path on **`pair-server`** | TV shows `code` from JSON response. |
| `POST /pair/confirm` | Same path on **`pair-server`** | Run **`pair-confirm`** on the **server** (or your admin UI), **not** “read logs only”. |
| `POST /v1/openharness` | **`bridge-server`** | Bearer token checked by **your** gateway policy; example store is SQLite via pairing flow. |
| TV / Shell client | **`pair-create`** + HTTP client building OpenHarness **`request`** | Use **[openharness-adapter-openclaw](../../adapters/openharness-adapter-openclaw/)** as reference; ship TV in **native** code. |

Normative wire and env vars: **[adapters/openharness-adapter-openclaw/README.md](../../adapters/openharness-adapter-openclaw/README.md)**.

---

## 3. What an “out-of-the-box skill pack” should contain

Think **operator bundle**, not “OpenClaw parses OpenHarness”:

| Artifact | Purpose |
|----------|---------|
| **`.env.example`** | `OPENCLAW_HTTP_URL`, `OPENCLAW_HTTP_BODY_TEMPLATE`, `OPENCLAW_RESPONSE_TEXT_PATH`, optional `OPENCLAW_HTTP_AUTHORIZATION`; bridge/pair **ports**. |
| **Install snippet** | Copy adapter + **`schema/openharness-v1.draft.json`** (or `OPENHARNESS_SCHEMA_PATH`). |
| **Run instructions** | Start **`pair-server`** then **`bridge-server`** (or one wrapper script). |
| **Pairing UX doc** | TV displays code → operator runs **`pair-confirm CODE --tenant-id …`** (or HTTP `POST /pair/confirm`). |
| **Reference Shell** (optional) | Python script = **lab only**; rename e.g. `openharness_shell_reference.py` so “TV” is not implied. |
| **OpenClaw-side note** | OpenClaw stays a **normal agent HTTP API**; the bridge is the only piece that speaks OpenHarness JSON to the Shell. |

**OpenClaw Cursor skill (if you ship one):** point to this file + adapter README + **[implementer-orientation.md](./implementer-orientation.md)** so agents do not recreate duplicate servers with wrong names.

---

## 4. `OPENCLAW_HTTP_URL` — no universal path

There is **no** single global OpenClaw URL in the OpenHarness spec. The bridge POSTs **your** JSON body (template-controlled) to **whatever URL you configure**.

- If your stack exposes e.g. `http://127.0.0.1:18789/agent`, **verify** in **your** OpenClaw version’s docs or by probing: method **POST**, **Content-Type**, required fields, and response shape.
- If the default body does not match, set **`OPENCLAW_HTTP_BODY_TEMPLATE`** and **`OPENCLAW_RESPONSE_TEXT_PATH`** so the bridge can extract assistant text. See the env table in the adapter README.

**Skill pack checklist:** “Document the exact OpenClaw HTTP contract **for this release**” — link or paste a minimal request/response example next to `.env.example`.

---

## 5. Pairing confirmation — avoid “logs only”

The example **`pair-server`** already supports programmatic confirm:

- **CLI:** `python3 openharness-adapter-openclaw.py pair-confirm <CODE> --tenant-id <T> --base-url http://127.0.0.1:8790`
- **HTTP:** `POST /pair/confirm` with the same JSON as in **`pairing_example_server.py`**

Logging the code is for **debugging**; the **product** flow should use **CLI, admin API, or dashboard** calling `/pair/confirm`.

---

## 6. Optional: one logical “server” for demos

For “single command” demos you can ship a **thin launcher** (shell or Python) that starts:

1. `pair-server --port 8790` (background)
2. `bridge-server --port 8788` (foreground)

The Shell (TV or reference script) then uses:

- Pairing base URL → **8790**
- OpenHarness POST → **8788** `/v1/openharness`

Merging pairing + bridge into **one Python process** is possible later; **not required** for protocol correctness.

---

## 中文

### 偏差从哪来

把方案想成「一个 `openharness_server.py` + 电视上跑 `openharness_tv_client.py`」**方向对**，但要两点校正：

1. **本仓里“服务端”已拆成子命令**：**`pair-server`**（配对）+ **`bridge-server`**（OpenHarness ↔ OpenClaw HTTP），合起来才是你草稿里的「网关」。
2. **电视端 Python 脚本只适合当参考 / 模拟器**；真机多为 **Kotlin/Java** 等。技能包里应写清：**参考 Shell**，生产用原生实现同样 HTTP 即可。

**协议层面**：只要遵守 **PROTOCOL + JSON**，与系统无关 — 见 **[implementer-orientation.md §4](./implementer-orientation.md)**。

### 开箱即用技能包建议装什么

- **`.env.example`**（`OPENCLAW_HTTP_URL`、模板、响应路径、鉴权、端口）
- **安装方式**（适配器目录 + schema）
- **启动方式**（先 pair 再 bridge，或一层启动脚本）
- **配对说明**：电视显示码 → 服务端用 **`pair-confirm`** 或 **`POST /pair/confirm`**，不要依赖「只看日志」
- **OpenClaw HTTP**：**无固定全局路径**；按 **你方 OpenClaw 版本** 文档配置 URL 与 **`OPENCLAW_HTTP_BODY_TEMPLATE` / `OPENCLAW_RESPONSE_TEXT_PATH`**

### Cursor / OpenClaw 技能文件

让技能 **链接本文 + adapter README + implementer-orientation**，避免重复造一套命名冲突的 `openharness_server.py` 而不知道对应 **`bridge-server` + `pair-server`**。

---

## See also

- **[adapters/openharness-adapter-openclaw/README.md](../../adapters/openharness-adapter-openclaw/README.md)** — commands, env vars, `pair-*`, `bridge-*`
- **[device-pairing-session.md](./device-pairing-session.md)** — product-level pairing patterns
- **[implementer-orientation.md](./implementer-orientation.md)** — TV-agnostic scope, network, pairing levels
