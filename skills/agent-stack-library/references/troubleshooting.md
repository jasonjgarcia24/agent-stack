# Cross-cutting troubleshooting

Hard-won fixes that span more than one setup skill. Each was hit first-hand
during agent-dev setup.

## TUI renders garbled glyphs (the locale trap) — HIGH VALUE

**Symptom:** A terminal UI (Claude Code, Hermes TUI, anything with box-drawing
borders) shows rows of identical wrong glyphs — diamonds, orange dots, `◆◆`
where arrows/borders should be. Looks like a font problem. **It is almost never
the font.**

**Root cause:** The shell's locale is unset or POSIX/C (not UTF-8). Check:

```bash
locale          # LANG= and LC_CTYPE="POSIX"  => broken
```

With a non-UTF-8 `LC_CTYPE`, the terminal reads each byte of a multi-byte UTF-8
sequence separately. Every box-drawing / geometric-shape codepoint
(`U+2500`–`U+25FF`) and many symbols begin with byte `0xE2` in UTF-8, so they
**all collapse to the same single glyph** — hence the uniform garbage.

**Fix:** set a UTF-8 locale. On a minimal cloud VM, `C.UTF-8` is usually the
only one available (`locale -a | grep -i utf`). Put it where login shells see
it:

```bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
```

Persist in `~/.bash_profile` (see the PATH note below for why bash_profile, not
just bashrc), then open a fresh terminal.

**Do not** go down the font rabbit hole first. Installing FiraCode, Nerd Fonts,
Powerline, Symbola, and rebuilding the fontconfig cache will all *fail to fix
this* because the bytes never reach the font layer as valid codepoints. Fix the
locale; the stock `DejaVu Sans Mono` already covers the glyphs.

## `TERM=dumb` — escape codes printed literally

**Symptom:** ANSI escape sequences show up as literal text (`^[[0m`, stray
bracket-codes) instead of being interpreted as color/cursor moves.

**Cause:** `TERM` is unset or `dumb` (common default when a process spawns a
shell non-interactively, e.g. via an SDK `commands.run`).

**Fix:**

```bash
export TERM=xterm-256color
```

Persist alongside the locale settings.

## Command installed but "command not found" in a login shell

**Symptom:** You installed something via `nvm`/user-prefix `npm` (or similar),
`which X` works in your interactive shell, but `bash -lc 'X'` or a launched
terminal reports "command not found."

**Cause:** Ubuntu's default `~/.bashrc` has an early-return guard for
non-interactive shells (`case $- in *i*) ;; *) return;; esac`). nvm's PATH
setup lives **below** that guard, so non-interactive/login invocations never
get it.

**Fix:** put the bin directory on PATH **unconditionally** in `~/.bash_profile`
(which login shells read), not only in the interactive part of `~/.bashrc`:

```bash
NODE_BIN=$(ls -d ~/.nvm/versions/node/*/bin 2>/dev/null | head -1)
cat > ~/.bash_profile <<EOF
export PATH="$NODE_BIN:\$HOME/.npm-global/bin:\$PATH"
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color
[ -f ~/.bashrc ] && . ~/.bashrc
EOF
```

Launch terminals as a login+interactive shell so this is sourced:
`xfce4-terminal --command="bash -lic 'your-cmd'"`.

## E2B SDK gotchas

- **`Sandbox.list()` returns a `SandboxPaginator`** — it is NOT iterable and has
  no `len()`. Page through it:
  ```python
  p = Sandbox.list()
  while True:
      items = p.next_items()
      if not items:
          break
      for sb in items:
          sid = getattr(sb, "sandbox_id", None)
          # ... use sid (Sandbox.connect(sid)) ...
      if not p.has_next:
          break
  ```
- **`commands.run()` raises `CommandExitException` on any non-zero exit.** Wrap
  it if you want to capture failures instead of crashing:
  ```python
  from e2b.sandbox.commands.command_handle import CommandExitException
  try:
      r = sb.commands.run(cmd)
  except CommandExitException as e:
      rc, out, err = e.exit_code, e.stdout, e.stderr
  ```
- **Default sandbox timeout is short.** For installs or long sessions pass
  `Sandbox.create(timeout=1800)` (30 min). Pass `timeout=0` on a `commands.run`
  to disable that call's deadline for a long-running step.
- **The live-stream handle attaches on `create()`, not `connect()`.** If you
  `Sandbox.connect(id)` to an existing sandbox, `sb.stream` won't be live — but
  the viewer URL pattern `https://6080-<sandbox_id>.e2b.app/vnc.html` still
  works if the stream was started on the original `create()`.
- **A crashed script can orphan a running sandbox** (the meter keeps running).
  After any failure, run the list-and-kill cleanup (see
  `setup-e2b-vm/scripts/e2b_list_kill.py`).

## Sandbox runs as non-root `user`

The default E2B Desktop user is `user`, home `/home/user`; `/root` is not
writable. Install everything into the user's home (nvm, uv, pip `--user`,
user-prefix npm). `sudo` is available (passwordless) for `apt` if you genuinely
need a system package.
