---
name: setup-composio
description: Connect an agent to real apps (Gmail, GitHub, Slack, Notion, Google Calendar, 500+ more) through a single Composio MCP connector, with per-app OAuth held server-side. Use this whenever the user wants to give their agent app access, "set up Composio," wire Gmail/GitHub/Slack/Notion to Claude Code or Hermes, add tool/app integrations via one connector, or asks how to let the agent send email / read issues / act on their accounts without hand-managing per-app credentials. Covers the two integration paths (Claude Code /mcp OAuth vs Hermes MCP), connecting apps in the dashboard, a multi-app verification, and the credential-surface check that proves no per-app secrets land on your host.
---

# Set up Composio (one connector → many apps)

Composio is a single MCP endpoint that fronts 500+ apps. You authenticate each
app **once, in Composio's dashboard**, and Composio holds those OAuth tokens
server-side. Your agent only ever sees one secret — the Composio API key — and
calls any connected app through the one connector. Swap agents and you don't
re-do any per-app auth.

> Read `../agent-stack-library/references/secrets-handling.md` before the key
> step. This skill assumes you may layer onto a Hermes agent (`setup-hermes-openrouter`),
> but it works identically driving Claude Code.

## Prerequisites

- A **Composio account** (`composio.dev`, free tier: 20k tool calls/mo, no
  card). The user signs up.
- A **Composio API key** from the dashboard (`Settings → Project Settings` for
  a project key, which the MCP `x-api-key` header expects; `Settings →
  Organization` for an org key).

> **Heads-up (verified May 2026):** new orgs default `require_mcp_api_key=true`,
> so the API key header is mandatory on the MCP endpoint. A May 2026 security
> incident force-rotated all keys created before 2026-05-23 — create a **fresh**
> key now rather than reusing an old one.

## Pick your integration path

There are two ways to attach Composio, depending on which agent drives it.
Both rely on the same hosted MCP and the same dashboard OAuth — the difference
is only the client.

| Path | Use when | Auth mechanism |
|---|---|---|
| **A — Claude Code `/mcp`** | You're driving from Claude Code (or Claude Desktop) | Browser **OAuth** flow |
| **B — Hermes MCP** | You want the connected apps available to your Hermes agent (and its Telegram bot) | API key header or OAuth |

### Path A — Claude Code `/mcp` (OAuth, simplest)

1. Install the Composio CLI (optional but handy). This pipes a remote script
   from Composio's vendor domain to a shell — trust the domain, or download and
   inspect `https://composio.dev/install` before running it:
   ```bash
   curl -fsSL https://composio.dev/install | bash
   ```
2. In Claude Code, run `/mcp` and choose to add/authenticate Composio. This
   runs an OAuth flow in the browser — approve it, and Composio's MCP tools
   (`COMPOSIO_SEARCH_TOOLS`, `COMPOSIO_MULTI_EXECUTE_TOOL`,
   `COMPOSIO_MANAGE_CONNECTIONS`, …) become available in the session.

### Path B — Hermes MCP

Store the key, then add the Composio MCP server. **Important nuance learned the
hard way:** the unified endpoint `https://connect.composio.dev/mcp` is an
**OAuth** endpoint — passing only `x-api-key` to it returns `401`. For an
API-key wire-up you must first create an MCP server config in the dashboard,
which yields a **per-server URL** (`https://backend.composio.dev/v3/mcp/<SERVER_ID>`)
that accepts the `x-api-key` header.

1. Hand off the key (user runs it; never echoed):
   ```bash
   read -rs COMPOSIO_API_KEY && \
     printf 'COMPOSIO_API_KEY=%s\n' "$COMPOSIO_API_KEY" >> ~/.hermes/.env && \
     unset COMPOSIO_API_KEY
   ```
2. Add the server. For the OAuth path against the unified endpoint:
   ```bash
   hermes mcp add composio --auth oauth --url https://connect.composio.dev/mcp
   ```
   For the API-key path, create a server in the dashboard first, then add its
   per-server URL with an `x-api-key` header (Hermes interpolates `${COMPOSIO_API_KEY}`
   from `.env` — see env-conventions). Test before trusting it:
   ```bash
   hermes mcp test composio   # redirect to a file and inspect for 401/auth errors; don't print the key
   ```

## Connect 2–3 apps (in the dashboard)

In the Composio dashboard, create/choose an MCP config and connect the apps you
want. Good first set, in order of "useful + low blast radius":

- **Gmail** — the cleanest "agent did something real" demo.
- **GitHub** — real engineering action; safe at read-only scopes.
- **Google Calendar** or **Linear** — a third app for a cross-app workflow test.

Each app runs an OAuth flow **in Composio's UI**, not on your machine. Default
to read-only / least-privilege scopes where offered. You can revoke anytime
from the app's own settings (Google/GitHub) and from the Composio dashboard.

## Verify

The point isn't "it connected" — it's "the agent calls real apps through one
connector, and no per-app secret touched my host." Two checks:

**1. Multi-app tool call.** Ask the agent (Claude Code or Hermes) to do
something that hits ≥2 apps in one go, e.g.: *"Using your Composio tools, list
the subjects of my 3 most recent Gmail threads and my 5 most recently updated
GitHub repos."* Expect real data from both — proving one connector → many apps.

**2. Credential-surface check.** Confirm zero per-app OAuth credentials live
locally — only the Composio key should be present:

```bash
cut -d= -f1 ~/.hermes/.env | grep -v '^#' | sort -u    # expect COMPOSIO_API_KEY, no GMAIL_/GITHUB_/GOOGLE_ keys
grep -cEi '^(google|gmail|github|gh|gcal|googlecalendar|linear|slack|notion)_(client|secret|token|key|refresh|access|oauth)' ~/.hermes/.env   # expect 0
```

`0` per-app credentials + a working multi-app call = the Composio value prop,
demonstrated.

## Security reality check

Because the connector reads your real inbox, an agent with Gmail access sees
**every OTP / 2FA code** that lands there. For anything beyond personal
experimentation, scope tightly: route 2FA to a separate inbox, use read-only
where possible, and prefer per-app least privilege over the convenience of
"connect everything."

## Notes & gotchas

- `connect.composio.dev/mcp` = OAuth only; `x-api-key` against it → 401. Use a
  dashboard-generated per-server URL for the key path.
- The "official" branding on community MCP wrappers can be ambiguous — prefer
  Composio's first-party endpoints and the dashboard flow.
- Post-cutoff tool: verify endpoints/flags against `docs.composio.dev` if
  anything here doesn't match what you see.
