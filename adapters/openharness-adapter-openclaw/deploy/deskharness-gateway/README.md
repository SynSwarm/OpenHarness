# deskharness.com gateway (reference deployment)

**Status:** Reference only. **Does not** change **[PROTOCOL.md](../../../../docs/PROTOCOL.md)**. Same semantics as **[openclaw-operator-kit.md §7](../../../../docs/guides/openclaw-operator-kit.md)**.

This folder is **not** a second HTTP stack in Python. The “gateway” is **TLS + path routing** (Caddy or nginx) in front of the existing processes:

| Path | Backend (default) | Role |
|------|-------------------|------|
| `/pair/*` | `pair-server` **127.0.0.1:8790** | Pairing (`/pair/create`, `/pair/confirm`, `GET /pair/health`) |
| `/v1/openharness`, `/openharness` | `bridge-server` **127.0.0.1:8788** | OpenHarness ↔ OpenClaw |
| `/health` | `bridge-server` **127.0.0.1:8788** | Liveness (bridge) |

**OpenClaw** is reached **only** from `bridge-server` via **`OPENCLAW_HTTP_URL`** (usually `http://127.0.0.1:…` on the same host), not through this public hostname.

---

## 1. Start backends

From this repository:

```bash
chmod +x start-backends.sh
export OPENCLAW_HTTP_URL="http://127.0.0.1:YOUR_OPENCLAW_PORT/..."   # your chat HTTP API
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
