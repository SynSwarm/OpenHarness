# openharness-adapter-android-tv

**Status:** Guidance-only placeholder (no APK or library in this repo). **Normative** wire format: **[PROTOCOL.md](../../docs/PROTOCOL.md)** + **[schema](../../schema/openharness-v1.draft.json)** + **[examples](../../examples/)**.

**Language:** English first · [中文](#中文)

---

## Purpose

An **Android TV** app (Leanback / TV input / remote-driven UI) can act as the **Shell**: collect **`context`** (session, user intent, device/UI state), send OpenHarness **`request`** messages to your **Harness Engine**, and apply **`response`** / **`action_directives`** (or degrade per PROTOCOL §11 when unknown).

This directory holds **orientation** for that product line. **Concrete development** (Gradle module, CI, releases) is expected in a **separate repository** to keep this protocol repo small; when you publish it, add a **link** in the table in **[../README.md](../README.md)** (Registry) and optionally in **[shell-at-scale.md](../../docs/guides/shell-at-scale.md)**.

---

## What to read (in order)

| Order | Document | Why |
|-------|----------|-----|
| 1 | **[PROTOCOL.md](../../docs/PROTOCOL.md)** | Wire format, `action_directives`, §11 unknown types, errors |
| 2 | **[schema/openharness-v1.draft.json](../../schema/openharness-v1.draft.json)** | Validatable JSON shape |
| 3 | **[examples/](../../examples/)** | Golden request/response JSON |
| 4 | **[profiles/im-bot-shell.md](../../docs/profiles/im-bot-shell.md)** | Who maps platform IDs → `context`; capabilities; attachments as refs |
| 5 | **[guides/shell-at-scale.md](../../docs/guides/shell-at-scale.md)** | Where Shell docs live at scale; links to external repos |
| 6 | **[profiles/http-transport.md](../../docs/profiles/http-transport.md)** | Illustrative HTTP framing (if your Shell uses HTTP to the Engine) |
| 7 | **[guides/device-pairing-session.md](../../docs/guides/device-pairing-session.md)** | Optional: one-time TV pairing codes + long-lived device credentials + stable `session_id` |
| 8 | **[guides/openclaw-operator-kit.md](../../docs/guides/openclaw-operator-kit.md)** | Optional: **HTTP gateway** beside OpenClaw (`pair-server` + `bridge-server`), public URL sketch, **§8 Shell handoff** — same gateway is **Shell ↔ Engine** generic, not TV-only |

Engine URL, TLS, and **`credential_ref`** resolution stay in **deployment / gateway** docs — not redefined here. If you deploy **OpenClaw + this repo’s bridge**, use the operator kit for **which URL the TV calls** (pairing vs `/v1/openharness`) and what to persist on device.

---

## Implementation checklist (Shell on TV)

- [ ] Fill **`request.context`** and, where applicable, **`shell`** (e.g. `shell_kind`, version, locale) honestly for your TV client.
- [ ] Declare **`capabilities`** you can honor; handle **`capability_denials`** / **`supported_capabilities`** in responses.
- [ ] **Attachments:** use **`ref_id`** pipelines — no large base64 in the body (PROTOCOL §9.1).
- [ ] **Privacy:** classify **`environment_state`** with **`privacy_tier`** when capturing sensitive UI or viewing data.
- [ ] On **`action_directives`:** ordered processing, **`requires_user_approval`**, **`risk_tier`**; unknown **`action_type`** → no side effects (§11).

Reuse the same validation idea as **`scripts/validate_examples.py`** in your own repo’s CI for outbound/inbound JSON.

---

## 中文

**性质：** 本目录仅 **指引占位**，**不含** APK 或实现代码。线格式以 **PROTOCOL + Schema + 金样** 为准。

**用途：** **Android TV** 应用可作为 **Shell**，采集遥控器/Leanback 等上下文，向 Engine 发送 **`request`**，并按 **`response`** / **`action_directives`** 渲染或降级（§11）。

**独立仓库：** 完整 **Gradle 工程、发版、CI** 建议在 **单独仓库** 开发；上线后在本仓 **[../README.md](../README.md)** 的 Registry **登记外链**，并可参考 **[shell-at-scale.md](../../docs/guides/shell-at-scale.md)** 的落点说明。

**设备配对与长期使用：** 见 **[device-pairing-session.md](../../docs/guides/device-pairing-session.md)**（资料性建议：验证码配对、设备 token、`session_id` 持久化等）。

阅读顺序与实现检查项见上文英文表与清单。
