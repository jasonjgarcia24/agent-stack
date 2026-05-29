---
name: setup-agentmail
description: Give an agent its own real email inbox via AgentMail so it can send and receive mail programmatically (status reports, self-alerts on failure, human-in-the-loop email). Use this whenever the user wants the agent to have an email address, "set up AgentMail," send email from the agent, receive/act on inbound mail, or email the operator when something breaks. Covers signup/free tier, the no-echo key handoff, creating an inbox, a bundled stdlib send+list script, and the important nuance that Hermes can't natively deliver alerts to email (only Telegram/Discord/Signal) — so email self-alerts need the thin wrapper this skill provides.
---

# Set up AgentMail (an inbox the agent owns)

AgentMail is an API-first email provider built for agents: each inbox is a REST
resource with its own address, two-way send/receive, and webhooks for inbound.
It gives your agent an identity it can send *from* and receive *at* — useful for
status digests, human-in-the-loop approvals, and "email me when a job fails."

> Read `../agent-stack-library/references/secrets-handling.md` before the key
> step. A working Hermes (`setup-hermes-openrouter`) is assumed but not
> required — the send/receive script is plain Python and runs anywhere.

## Prerequisites

- An **AgentMail account** (`agentmail.to`, free tier: 3 inboxes, 3,000
  emails/mo, no card). The user signs up.
- An **AgentMail API key** from the dashboard. Auth is a simple API key (no
  OAuth).

## Step 1 — Hand off the key

User runs it; never echoed (see secrets-handling):

```bash
read -rs AGENTMAIL_API_KEY && \
  printf 'AGENTMAIL_API_KEY=%s\n' "$AGENTMAIL_API_KEY" >> ~/.hermes/.env && \
  unset AGENTMAIL_API_KEY
```

## Step 2 — Create an inbox

Create one in the dashboard (or via API). You'll get an address like
`you-1234@agentmail.to`. That's the agent's identity — note it; the send script
uses it as the `from` and you'll check it for inbound.

## Step 3 — Send + verify with the bundled script

There's no need to hand-write the HTTP calls — this skill ships
`scripts/agentmail.py`, a dependency-free (stdlib `urllib`) client that sends a
message and lists the inbox. Run it sourcing the key from `.env`:

```bash
set -a && . ~/.hermes/.env && set +a && \
  python3 scripts/agentmail.py send \
    --inbox you-1234@agentmail.to \
    --to you@example.com \
    --subject "AgentMail test" \
    --text "Hello from the agent." ; \
  unset AGENTMAIL_API_KEY

# confirm it landed / see inbound:
set -a && . ~/.hermes/.env && set +a && \
  python3 scripts/agentmail.py list --inbox you-1234@agentmail.to ; \
  unset AGENTMAIL_API_KEY
```

A successful send prints an HTTP 200 + a `message_id`; `list` shows the inbox
count incrementing. That's send **and** receive proven first-hand.

## The self-alert nuance (read before wiring "email me when it breaks")

The headline use case is "the agent emails you when a cron job or skill fails."
That works, but **not** out of the box with Hermes, and the reason is worth
understanding so you don't fight it:

- Hermes natively *detects* a cron/skill failure and can *trigger* on it.
- But Hermes has **no native error/failure hook**, and its `cron --deliver`
  targets only **messaging platforms (Telegram / Discord / Signal) — not
  email**.

So the email leg needs a thin wrapper: wrap the failing job so that on non-zero
exit it calls `scripts/agentmail.py send` to fire the alert, then exits non-zero
itself. Pattern:

```bash
#!/usr/bin/env bash
# alert-wrapper.sh — run a job; email the operator if it fails.
set -a && . ~/.hermes/.env && set +a
if ! "$@"; then
  python3 /path/to/scripts/agentmail.py send \
    --inbox you-1234@agentmail.to --to operator@example.com \
    --subject "[AGENT ALERT] job failed: $*" \
    --text "Exit non-zero at $(date -u). Command: $*"
  exit 1
fi
```

If you'd rather avoid the wrapper, the **native, simpler** self-alert path is a
Telegram failure alert via `cron --deliver` (see `setup-telegram-gateway`) —
use email when the agent needs an email *identity*, Telegram when you just want
to be pinged.

## Notes & gotchas

- Inbound in real time uses webhooks/websockets; for setup verification, polling
  `list` is enough.
- Keep the inbox address out of commits if you treat it as sensitive; the API
  key always stays in `.env`, never rendered.
- Post-cutoff tool: confirm endpoints against `docs.agentmail.to` if the script
  ever 4xxs unexpectedly.
