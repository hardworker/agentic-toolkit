---
name: cf-access
description: Reach Cloudflare Access–gated hosts (internal CI, dashboards, APIs, MCP servers) from the CLI, from Node clients, and from long-running processes whose credential would otherwise expire. Use when a request to an internal host answers with a redirect to cdn-cgi/access/login or a 403, when an MCP server or daemon behind Cloudflare Access works right after launch and stops hours later, when an Access app has no service-token policy so only browser SSO can mint a JWT, or when the user mentions cf-access, cloudflared access login/token, CF_Authorization, the cf-access-token header, or asks to install, repair, or inspect the local Access token broker and proxy.
argument-hint: "[install | status | uninstall | login | token <app> | curl <url>]"
---

# Cloudflare Access from the CLI

A token broker (`cf-access`), a localhost proxy that keeps injecting fresh tokens (`cf-access-proxy`), and a Node preload that routes gated traffic into the proxy with no client changes (`cf-access-preload.cjs`).

The broker and `curl` mode work anywhere `cloudflared` runs; the launchd daemon in `install.sh` is macOS-only.

## Why a broker is needed

- An Access app whose policy allows only an IdP (Google Workspace, Okta, …) has **no service-token path**. A JWT can only come from a browser SSO round-trip — a headless client cannot get one on its own, ever.
- `cloudflared` keeps an **org-wide session** plus a per-app token cache at `~/.cloudflared/<host>-<aud>-token`. So the first login is the only interactive one: it warms the org, and every other app in the same org then mints silently. That is why `cf-access login` with no arguments is the normal entry point.
- App tokens are short-lived (typically ~24h). Anything that reads its credential **once at startup** — most MCP servers, any daemon taking a header from env — works for a day and then fails with a login redirect that looks nothing like an auth error. The proxy exists for exactly that case.

## Three layers — pick by what the client can do

| The client can | Use | Renewal |
|---|---|---|
| take a fresh header/env on **every** invocation (shell, curl, short-lived CLI) | `cf-access token` / `cookie` / `curl` / `env` | per invocation |
| only be pointed at a **URL** (any language, any runtime) | proxy **fixed port** — a line in `~/.config/cloudflare-access/proxy` | per request, by the proxy |
| be a **Node** process with no useful config surface | `NODE_OPTIONS=--require …/cf-access-preload.cjs` → proxy **dynamic port** | per request, by the proxy |

Direct mode is simplest and should be preferred for anything short-lived. Reach for the proxy the moment the process outlives its token.

## Files

All of these live in this skill's directory, beside this SKILL.md.

| File | Role |
|---|---|
| `cf-access` | token broker: `token`, `cookie`, `env`, `curl`, `login`, `list` |
| `cf-access-proxy` | localhost HTTP fronts; injects and renews `cf-access-token` per request |
| `cf-access-preload.cjs` | `--require` shim: patches `http`/`https`/`fetch` to route allowed hosts into the proxy |
| `install.sh` | symlinks the three into a bin dir, seeds config, loads the launchd agent |
| `apps.example`, `hosts.example` | config templates (placeholders — edit after install) |

## Install

```bash
<skill-dir>/install.sh              # symlink + seed config + load the daemon
<skill-dir>/install.sh status       # links, config, cloudflared, daemon, port, token TTLs
<skill-dir>/install.sh uninstall    # unload daemon, remove our symlinks; keeps config and tokens
```

`--bin-dir DIR` (default `~/.claude/bin`) and `--no-daemon` are the only knobs. Installs are **symlinks**, so editing a script in the skill directory is live immediately — but the daemon holds the old code until it restarts:

```bash
launchctl kickstart -k gui/$(id -u)/local.cf-access-proxy
```

Requires `cloudflared` (`brew install cloudflared`) and `node`. Then one interactive step:

```bash
cf-access login
```

## Config

`~/.config/cloudflare-access/` — three files, all optional except as noted:

| File | Purpose |
|---|---|
| `apps` | app origins `login`/`list` operate on. Origins only, no paths |
| `hosts` | **domain suffixes** the proxy will forward to. Required for the proxy — with no `hosts` file nothing is allowed, and the preload patches nothing |
| `proxy` | optional fixed ports: `<port> <upstream-origin>` per line, hot-reloaded (polled every 2s, no restart) |

`hosts` holds suffixes rather than apps so an app added under the domain next month needs no configuration. It is also the allowlist that keeps the dynamic port from being an open forwarder on loopback — **only put domains you own in it**.

## Broker subcommands

| Command | Purpose |
|---|---|
| `cf-access token [--no-login] <app>` | print a valid JWT, refreshing if under 10 min of life. `--no-login` never opens a browser (for scripts) |
| `cf-access cookie <app>` | `CF_Authorization=<jwt>`, for tools that want a cookie |
| `cf-access env <app> <VAR> -- <cmd…>` | exec `cmd` with `VAR=<jwt>` — the MCP-launcher form. `env(1)`, so `VAR` may contain hyphens |
| `cf-access curl <url> [args…]` | `curl` with `cf-access-token:` injected |
| `cf-access login [<app>…]` | refresh stale tokens; default is every app in `apps` |
| `cf-access list` | remaining lifetime per configured app |

Two details worth knowing, because both look like bugs otherwise: an app URL is truncated to its **origin** (cloudflared caches per hostname, a path would miss the cache), and `login` **clears the cached token first** — `cloudflared access login` otherwise hands back the cached token even seconds from expiry. The cleared token is stashed and restored if the login fails.

## Proxy behaviour

- **Dynamic port** (default `8780`): the upstream comes from an `x-cf-access-upstream` header (`x-cf-access-scheme` for http). One listener covers every allowed host, so a new app needs no route entry. A bare `GET /` answers `400 missing x-cf-access-upstream` — that is the health check `install.sh status` uses.
- **Gating is learned, not configured.** The first request to an origin goes out bare; only a redirect to `cdn-cgi/access/login` proves a token is needed. Non-gated hosts therefore never trigger an SSO attempt, and a newly gated host starts getting tokens on its own.
- **A client's own credential wins.** A request already carrying a service token (`CF-Access-Client-Id` + `CF-Access-Client-Secret`), a `cf-access-token`, or a `CF_Authorization` cookie is forwarded untouched and triggers no SSO. Only if Access *rejects* it does the broker step in and retry — so a working credential is never overridden, and a broken one still gets service.
- **No request ever waits on a human indefinitely.** A request holds for at most `CF_ACCESS_HOLD` seconds (default 20, under the usual 30s client timeout) and is then answered `511`, while the login keeps running in the background — so the client's retry lands on a token. `CF_ACCESS_HOLD=0` never waits at all. A mint that wedges is abandoned after `CF_ACCESS_LOGIN_DEADLINE` (default 120s); the proxy stops waiting on it whether or not the child can be killed, because `cloudflared` ignores `SIGTERM` and holds its pipe open.
- **Renewal.** Tokens are cached per origin until 10 min before expiry, minting is single-flight (a stampede collapses into one mint), and a browser login is rate-limited to once a minute so a burst of failures cannot stack up tabs.
- **Request bodies are buffered** so a token retry replays the request byte-for-byte.
- Status codes it originates: `511` no token available (run `cf-access login <origin>`), `403` host not in `hosts`, `508` the upstream is the proxy itself, `502` transport error, `400` missing upstream header.

## Wiring an MCP server

Pick by lifetime. A server that is spawned per session and dies with it can take the token at launch; one that runs for days must go through the proxy.

**Per-launch token** — the client reads a header from env at startup:

```json
{
  "mcpServers": {
    "internal": {
      "command": "/absolute/path/to/bin/cf-access",
      "args": ["env", "https://ci.example.com", "TOOL_HEADER_cf-access-token", "--",
               "node", "/path/to/server.mjs"]
    }
  }
}
```

MCP configs generally do not expand `~` or `$HOME` — write the absolute path.

**Proxy, no server changes** — the server keeps its real URL, the preload reroutes it:

```json
{
  "mcpServers": {
    "internal": {
      "command": "node",
      "args": ["/path/to/server.mjs"],
      "env": {
        "NODE_OPTIONS": "--require /absolute/path/to/bin/cf-access-preload.cjs",
        "SERVER_API_URL": "https://ci.example.com"
      }
    }
  }
}
```

For a non-Node client, give it a fixed port instead — `8790 https://ci.example.com` in `~/.config/cloudflare-access/proxy`, then point the client at `http://127.0.0.1:8790`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| client gets a 302 to `cdn-cgi/access/login` | no token, or the client never went through the proxy | `cf-access login <origin>`; check the client is Node (the preload only patches Node) or give it a fixed port |
| `511 no token for <origin>` from the proxy | SSO needed and not possible headlessly | `cf-access login <origin>` in a session with a browser |
| `403 <host> is not an allowed upstream` | host missing from `hosts` | add the domain suffix; no restart needed |
| `508 … is this proxy` | an upstream origin points back at a proxy port | fix the `proxy` route or the client's URL |
| `token FAILED` in the log | login failed, or inside the 60s cooldown | run `cf-access login <origin>` by hand and watch it |
| worked yesterday, dead today | token expired in a process that snapshotted it | move that client to the proxy or the preload |
| an MCP server times out at exactly its client timeout (30s), repeatedly, while `curl` to the same host is fine | the client is being held behind an SSO the proxy cannot complete headlessly | check the log for `is Access-gated — minting a token` with no `token ok` after it; run `cf-access login <origin>` once, then retry. Lower `CF_ACCESS_HOLD` to fail faster |
| log says `client credential rejected by Access` | the client's service token is not on the app's policy (Access reports `service_token_status: false` on its login page) | fix the service token in Cloudflare, or accept the broker fallback — but know the client now depends on a browser token |
| a client you never wired is going through the proxy | `NODE_OPTIONS` is set globally (e.g. in `~/.claude/settings.json`), so **every** Node process is patched | intended for blanket coverage; scope it to one client's `env` if you want it narrower |
| `cf-access list` shows `no token` right after a successful login | login was for a different origin (path or scheme mismatch) | use the exact origin, no path |
| daemon keeps restarting | `node`/`cloudflared` not on the daemon's `PATH` | re-run `install.sh` (it writes the plist with the detected `node`) and read `~/Library/Logs/cf-access-proxy.log` |

## Rules

- A JWT is a bearer credential for a whole app. Never print one into a shared transcript, a commit, an issue, or a log. Pass tokens by env or header; `cf-access token` exists for piping, not for pasting.
- Never widen `hosts` to a domain the user does not control — every entry is a host the loopback proxy will forward to on behalf of anything running as the user.
- The proxy binds `127.0.0.1` only. Do not change that, and do not add an auth-free route to a host outside the user's org.
- Do not hand-edit files in `~/.cloudflared/` — they are cloudflared's cache, keyed by the token's own `aud`.
- `cf-access login` is interactive by design: it opens a browser tab and the user completes SSO. In a headless or CI context use `token --no-login` and fail loudly instead of hanging.
- Diagnose with `install.sh status` before touching anything; it distinguishes "no token", "daemon down", "host not allowed", and "not installed", which produce very similar client-side symptoms.
