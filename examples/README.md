# OpenHarness example messages (Informative)

These JSON files are **golden references** for implementers and **AI coding assistants**. They are **not** normative; **[PROTOCOL.md](../docs/PROTOCOL.md)** and the **[Schema](../schema/openharness-v1.draft.json)** are.

## Layout

| Path | Purpose |
|------|---------|
| `minimal/request.json` | Smallest valid **Shell → Engine** message (`requestMessage`). |
| `minimal/response.json` | Smallest valid **Engine → Shell** success (`responseMessage`). |
| `im-cli/request.json` | Illustrative **IM / bot-platform CLI** request: `shell`, `task_hint`, `continuation`, attachment **ref**. |
| `im-cli/response-success.json` | Matching success response with `supported_capabilities` / empty `capability_denials`. |

See **[../docs/profiles/im-bot-shell.md](../docs/profiles/im-bot-shell.md)** for responsibility split (Shell vs Engine) on this class of integrations.

## Validation

The Schema root is a **`oneOf`** of `requestMessage` | `responseMessage`. Validate **each file separately** against the Schema (many validators require picking the matching branch).

**Check JSON syntax only (no Schema):**

```bash
python3 -m json.tool minimal/request.json > /dev/null && echo OK
```

**Schema validation** (if you have a JSON Schema CLI, e.g. `ajv`):

```bash
# example — tool-specific; adapt to your stack
# npx ajv validate -s ../schema/openharness-v1.draft.json -d minimal/request.json
```

Contributions welcome: add CI that validates all `examples/**/*.json`.

---

中文：本目录为 **金样 JSON**，供实现与 AI 对齐；**规范性** 仍以 **PROTOCOL** 与 **Schema** 为准。请求与响应应 **分别** 校验（Schema 顶层为 `oneOf`）。IM/机器人 Shell 职责划分见 **[../docs/profiles/im-bot-shell.md](../docs/profiles/im-bot-shell.md)**。
