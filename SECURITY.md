# Security

This plugin is **setup guidance** — Markdown runbooks plus a few small,
dependency-light helper scripts. It runs no server and stores no data. But it is
credential-heavy by nature: the skills walk you through handling API keys for
OpenRouter, Composio, AgentMail, Telegram, and E2B.

## How secrets are handled

The skills never ask you to paste a key into a chat or a command argument. They
use a no-echo handoff into `~/.hermes/.env`, documented once in
[`skills/agent-stack-library/references/secrets-handling.md`](skills/agent-stack-library/references/secrets-handling.md):

- Keys are read with `read -rs` (silent) and appended to `~/.hermes/.env`.
- `~/.hermes/.env` and other secret-bearing paths (`*.key`, `*.pem`,
  `credentials.json`, `token.json`, `.hermes/`) are blocked by
  [`.gitignore`](.gitignore) so they can't be committed.
- Verification uses key **names** or **lengths** only — never values.

If you ever see a secret rendered to a terminal, log, or commit while following
these skills, treat it as compromised: **rotate the key at the provider** and do
not try to scrub the transcript.

## Known hardening notes (in the skills themselves)

- **E2B live stream** (`setup-e2b-vm`): the `require_auth=False` demo URL is
  unauthenticated and control-capable — use `require_auth=True` and treat the
  URL as a secret for anything beyond a throwaway sandbox.
- **Composio** (`setup-composio`): an agent with Gmail access can read every
  OTP/2FA code in that inbox — scope tightly and prefer a separate 2FA inbox.
- **Pipe-to-shell installers** (uv, Composio): these execute remote scripts from
  the vendors' own domains. Trust the domain or download and inspect first; pin
  a version where the installer supports it.

## Reporting

Found a real credential committed here, or a security issue in a script or
instruction? Please open an issue at
<https://github.com/jasonjgarcia24/agent-stack/issues> (omit any secret values
from the report).
