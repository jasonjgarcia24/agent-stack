#!/usr/bin/env python3
"""List or kill E2B sandboxes — the cleanup safety net.

A crashed script can orphan a running sandbox that keeps billing. Run this
after any session (especially a failed one) to see what's live and kill it.
Correctly pages through SandboxPaginator (which is NOT iterable and has no
len()). Reads E2B_API_KEY from the environment.

Usage:
  set -a && . ~/.hermes/.env && set +a && python3 e2b_list_kill.py --list
  set -a && . ~/.hermes/.env && set +a && python3 e2b_list_kill.py --kill-all
"""
import argparse
import os
import sys

try:
    from e2b_desktop import Sandbox
except ImportError:
    sys.exit("ERROR: e2b-desktop not installed. `pip install e2b-desktop` in your venv.")


def iter_live():
    """Yield live sandbox handles, paging through the SandboxPaginator."""
    p = Sandbox.list()
    while True:
        items = p.next_items()
        if not items:
            break
        for sb in items:
            yield sb
        if not p.has_next:
            break


def main():
    ap = argparse.ArgumentParser(description="List or kill E2B sandboxes.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="list live sandboxes")
    g.add_argument("--kill-all", action="store_true", help="kill every live sandbox")
    args = ap.parse_args()

    if not os.environ.get("E2B_API_KEY"):
        sys.exit("ERROR: E2B_API_KEY not set — source ~/.hermes/.env first.")

    killed = 0
    count = 0
    for sb in iter_live():
        count += 1
        sid = getattr(sb, "sandbox_id", None) or getattr(sb, "id", None)
        state = getattr(sb, "state", "?")
        print(f"live: {sid}  state={state}")
        if args.kill_all and sid:
            try:
                Sandbox.connect(sid).kill()
                killed += 1
            except Exception as e:  # noqa: BLE001 — best-effort cleanup
                print(f"  kill failed: {e!r}")

    if args.kill_all:
        print(f"killed {killed} of {count} live sandbox(es).")
    else:
        print(f"{count} live sandbox(es).")


if __name__ == "__main__":
    main()
