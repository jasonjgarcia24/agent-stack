# agent-stack

A Claude Code plugin: six source-grounded **setup runbooks** for standing up a
self-hosted AI agent stack. Each skill is a verified walkthrough distilled from
first-hand setup in the [agent-dev](https://github.com/jasonjgarcia24) project —
not vibes, not model memory.

**Initial setup cost: ~$5 out of pocket** *(as of 2026-05-29)* — almost
everything is free: Composio (20k tool calls/mo), AgentMail (3 inboxes, 3k
emails/mo), and Telegram are free with no card; E2B ships a **$100 one-time
credit** (no card). The one real out-of-pocket item is **OpenRouter**, which
needs a prepaid credit balance to use its API — a **$5 minimum top-up** gets you
started. Actual consumption is tiny: model tokens run a fraction of a cent per
test exchange, and the full stack was exercised end-to-end for **well under
$0.01** of that OpenRouter balance plus **under $0.01** of the E2B credit. So the
$5 is a floor you mostly don't spend, not a recurring cost.

| Skill | Stands up |
|---|---|
| `setup-hermes-openrouter` | A Hermes Agent harness on OpenRouter (the base layer) |
| `setup-composio` | One Composio connector → 500+ apps, OAuth held server-side |
| `setup-agentmail` | A real email inbox the agent owns (send/receive + self-alerts) |
| `setup-telegram-gateway` | A phone-reachable, always-on Telegram bot with a crash watchdog |
| `setup-e2b-vm` | Cloud-desktop VMs an agent can see and control |
| `setup-claude-code-on-e2b` | Claude Code running inside an E2B VM (+ the locale fix for its TUI) |

A seventh skill, `agent-stack-library`, is a shared reference library the others
read from (secret-handoff pattern, `~/.hermes/.env` conventions, cross-cutting
troubleshooting) — you won't invoke it directly.

Start with `setup-hermes-openrouter`; the others layer on a working Hermes.

## Quick Start

> **Before you start:** these skills walk you through external services that
> require their own free accounts and API keys (OpenRouter, Composio, AgentMail,
> Telegram/BotFather, E2B). The skills never ask you to paste a key into chat —
> they use a no-echo handoff into `~/.hermes/.env`. E2B is the only component
> that involves spend, and it ships a $100 free credit (no card). You'll also
> want Python ≥ 3.11 for Hermes (the Hermes skill shows how to provision it with
> `uv` if your system Python is older).

<details>
<summary><b>Claude Code — Marketplace (recommended)</b></summary>

```
/plugin marketplace add jasonjgarcia24/agent-stack
/plugin install agent-stack@jason-agent-stack
/reload-plugins
/agent-stack:init
```

The first two add the marketplace and install the plugin; the third reloads the
current session so the new skills/commands are callable without restarting
Claude Code; the fourth runs first-run setup (symlinks the seven skills into
`~/.claude/skills/` for short-form access). `/agent-stack:init` is idempotent —
re-running it only fixes what's missing.

To pull a newer version later: **uninstall first then reinstall** (Claude Code's
`/plugin install` skips already-installed plugins, so a vanilla rerun won't pick
up changes):

```
/plugin marketplace update jason-agent-stack
/plugin uninstall agent-stack@jason-agent-stack
/plugin install agent-stack@jason-agent-stack
/reload-plugins
/agent-stack:init
```

> **Two ways to invoke the skills.** After `/agent-stack:init`, each skill is
> addressable by short name (e.g. `setup-hermes-openrouter`) via a user-level
> symlink at `~/.claude/skills/<skill>` → the plugin's skill dir, *and* by its
> plugin-namespaced form (`agent-stack:setup-hermes-openrouter`). Both resolve
> to the same file. Init itself stays namespaced — `/agent-stack:init` only —
> because Claude Code has a built-in `/init` the short form would collide with.

> **SSH errors?** The marketplace clones repos via SSH. If you don't have SSH
> keys on GitHub, either [add a key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
> or switch to HTTPS for fetches:
> ```bash
> git config --global url."https://github.com/".insteadOf "git@github.com:"
> ```

</details>

<details>
<summary><b>Uninstall</b></summary>

Three steps. The first removes the user-level skill symlinks init created; the
next two remove the plugin and marketplace.

```
/agent-stack:init --remove
/plugin uninstall agent-stack@jason-agent-stack
/plugin marketplace remove jason-agent-stack
```

**`--remove` removes** (only if they exist and point at `agent-stack`):

- `~/.claude/skills/agent-stack-library`
- `~/.claude/skills/setup-hermes-openrouter`
- `~/.claude/skills/setup-composio`
- `~/.claude/skills/setup-agentmail`
- `~/.claude/skills/setup-telegram-gateway`
- `~/.claude/skills/setup-e2b-vm`
- `~/.claude/skills/setup-claude-code-on-e2b`

**`--remove` does NOT touch** anything else — this plugin stores no secrets, no
`settings.json` entries, and no user data. Credentials you created while
following the skills live in **`~/.hermes/.env`** and any external accounts
(OpenRouter/Composio/AgentMail/Telegram/E2B); manage those yourself if you want
full cleanup.

</details>

<details>
<summary><b>Claude Code — Local / development clone</b></summary>

Useful if you want to edit the plugin in place and see changes without
reinstalling.

```bash
git clone https://github.com/jasonjgarcia24/agent-stack.git ~/code/agent-stack
claude --plugin-dir ~/code/agent-stack
```

</details>

<details>
<summary><b>Manual install (no plugin marketplace)</b></summary>

Bolt onto an existing Claude Code config without the marketplace:

```bash
git clone https://github.com/jasonjgarcia24/agent-stack.git ~/agent-stack
cd ~/agent-stack

# Skills — symlink each skill directory (include the library so relative
# ../agent-stack-library/ references resolve):
mkdir -p ~/.claude/skills
for s in agent-stack-library setup-hermes-openrouter setup-composio \
         setup-agentmail setup-telegram-gateway setup-e2b-vm \
         setup-claude-code-on-e2b; do
  ln -sf "$PWD/skills/$s" ~/.claude/skills/"$s"
done

# Command (skip the namespaced :init — it stays plugin-scoped):
# (the skills work standalone; no command symlink needed)
```

This plugin needs no `settings.json` permission entries.

</details>

## What's verified vs. what's not

Every procedure was run first-hand (experiments E-002–E-009, May 2026). Honest
caveats the skills carry:

- **E2B substitutes for Orgo.** The original target (Orgo) paywalls at signup;
  E2B is a category peer with a free credit. The hosting *mechanism* is what's
  verified, not Orgo specifically.
- **"Sub-second VM recreate" is marketing.** Measured client-side, create+destroy
  is ~1.3s — fast, but not under a second. The E2B skill states the real numbers.
- **Composio's `connect.composio.dev/mcp` is OAuth-only** — the `x-api-key` path
  needs a dashboard-generated per-server URL. The skill documents both.
- These tools post-date most training cutoffs. Each skill says to re-ground
  against the vendor's current docs if a flag or path drifts.

## License

MIT — see [LICENSE](LICENSE).
