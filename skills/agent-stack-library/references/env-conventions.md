# `~/.hermes/` conventions — where everything lives

Hermes hardcodes its state home at `~/.hermes/`. The whole stack piggybacks on
it as the single place credentials and config live, whether or not Hermes is
the harness driving a given component.

## The two files

| File | Holds | Committed? |
|---|---|---|
| `~/.hermes/.env` | **Secrets** — all API keys and tokens. | **Never.** Must be gitignored. |
| `~/.hermes/config.yaml` | **Non-secret config** — model provider/default, `mcp_servers`, gateway settings. | Safe to commit if you want, but it can contain references; check before committing. |

Get the paths from Hermes itself if unsure:

```bash
hermes config path       # -> ~/.hermes/config.yaml
hermes config env-path   # -> ~/.hermes/.env
hermes config show       # current merged config (may print secret VALUES — avoid in shared sessions)
```

## Canonical key names in `~/.hermes/.env`

The stack standardizes on these names. Keeping them consistent means
`config.yaml` interpolation and helper scripts find them without per-machine
tweaks:

| Key | Used by |
|---|---|
| `OPENROUTER_API_KEY` | Hermes model access (setup-hermes-openrouter) |
| `COMPOSIO_API_KEY` | Composio connector (setup-composio) |
| `AGENTMAIL_API_KEY` | AgentMail inbox send/receive (setup-agentmail) |
| `TELEGRAM_BOT_TOKEN` | Telegram gateway (setup-telegram-gateway) |
| `E2B_API_KEY` | E2B cloud-desktop VMs (setup-e2b-vm, setup-claude-code-on-e2b) |

## Env-var interpolation in `config.yaml`

Hermes expands `${VAR}` placeholders (NOT bare `$VAR`) in `mcp_servers`
entries — inside `url`, `headers`, `transport.command`, `transport.args`, and
`env` — resolved at connect time from the environment, which includes
everything in `~/.hermes/.env`. This is how a secret stays in `.env` and is only
referenced (never duplicated) in `config.yaml`:

```yaml
mcp_servers:
  some_http_server:
    url: "https://example.com/mcp"
    headers:
      Authorization: "Bearer ${SOME_API_KEY}"   # value comes from ~/.hermes/.env
```

> Note (verified May 2026): docs and an open Hermes issue have disagreed on
> whether header interpolation is fully supported in every version. If a header
> `${VAR}` doesn't expand, test the MCP connection with `hermes mcp test <name>`
> (redirect output to a file and inspect for `401`/auth errors rather than
> printing it) and fall back to the server's OAuth flow if available.

## Sourcing `.env` for a one-off script (without leaking)

When a helper script (E2B, AgentMail) needs the keys, source `.env` into the
environment for just that command and unset afterward:

```bash
set -a && . ~/.hermes/.env && set +a && python3 your_script.py ; \
  unset OPENROUTER_API_KEY COMPOSIO_API_KEY AGENTMAIL_API_KEY TELEGRAM_BOT_TOKEN E2B_API_KEY
```

The trailing `unset` keeps the keys from lingering in the shell environment
after the script exits.
