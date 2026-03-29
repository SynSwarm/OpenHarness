# Contributing to OpenHarness

Thank you for helping improve the OpenHarness protocol and documentation.

## Authority

- **Normative wire format:** `docs/PROTOCOL.md` (English, authoritative).  
- **Chinese mirror:** `docs/PROTOCOL.zh.md` — must stay aligned with the English spec.  
- **JSON Schema:** `schema/openharness-v1.draft.json` — must match PROTOCOL.

Informative docs (`docs/SCOPE.md`, `docs/OVERVIEW.md`, `docs/guides/`, `examples/`) **do not** override PROTOCOL.

## Implementers (third-party Harness / Shell / AI-assisted coding)

See **`docs/guides/AI_INTEGRATION.md`** and golden JSON under **`examples/`** before building adapters.

## Changing the protocol

1. Edit **`docs/PROTOCOL.md`** first.  
2. Mirror substantive changes in **`docs/PROTOCOL.zh.md`**.  
3. Update **`schema/openharness-v1.draft.json`** as needed.  
4. Update **`examples/**/*.json`** so golden samples remain consistent.  
5. Run **`pip install -r requirements-dev.txt`** (PyPI) and **`python scripts/validate_examples.py`** — CI enforces the same check via **`.github/workflows/validate-examples.yml`**.  
6. If README or cross-links need updates, include them in the same PR.

Keep changes focused; avoid drive-by refactors unrelated to the protocol change.

## Pull requests

- Use clear commit messages and PR descriptions in complete sentences.  
- Note whether the change is **normative** (wire/schema) or **informative** (guides only).  
- MIT license applies; do not commit secrets or large binary blobs into examples (use attachment **refs** per PROTOCOL §9.1).

## Questions

Open issues or discussions on the project repository for design questions before large normative changes.
