---
description: Setup or cleanup for agent-stack. Default creates user-level symlinks at ~/.claude/skills/ so the seven agent-stack skills are addressable by short name (not just the plugin-namespaced form). Use `--remove` to undo those symlinks (foreign-target-safe). Idempotent — safe to re-run either mode.
---

# agent-stack:init [--remove]

Two modes, dispatched by flag.

| Flag | Mode | What it does |
|------|------|--------------|
| (none) | **Setup** | Symlink the 7 skills into `~/.claude/skills/` for short-form access. |
| `--remove` | **Cleanup** | Remove those symlinks (only if they point at agent-stack). |

Both modes are idempotent. This plugin holds no secrets and touches no
`settings.json` — the only state it creates is skill symlinks, so the lifecycle
is deliberately minimal.

## Step 0 — Parse flag and dispatch

Inspect `$ARGUMENTS`:

| Flag | Section to follow |
|------|-------------------|
| (none) | **Setup mode** below — skip Cleanup. |
| `--remove` | **Cleanup mode** below — skip Setup. |

If both appear, prefer `--remove`.

## Finding plugin-root

Run once at the start (works regardless of marketplace name — rule 6):

```bash
PLUGIN_ROOT=""
for d in ~/.claude/plugins/marketplaces/*/; do
  manifest="$d/.claude-plugin/plugin.json"
  if [ -f "$manifest" ]; then
    name=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('name',''))" "$manifest" 2>/dev/null || \
           grep -E '"name"\s*:\s*"' "$manifest" | head -1 | sed -E 's/.*"name"\s*:\s*"([^"]+)".*/\1/')
    if [ "$name" = "agent-stack" ]; then
      PLUGIN_ROOT="${d%/}"
      break
    fi
  fi
done

# Fallback to a dev clone if not installed via marketplace:
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT="$(ls -d ~/Documents/agent-stack ~/code/agent-stack 2>/dev/null | head -1)"

if [ -z "$PLUGIN_ROOT" ] || [ ! -d "$PLUGIN_ROOT/skills" ]; then
  echo "agent-stack install broken — couldn't locate the plugin's skills/ dir. Aborting." >&2
  exit 1
fi
```

---

# Setup mode (default)

First-run setup. **Does not run any of the agent-setup procedures** — it only
makes the skills addressable by short name. Idempotent — re-running only creates
what's missing.

At the end of a successful run, the user has these symlinks in
`~/.claude/skills/` (each → its dir under `$PLUGIN_ROOT/skills/`):

- `agent-stack-library`
- `setup-hermes-openrouter`
- `setup-composio`
- `setup-agentmail`
- `setup-telegram-gateway`
- `setup-e2b-vm`
- `setup-claude-code-on-e2b`

The library is symlinked too so the setup skills' `../agent-stack-library/...`
relative references resolve when invoked by short name.

## Opening banner

```
/agent-stack:init — first-run setup
Linking 7 skills into ~/.claude/skills/ for short-form access.
Legend: ✓ passed · → fixing · ⚠ needs you · ✗ blocking
```

## Implementation

```bash
mkdir -p ~/.claude/skills
SKILLS="agent-stack-library setup-hermes-openrouter setup-composio setup-agentmail setup-telegram-gateway setup-e2b-vm setup-claude-code-on-e2b"
linked=0; existed=0; conflict=0; i=0; total=7
for s in $SKILLS; do
  i=$((i+1))
  src="$PLUGIN_ROOT/skills/$s"
  dst="$HOME/.claude/skills/$s"
  if [ ! -d "$src" ]; then
    echo "[$i/$total] $s — ✗ blocking (source missing at $src)"
    continue
  fi
  if [ -L "$dst" ]; then
    target=$(readlink "$dst")
    if [ "$target" = "$src" ]; then
      echo "[$i/$total] $s — ✓ passed (already linked)"; existed=$((existed+1))
    else
      echo "[$i/$total] $s — ⚠ needs you (a different symlink exists: $target; not overwriting)"; conflict=$((conflict+1))
    fi
  elif [ -e "$dst" ]; then
    echo "[$i/$total] $s — ⚠ needs you (a real file/dir exists at $dst; not overwriting)"; conflict=$((conflict+1))
  else
    ln -s "$src" "$dst"
    echo "[$i/$total] $s — → fixing → ✓ linked"; linked=$((linked+1))
  fi
done
echo ""
echo "agent-stack:init complete — $linked linked, $existed already present, $conflict need attention."
echo "Invoke a skill by short name (e.g. 'setup-hermes-openrouter') or namespaced (agent-stack:setup-hermes-openrouter)."
```

### Setup safety rules

- Never overwrite a real file/dir or a foreign symlink at a target path — report
  it and move on.
- This plugin needs no `settings.json` entries and no secrets — there is nothing
  to merge or hand off here.

---

# Cleanup mode (`--remove`)

Removes the skill symlinks Setup created. **Never deletes a real directory and
never removes a symlink that points somewhere other than this plugin**
(foreign-target safety, rule 3). Touches nothing else — this plugin stores no
secrets or user data.

## Implementation

```bash
removed=0; foreign=0; not_symlink=0; absent=0
SKILLS="agent-stack-library setup-hermes-openrouter setup-composio setup-agentmail setup-telegram-gateway setup-e2b-vm setup-claude-code-on-e2b"

remove_symlink() {
  local dst="$1"; local label="$2"
  if [ -L "$dst" ]; then
    local target; target=$(readlink "$dst")
    if echo "$target" | grep -q "agent-stack"; then
      rm "$dst"; echo "  ✓ removed: $label"; removed=$((removed+1))
    else
      echo "  ⚠ kept: $label — points elsewhere ($target); not touching"; foreign=$((foreign+1))
    fi
  elif [ -e "$dst" ]; then
    echo "  ⚠ kept: $label — real file/dir, not a symlink; not touching"; not_symlink=$((not_symlink+1))
  else
    absent=$((absent+1))
  fi
}

for s in $SKILLS; do
  remove_symlink "$HOME/.claude/skills/$s" "~/.claude/skills/$s"
done

echo ""
echo "agent-stack:init --remove complete — $removed removed, $absent already absent, $foreign kept (foreign), $not_symlink kept (not a symlink)."
echo ""
echo "Nothing else to clean up — this plugin stores no secrets, settings, or data."
echo ""
echo "To uninstall the plugin itself:"
echo ""
echo "  /plugin uninstall agent-stack@jason-agent-stack"
echo "  /plugin marketplace remove jason-agent-stack"
echo ""
echo "(Skipping those keeps the plugin installed — symlinks can be recreated with /agent-stack:init.)"
```

### Cleanup safety rules

- Only remove symlinks whose target contains `agent-stack` — leave foreign
  symlinks and real files alone.
- Never auto-invoke `/plugin uninstall` — print it for the user (rule 5).
