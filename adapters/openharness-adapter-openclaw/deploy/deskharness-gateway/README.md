# deskharness.com gateway (reference deployment)

**Status:** Reference only. **Does not** change **[PROTOCOL.md](../../../../docs/PROTOCOL.md)**. Same semantics as **[openclaw-operator-kit.md §7](../../../../docs/guides/openclaw-operator-kit.md)**.

This folder is **not** a second HTTP stack in Python. The “gateway” is **TLS + path routing** (Caddy or nginx) in front of the existing processes:

| Path | Backend (default) | Role |
|------|-------------------|------|
| `/pair/*` | `pair-server` **127.0.0.1:8790** | Pairing (`/pair/create`, `/pair/confirm`, `GET /pair/health`) |
| `/v1/openharness`, `/openharness` | `bridge-server` **127.0.0.1:8788** | OpenHarness ↔ OpenClaw |
| `/health` | `bridge-server` **127.0.0.1:8788** | Liveness (bridge) |

**OpenClaw** is **not** on this public hostname. Only **`pair-server`** and **`bridge-server`** sit behind `gw.deskharness.com`. The bridge calls OpenClaw via **`OPENCLAW_HTTP_URL`**:

| Where OpenClaw runs | Typical `OPENCLAW_HTTP_URL` |
|----------------------|------------------------------|
| **Same machine** as `bridge-server` (lab / single-tenant all-in-one) | `http://127.0.0.1:PORT/…` |
| **User’s / tenant’s server** (OpenClaw **not** in deskharness’s rack) | **HTTPS URL reachable from this gateway**, e.g. `https://user-host.example/v1/chat/completions` — plus auth headers if required |

The reference **`bridge-server`** reads **one** URL from the environment. **Per-user OpenClaw endpoints** need **your** routing (multiple bridge instances, a BFF, or a custom gateway) — not something this Caddyfile solves by itself.

---

## 1. Start backends

From this repository:

```bash
chmod +x start-backends.sh
# Same host as OpenClaw:
# export OPENCLAW_HTTP_URL="http://127.0.0.1:YOUR_OPENCLAW_PORT/..."
# OpenClaw on the user's server (reachable from this host):
export OPENCLAW_HTTP_URL="https://user-openclaw.example/v1/chat/completions"
./start-backends.sh
```

Optional: `PAIR_PORT`, `BRIDGE_PORT`, `HOST` (default `127.0.0.1`).

---

## 2. Point DNS and TLS

- Create **`gw.deskharness.com`** → your server’s public IP.
- Run **Caddy** (auto HTTPS) or **nginx** with the provided configs.

**Caddy** (example):

```bash
caddy run --config Caddyfile
```

**nginx:** adapt `nginx.conf.example` into your `sites-enabled` and install certificates (e.g. certbot).

---

## 3. Shell clients (e.g. TV)

Use the **same paths on HTTPS**:

- Pairing base: `https://gw.deskharness.com` → `POST …/pair/create`, etc.
- Dialogue: `POST https://gw.deskharness.com/v1/openharness`

---

## 4. Alternate hostnames

Copy the config and replace `gw.deskharness.com` with `api.deskharness.com` or another name; keep upstream ports unless you change `start-backends.sh` / process manager.
