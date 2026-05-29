---
name: agent-stack-library
description: Shared reference library for the agent-stack plugin's setup skills. Not invoked directly — the setup-* skills read from its references/ for the secret-handoff pattern, the ~/.hermes/.env conventions, and cross-cutting troubleshooting (UTF-8 locale, TERM, PATH, E2B SDK gotchas). Read a specific file under references/ when a setup skill points you here.
---

# Agent Stack — Library

This is the **library skill** for the `agent-stack` plugin: a single source of
truth for material shared across the six `setup-*` skills. It is not a runbook
on its own. The setup skills reference its files by relative path
(`../agent-stack-library/references/<file>.md`).

Why a library skill instead of duplicating: the secret-handoff pattern, the
`~/.hermes/.env` conventions, and the cross-cutting troubleshooting notes are
consumed by 3+ skills that always ship together in this one plugin. One
canonical copy, no drift.

## What's here

| Reference | Read it when |
|---|---|
| `references/secrets-handling.md` | Any time a skill needs the user to hand off an API key or token — the no-echo `read -rs` pattern and the "never render a secret" rule. |
| `references/env-conventions.md` | Working with `~/.hermes/.env` and `~/.hermes/config.yaml` — what lives where, canonical key names, how Hermes interpolates env vars. |
| `references/troubleshooting.md` | A TUI renders garbled glyphs, a command isn't found in the VM, the E2B SDK throws, or a sandbox won't stay alive. The UTF-8-locale fix lives here. |

## Provenance

Every procedure in this plugin was verified first-hand in the `agent-dev`
project (experiments E-002 through E-009, May 2026), then distilled here. These
tools post-date most models' training cutoffs — when a detail looks stale,
re-ground it against the vendor's current docs before trusting it.
