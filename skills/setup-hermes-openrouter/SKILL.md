---
name: setup-hermes-openrouter
description: Stand up a Hermes Agent (Nous Research) harness locally and wire it to a model through OpenRouter. Use this whenever the user wants to install Hermes, "set up a Hermes agent," run a model-agnostic agent harness, configure OpenRouter as the model provider, swap the underlying model, or asks "how do I get the agent running" in the context of this stack. Covers the uv/pip install, ~/.hermes/config.yaml provider+model wiring, the no-echo API-key handoff, a functional smoke test, and one-flag model swapping. This is the foundation skill — the other agent-stack skills (Composio, AgentMail, Telegram) layer on top of a working Hermes.
---

# Set up Hermes Agent on OpenRouter

Hermes is a model-agnostic agent **harness** (the thing that drives a model and
its tools) — not a model itself. OpenRouter is a single API gateway to 200+
models behind one key, which is what makes Hermes' "swap the model freely"
selling point real: one key, change a flag, run a different vendor's model.

This skill gets you from nothing to a Hermes agent that answers prompts and
uses tools. It's the base layer — do this first; the Composio, AgentMail, and
Telegram skills assume a working Hermes at `~/.hermes/`.

> Read `../agent-stack-library/references/secrets-handling.md` before the key
> step, and `../agent-stack-library/references/env-conventions.md` for what
> lives in `~/.hermes/`.

## Prerequisites

- **Python ≥ 3.11.** Hermes' PyPI distribution requires it. If the system
  Python is older (a fresh Ubuntu/VM often ships 3.10), provision 3.12 with
  `uv` — see step 1B. Check with `python3 --version`.
- An **OpenRouter account + API key** (`openrouter.ai/keys`). The user creates
  this; you never type or paste the key (see secrets-handling).

## Step 1 — Install Hermes

Two routes. Prefer **1A (uv + PyPI)** — it's the fastest and it sidesteps the
Python-version gate by letting uv bring its own interpreter.

### 1A — uv + PyPI (recommended)

```bash
# Install uv if absent (no sudo needed). This pipes a remote script from uv's
# vendor domain (astral.sh) to a shell — trust the domain, or download +
# inspect the script first. To pin a known version instead of "latest":
#   curl -LsSf https://astral.sh/uv/0.5.11/install.sh | sh
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Provision Python 3.12 and a venv, then install Hermes into it:
uv python install 3.12
uv venv --python 3.12 ~/.hermes-venv
uv pip install --python ~/.hermes-venv/bin/python hermes-agent

# Put hermes on PATH (or use the full venv path):
ln -sf ~/.hermes-venv/bin/hermes ~/.local/bin/hermes
```

### 1B — manual developer install (when you want the source tree)

```bash
git clone https://github.com/NousResearch/hermes-agent ~/hermes-agent
cd ~/hermes-agent
uv venv && uv pip install -e ".[all,dev]"
```

Verify either route:

```bash
hermes --version    # -> Hermes Agent v0.15.x  (Python 3.12.x)
```

Hermes auto-creates its state home at `~/.hermes/` on first run (config,
sessions, logs, `.env`).

## Step 2 — Point Hermes at OpenRouter

Set the provider and a sensible default model in `~/.hermes/config.yaml`. A
small, cheap, token-frugal model is the right default for *driving the harness*
(reserve big models for long-horizon coding handoffs):

```yaml
model:
  provider: openrouter
  default: google/gemini-2.5-flash-lite
```

`gemini-2.5-flash-lite` has a 1M context window (well past Hermes' ≥64k floor)
and costs a fraction of a cent per exchange. Other good harness-driver choices
on OpenRouter: `deepseek/deepseek-chat`, `anthropic/claude-haiku-4-5`.

## Step 3 — Hand off the OpenRouter key

The user runs this themselves, in a real terminal — the key is never echoed
(full rationale in secrets-handling):

```bash
read -rs OPENROUTER_API_KEY && \
  printf 'OPENROUTER_API_KEY=%s\n' "$OPENROUTER_API_KEY" >> ~/.hermes/.env && \
  unset OPENROUTER_API_KEY
```

## Step 4 — Verify it actually works

Two smoke tests. The first proves connectivity + identity; the second proves
reasoning **plus tool use**, which is what separates "configured" from
"functional":

```bash
# 1) connectivity + which model
hermes -z "In one sentence, confirm you're online and name the model you're running on."

# 2) tool use (file access) — adjust the path to any real dir
hermes -z "Using your tools, count the .md files under the current directory and list their paths."
```

If test 1 errors on auth, re-check that `OPENROUTER_API_KEY` is present in
`~/.hermes/.env` (key name only: `cut -d= -f1 ~/.hermes/.env`). If test 2 just
chats without invoking a tool, the model may be too weak — bump to a stronger
default.

## Step 5 — Prove the model is swappable (the whole point)

The `-m` flag overrides the model for one run; nothing else changes. This is
the "not married to a vendor" claim, verifiable in two commands:

```bash
hermes -m google/gemini-2.5-flash-lite -z "Name your model."   # Google
hermes -m deepseek/deepseek-chat       -z "Name your model."   # DeepSeek
```

To make a swap permanent, edit `model.default` in `config.yaml` (or
`hermes model` if your version exposes the interactive picker).

## What you have now

A functional, local, model-portable Hermes agent. The single human-required
step was the credential — the setup itself is fully scriptable. From here:

- **`setup-composio`** — give the agent reach into Gmail/GitHub/Slack/etc.
- **`setup-agentmail`** — give the agent its own email inbox.
- **`setup-telegram-gateway`** — talk to the agent from your phone, always-on.

## Notes & gotchas

- **`hermes config`** subcommands: `show` (prints merged config — may include
  secret *values*, avoid in shared sessions), `path`, `env-path`, `set`,
  `check`, `migrate`.
- **`hermes config set KEY VALUE`** routes secrets to `.env` automatically but
  echoes the value into shell history — prefer the `read -rs` handoff for real
  keys.
- These tools post-date most training cutoffs; if a flag or path here looks
  wrong against the installed version, trust `hermes --help` and the current
  docs at `hermes-agent.nousresearch.com/docs` over this file.
