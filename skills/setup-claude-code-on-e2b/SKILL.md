---
name: setup-claude-code-on-e2b
description: Install and run Claude Code inside an E2B Desktop VM, with the environment fixes that make its terminal UI render correctly. Use this whenever the user wants Claude Code (or any rich TUI) running in an E2B sandbox, "set up Claude Code on the VM," a coding agent inside a cloud desktop, or is debugging garbled/box-drawing glyphs, "command not found" after an nvm install, or dumped escape codes in a sandbox terminal. Covers installing Node via nvm + the Claude Code npm package, the bash_profile PATH fix, and — the headline — the UTF-8 locale fix that resolves the garbled-glyph rendering everyone mistakes for a font problem. Ships a one-shot provisioning script.
---

# Set up Claude Code on an E2B VM

This provisions Claude Code inside an E2B Desktop sandbox and — more
importantly — fixes the three environment problems that make a freshly-spawned
sandbox a hostile place for a rich terminal UI. The big one is a **locale**
issue that masquerades as a font problem and will eat your afternoon if you
chase fonts. Read the headline section before you start clicking.

> Requires a working E2B setup (`setup-e2b-vm`). The cross-cutting fixes here
> are documented once in `../agent-stack-library/references/troubleshooting.md`
> — this skill is the applied, Claude-Code-specific runbook.

## The headline: garbled glyphs are a LOCALE bug, not a font bug

**Symptom:** Claude Code's banner/borders/prompt arrows render as rows of
identical wrong glyphs (diamonds, orange dots, `◆◆`). It looks exactly like a
missing font.

**It is the locale.** A fresh E2B sandbox ships `LANG=` (unset) and
`LC_CTYPE=POSIX`. With a non-UTF-8 ctype, the terminal reads each byte of a
multi-byte UTF-8 character separately. Every box-drawing / geometric codepoint
(`U+2500`–`U+25FF`) starts with byte `0xE2` in UTF-8, so they **all collapse to
the same glyph** — the uniform garbage you see.

**Do not install fonts to fix this.** Chasing FiraCode → Nerd Font → Symbola +
`fc-cache` rebuilds will all fail, because the bytes never reach the font layer
as valid codepoints. The stock `DejaVu Sans Mono` already has the glyphs. Fix
the locale and it renders immediately.

The provisioning script below sets `LANG=C.UTF-8` / `LC_ALL=C.UTF-8` for you;
this section exists so you recognize the symptom and don't go down the font
hole when you see it elsewhere.

## One-shot provision (recommended)

`scripts/provision_claude_code.sh` does the whole install + all three fixes
inside a target sandbox. It's designed to be run *via the E2B SDK's
`commands.run`* against a long-lived sandbox, or pasted into the sandbox's own
terminal. It is idempotent.

What it does, in order:
1. Install **nvm**, then Node LTS (`nvm install --lts`).
2. `npm install -g @anthropic-ai/claude-code`.
3. Write `~/.bash_profile` that puts Node + npm-global bins on PATH
   **unconditionally**, and exports `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`,
   `TERM=xterm-256color`, then sources `~/.bashrc`.
4. Print the resolved `claude --version`.

Drive it from the host (long-lived sandbox so the install has time):

```python
from e2b_desktop import Sandbox
sb = Sandbox.create(timeout=1800)
script = open("scripts/provision_claude_code.sh").read()
sb.commands.run(f"cat > /tmp/prov.sh <<'PROV'\n{script}\nPROV")
r = sb.commands.run("bash /tmp/prov.sh", timeout=600)
print(r.stdout)   # ends with: claude X.Y.Z (Claude Code)
```

## Why each fix is needed (so you can debug variants)

### 1. Node isn't preinstalled → nvm

E2B Desktop has Python but no Node. Install via **nvm** (user-space, no sudo):
`curl … nvm/install.sh | bash` then `nvm install --lts`.

### 2. "command not found" in launched terminals → bash_profile PATH

After an nvm install, `which claude` works in *your* shell but a launched
terminal or `bash -lc 'claude'` says "command not found." Cause: Ubuntu's
`~/.bashrc` has an early-return guard for non-interactive shells, and nvm's PATH
setup lives below it. Fix: export the Node bin path **unconditionally** in
`~/.bash_profile` (login shells read it), not only in interactive `~/.bashrc`.

### 3. Dumped escape codes → TERM

If escape sequences print literally (`^[[0m`), `TERM` is `dumb`. Set
`TERM=xterm-256color`. (Distinct from the locale bug — that's garbled glyphs;
this is visible escape codes.)

## Launch Claude Code in the VM

Open a terminal as a **login + interactive** shell so it sources
`~/.bash_profile` (PATH + locale + TERM), and start Claude:

```bash
# from the host, against the sandbox:
DISPLAY=:0 TERM=xterm-256color xfce4-terminal --geometry=140x42 \
  --command="bash -lic 'claude'" &
```

Then in that terminal, authenticate: run `/login` (interactive, in the VNC
window) or set `ANTHROPIC_API_KEY` in the sandbox before launching. Verify the
UI: the trust prompt should show a clean `❯` arrow and a `·` separator, not
`◆◆`.

## Verify

```bash
# resolves under a login shell (proves the PATH fix):
bash -lc 'which claude && claude --version'    # -> /home/user/.nvm/.../claude  +  X.Y.Z (Claude Code)

# locale is UTF-8 (proves the glyph fix):
bash -lc 'echo $LANG $LC_ALL'                  # -> C.UTF-8 C.UTF-8
```

## Notes & gotchas

- `C.UTF-8` is usually the only UTF-8 locale available on the minimal sandbox
  (`locale -a | grep -i utf` to confirm); that's fine — it covers the glyphs.
- Sandboxes are ephemeral: this provisioning lives only for that sandbox's
  lifetime. For a reusable setup, bake it into a custom E2B template, or re-run
  the script on each fresh sandbox.
- Don't forget cleanup (`setup-e2b-vm` → `e2b_list_kill.py --kill-all`) — Claude
  Code running in a forgotten sandbox still bills.
