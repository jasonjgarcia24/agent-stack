# Secret handoff — the no-echo pattern

Every skill in this plugin needs at least one API key or token. They all use
the same discipline. Read this once; the setup skills just point back here.

## Two hard rules

1. **Never render a secret to the conversation.** Not in command output, not in
   a file you cat, not in a commit. Anything printed lands in logs, telemetry,
   and terminal scrollback — once there, it's compromised and must be rotated.
2. **Never commit a secret.** Keys live in `~/.hermes/.env` (or process env),
   which must be gitignored. Reference a key by name ("the OpenRouter key"),
   never by value.

## The no-echo handoff

When the user needs to put a key into `~/.hermes/.env`, have **them** run this
in a real terminal (not piped through the agent). `read -rs` reads silently —
the key never appears on screen, in history, or in the conversation:

```bash
read -rs KEY_NAME && \
  printf 'KEY_NAME=%s\n' "$KEY_NAME" >> ~/.hermes/.env && \
  unset KEY_NAME
```

Substitute the real variable name, e.g.:

```bash
read -rs OPENROUTER_API_KEY && \
  printf 'OPENROUTER_API_KEY=%s\n' "$OPENROUTER_API_KEY" >> ~/.hermes/.env && \
  unset OPENROUTER_API_KEY
```

Press Enter, paste the key at the silent prompt (nothing shows), press Enter
again. Done.

> Hermes also ships `hermes config set <KEY> <value>`, which routes secrets to
> `.env` automatically — but it takes the value as a shell argument, so it
> **echoes the key into shell history**. Prefer the `read -rs` form above.

## Verifying a key landed WITHOUT revealing it

To confirm a key exists without printing its value:

```bash
# Key names only — never the values:
cut -d= -f1 ~/.hermes/.env | grep -v '^#' | sort -u

# Length-only audit (does NOT reveal the value):
awk -F= '/^[A-Z]/ {printf "%s: %d bytes\n", $1, length($2)}' ~/.hermes/.env
```

If you must grep `.env` for a pattern, match **key names only**
(`grep -E '^OPENROUTER'`), never a pattern that would surface the value line in
full. A filter intended as a sanity check will happily print the secret if you
let it.

## If a secret leaks anyway

Tell the user immediately, recommend rotating that key at the provider, and do
**not** try to scrub the transcript — it's already in logs you can't reach.
Rotation is the only real remedy.
