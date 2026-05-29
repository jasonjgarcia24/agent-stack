---
name: setup-telegram-gateway
description: Make a Hermes agent reachable from your phone via a Telegram bot, always-on, with a watchdog that auto-restarts the gateway if it crashes. Use this whenever the user wants to talk to their agent from Telegram, "set up the Telegram gateway / bot," reach the agent from their phone, make the agent always-on, add a messaging front-end, or set up the crash-recovery watchdog. Covers creating the bot with BotFather, the no-echo token handoff, the systemd --user gateway with its native watchdog, the one-time pairing-code approval (deny-by-default access control), enabling linger for always-on, fault-injection verification, and clean teardown.
---

# Set up the Telegram gateway (talk to your agent from your phone)

This puts a messaging front-end on a Hermes agent: you DM a Telegram bot, the
agent replies. It's the transcript's "digital employee you just message"
experience. Hermes installs the gateway as a `systemd --user` service whose
**native watchdog** restarts it automatically if it dies — that's the
reliability layer that makes an always-on agent trustworthy.

> Requires a working Hermes (`setup-hermes-openrouter`). Read
> `../agent-stack-library/references/secrets-handling.md` before the token step.

## Step 1 — Create the bot

In Telegram, message **@BotFather**, send `/newbot`, follow the prompts (name +
username). BotFather returns a **bot token**. Note the bot's `@username` too —
that's what you'll DM.

## Step 2 — Hand off the token

User runs it; never echoed (see secrets-handling):

```bash
read -rs TELEGRAM_BOT_TOKEN && \
  printf 'TELEGRAM_BOT_TOKEN=%s\n' "$TELEGRAM_BOT_TOKEN" >> ~/.hermes/.env && \
  unset TELEGRAM_BOT_TOKEN
```

The token in `.env` **auto-enables** Hermes' Telegram channel — there's no
separate "enable Telegram" wizard. Hermes connects in polling mode and
registers the bot's commands on startup.

## Step 3 — Install the gateway service (with the watchdog)

```bash
hermes gateway install
```

This creates a `systemd --user` unit (`hermes-gateway.service`) configured with
a native watchdog: `Restart=always`, `RestartSec=5`, flap-limiting disabled. No
supervisor script to write — the watchdog is built in. Confirm it's up:

```bash
systemctl --user status hermes-gateway.service
```

## Step 4 — Pair your account (deny-by-default access control)

Hermes does **not** use a raw user-ID allowlist. It uses a one-time
pairing-code flow, deny-by-default — strangers who DM the bot get nothing until
the owner approves them:

1. DM the bot (`@your_bot`) anything.
2. The bot replies with a **pairing code** and instructions, e.g.:
   `Ask the bot owner to run: hermes pairing approve telegram <CODE>`
3. On the host, approve it (substitute the code the bot gave you):
   ```bash
   hermes pairing approve telegram <CODE>
   ```
4. DM again — the agent now responds. Only paired accounts get through.

## Step 5 — Make it always-on (linger)

A `systemd --user` service stops when the user logs out. Enable **linger** so it
survives logout / reboot and runs headless:

```bash
loginctl enable-linger "$USER"
```

## Step 6 — Verify the watchdog (fault injection)

Don't take "Restart=always" on faith — prove it. Kill the gateway hard and
watch systemd bring it back:

```bash
systemctl --user status hermes-gateway.service | grep "Main PID"   # note the PID
kill -9 <PID>
sleep 12
systemctl --user show hermes-gateway.service -p NRestarts -p ActiveState
```

`NRestarts` increments and `ActiveState=active` again within ~5–12s (the second
restart can be slightly longer due to anti-flap backoff). DM the bot to confirm
it reconnected. That's first-hand proof the agent self-heals.

## Bonus — native failure alerts (no email wrapper needed)

Unlike email (see `setup-agentmail`), Telegram **is** a native Hermes
`cron --deliver` target. If you want "ping me when a job fails," a Telegram
alert is the simplest path — no wrapper script. Configure the failing cron with
Telegram delivery and you'll get the alert in the same chat.

## Teardown

Reverse it cleanly when done:

```bash
hermes gateway stop
hermes gateway uninstall          # removes the systemd unit
loginctl disable-linger "$USER"   # only if nothing else needs linger
```

The bot token stays in `.env` (delete the line if you're fully done); the bot
itself can be deleted via @BotFather.

## Notes & gotchas

- Footprint is user-level and reversible: `~/.config/systemd/user/hermes-gateway.service`
  + an enable symlink + user linger. No root needed.
- If the gateway won't start, check `journalctl --user -u hermes-gateway.service`
  — most often a missing/expired `TELEGRAM_BOT_TOKEN` or a model-auth failure
  bubbling up from the underlying Hermes.
- Post-cutoff tool: confirm `hermes gateway` / `hermes pairing` subcommands
  against `hermes gateway --help` if they differ from this file.
