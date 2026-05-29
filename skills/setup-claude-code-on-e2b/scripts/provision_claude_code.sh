#!/usr/bin/env bash
# Provision Claude Code inside an E2B Desktop sandbox, with the three fixes that
# make its TUI render and resolve correctly:
#   1. Node via nvm (none preinstalled)
#   2. PATH set unconditionally in ~/.bash_profile (bashrc's non-interactive
#      guard otherwise hides nvm from login shells -> "command not found")
#   3. UTF-8 locale + TERM (unset locale => garbled box-drawing glyphs that look
#      like a font bug but are not)
#
# Idempotent. Run inside the sandbox (e.g. via the E2B SDK's commands.run, or
# pasted into the sandbox terminal). Does NOT need sudo.
set -euo pipefail

echo "==> 1/4 installing nvm + Node LTS"
if [ ! -s "$HOME/.nvm/nvm.sh" ]; then
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi
export NVM_DIR="$HOME/.nvm"
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh"
nvm install --lts >/dev/null
node --version

echo "==> 2/4 installing Claude Code (npm global)"
npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 || npm install -g @anthropic-ai/claude-code

echo "==> 3/4 writing ~/.bash_profile (PATH unconditional + locale + TERM)"
NODE_BIN="$(ls -d "$HOME"/.nvm/versions/node/*/bin 2>/dev/null | head -1)"
cat > "$HOME/.bash_profile" <<EOF
# Put Node + npm-global bins on PATH for ALL shells (interactive or not).
# ~/.bashrc returns early for non-interactive shells, so nvm's own PATH setup
# never runs under 'bash -lc' / launched terminals -> "command not found".
export PATH="$NODE_BIN:\$HOME/.npm-global/bin:\$PATH"

# UTF-8 locale is REQUIRED for box-drawing/Unicode in TUIs to render. Without
# it, LC_CTYPE=POSIX makes the terminal mangle every multi-byte char into the
# same glyph (the "garbled diamonds" that look like a font bug but are not).
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# Avoid TERM=dumb, which makes ANSI escape codes print literally.
export TERM=xterm-256color

# Source interactive config for everything else.
[ -f ~/.bashrc ] && . ~/.bashrc
EOF

echo "==> 4/4 verifying claude resolves under a login shell"
# shellcheck disable=SC1090
bash -lc 'which claude && claude --version'

echo "==> done. Launch with: xfce4-terminal --command=\"bash -lic 'claude'\""
echo "    then authenticate in the VNC window with /login (or set ANTHROPIC_API_KEY)."
