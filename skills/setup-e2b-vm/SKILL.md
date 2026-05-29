---
name: setup-e2b-vm
description: Spin up cloud-desktop VMs for agents on E2B — full Linux GUI sandboxes an agent can see and control (screenshot, mouse, keyboard, shell), create/destroy in ~1s, drive many from one operator process. Use this whenever the user wants a cloud VM/desktop for an agent, "set up E2B," a sandbox to run an agent in, a remote computer the agent controls, multi-VM orchestration, or a cheap ephemeral environment for agent work. Covers signup/$100 credit, the SDK install, a bundled create→screenshot→shell→destroy smoke test, the live noVNC stream URL, multi-VM control via the paginator, the real (not marketing) latency numbers, and a bundled list-and-kill cleanup so you never leak a running sandbox.
---

# Set up E2B cloud-desktop VMs

E2B Desktop gives an agent a full Linux GUI sandbox — not a headless VPS. The
agent can screenshot it, click, type, and run shell commands. Sandboxes create
in about a second and destroy in tens of milliseconds, and one operator process
can drive many at once. This is the "give the agent a computer" layer, and a
clean substrate for agent-driven remote installs.

> Read `../agent-stack-library/references/secrets-handling.md` (key handoff) and
> `../agent-stack-library/references/troubleshooting.md` (the E2B SDK gotchas —
> the paginator and exception behavior bite everyone once).

## Prerequisites

- An **E2B account** (`e2b.dev`). The Hobby tier gives a **$100 one-time
  credit**, 20 concurrent sandboxes, 1-hour session cap, **no credit card**.
  This experiment-scale work costs cents against that credit.
- An **E2B_API_KEY** from the dashboard.
- Python 3 + a venv on the host you drive from.

## Step 1 — Hand off the key + install the SDK

```bash
read -rs E2B_API_KEY && \
  printf 'E2B_API_KEY=%s\n' "$E2B_API_KEY" >> ~/.hermes/.env && \
  unset E2B_API_KEY

python3 -m venv ~/e2b-venv
~/e2b-venv/bin/pip install e2b-desktop
```

## Step 2 — Smoke test: create → screenshot → shell → destroy

This skill ships `scripts/e2b_smoke.py`, which proves the sandbox is a real GUI
desktop with shell access and prints create/destroy timing. Run it sourcing the
key (never echo it):

```bash
set -a && . ~/.hermes/.env && set +a && \
  ~/e2b-venv/bin/python scripts/e2b_smoke.py ; \
  unset E2B_API_KEY
```

Expect: a sandbox ID, a multi-KB PNG written locally (real X11 display — a
headless box would not produce one), `uname -a` output, and the OS pretty-name
(Ubuntu 22.04). The script destroys the sandbox before exiting.

## Step 3 — Watch it live (noVNC)

For a demo, start the stream on a freshly-created sandbox and open the viewer:

```python
from e2b_desktop import Sandbox
sb = Sandbox.create(timeout=1800)
sb.stream.start(require_auth=False)
print(sb.stream.get_url())   # https://6080-<id>.e2b.app/vnc.html?autoconnect=true&resize=scale
```

Open that URL in a browser — mouse/keyboard work in noVNC.

> **Security caveat:** `require_auth=False` makes that URL an **unauthenticated,
> control-capable** surface — anyone with the link gets full mouse/keyboard
> control of the sandbox (which can run shell commands, and in the
> Claude-Code-on-E2B flow may hold an `ANTHROPIC_API_KEY`). The sandbox ID is
> the only thing protecting it. Fine for a throwaway local demo; for anything
> beyond that use `require_auth=True` and treat the URL as a secret.

**Gotcha:** the stream handle attaches on `create()`, not on `connect()`; if you
reconnect to an existing sandbox the `sb.stream` object won't be live (the URL
pattern still works if the stream was already started).

## Step 4 — Drive multiple VMs from one operator process

The "one operator → many customer VMs" pattern: create several sandboxes and
command them from a single process. `scripts/e2b_list_kill.py --list` shows all
live sandboxes via the paginator (which is **not** a plain iterable — see
troubleshooting). Concurrency with `ThreadPoolExecutor` lets you fan out:
spawning 3 sandboxes + commanding each runs in ~1.3s wall, not 3× sequential.

## Step 5 — ALWAYS clean up (the meter runs until you kill it)

A crashed script can orphan a running sandbox that keeps billing. After any
session — especially a failed one — list and kill everything:

```bash
set -a && . ~/.hermes/.env && set +a && \
  ~/e2b-venv/bin/python scripts/e2b_list_kill.py --kill-all ; \
  unset E2B_API_KEY
```

It prints each live sandbox then kills them; a final `--list` should show zero.

## The latency reality (don't repeat the marketing line)

Vendors quote "sub-500ms boot," but that's **server-side**. Measured
**client-side** through the SDK (what you actually experience):

| Operation | Median | Note |
|---|---|---|
| create | ~1.25s | network + SDK overhead on top of server boot |
| destroy | ~38ms | genuinely sub-second |
| create+destroy combined | ~1.3s | fast, but **not** "under a second" |

So "deletable/recreatable in seconds" is true and useful (orders of magnitude
faster than spinning a classic VM); "under a second" doesn't survive
client-side measurement. State it honestly.

## Notes & gotchas (full list in troubleshooting.md)

- `Sandbox.list()` → a `SandboxPaginator`: not iterable, no `len()`; use
  `.next_items()` / `.has_next`.
- `commands.run()` raises `CommandExitException` on non-zero exit — catch it to
  capture failures instead of crashing.
- Default sandbox timeout is short; pass `Sandbox.create(timeout=1800)` for
  installs, `timeout=0` on a `commands.run` for a long step.
- Default user is `user` (home `/home/user`); `/root` isn't writable. Install
  into the user's home.
- Post-cutoff tool: confirm SDK method names against `e2b.dev/docs` if anything
  here drifts.

## Next

`setup-claude-code-on-e2b` — provision Claude Code *inside* one of these VMs
(and the locale fix that makes its TUI render correctly).
