# OpenHarness example messages (Informative)

These JSON files are **golden references** for implementers and **AI coding assistants**. They are **not** normative; **[PROTOCOL.md](../docs/PROTOCOL.md)** and the **[Schema](../schema/openharness-v1.draft.json)** are.

**CI:** On every push/PR, GitHub Actions runs **`python scripts/validate_examples.py`** (requires `jsonschema` from **`requirements-dev.txt`**). Golden files **must** stay aligned with the Schema.

## Layout

| Path | Purpose |
|------|---------|
| `minimal/request.json` | Smallest valid **Shell → Engine** message (`requestMessage`). |
| `minimal/response.json` | Smallest valid **Engine → Shell** success (`responseMessage`). |
| `minimal/response-error.json` | **`status`: `error`** with `retryable` / `details`. |
| `minimal/response-protocol-unsupported.json` | Error path: **`protocol_version_unsupported`**. |
| `im-cli/request.json` | Illustrative **IM / bot-platform CLI** request: `shell`, `task_hint`, `continuation`, attachment **ref**. |
| `im-cli/response-success.json` | Success with `supported_capabilities` / empty `capability_denials`. |
| `im-cli/response-capability-denials.json` | **Non-empty `capability_denials`** + degraded success `action_directives`. |

See **[../docs/profiles/im-bot-shell.md](../docs/profiles/im-bot-shell.md)** for responsibility split (Shell vs Engine) on IM-style integrations. Optional HTTP header hints: **[../docs/profiles/http-transport.md](../docs/profiles/http-transport.md)**.

## Validation (local)

```bash
pip install -r requirements-dev.txt   # once; use PyPI if your mirror lacks jsonschema
python scripts/validate_examples.py
```

**Check JSON syntax only (no Schema):**

```bash
python3 -m json.tool minimal/request.json > /dev/null && echo OK
```

Contributions welcome: add fixtures and keep **`scripts/validate_examples.py`** green.

---

中文：本目录为 **金样 JSON**；**CI** 会对 **全部** `examples/**/*.json` 做 **Schema 校验**（见 **`requirements-dev.txt`** 与 **`scripts/validate_examples.py`**）。IM/机器人 Shell 职责见 **[../docs/profiles/im-bot-shell.md](../docs/profiles/im-bot-shell.md)**；HTTP 可选惯例见 **[../docs/profiles/http-transport.md](../docs/profiles/http-transport.md)**。
