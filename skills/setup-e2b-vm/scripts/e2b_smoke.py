#!/usr/bin/env python3
"""E2B Desktop smoke test: create -> screenshot -> shell -> destroy, with timing.

Proves a sandbox is a real GUI desktop (screenshot returns image bytes) with
working shell access, and reports client-side create/destroy latency. Reads
E2B_API_KEY from the environment — source ~/.hermes/.env before running.

Usage:
  set -a && . ~/.hermes/.env && set +a && python3 e2b_smoke.py
"""
import os
import sys
import time
from pathlib import Path

try:
    from e2b_desktop import Sandbox
    from e2b.sandbox.commands.command_handle import CommandExitException
except ImportError:
    sys.exit("ERROR: e2b-desktop not installed. `pip install e2b-desktop` in your venv.")

OUT = Path(__file__).parent / "e2b_smoke_screenshot.png"


def main():
    if not os.environ.get("E2B_API_KEY"):
        sys.exit("ERROR: E2B_API_KEY not set — source ~/.hermes/.env first.")

    t0 = time.monotonic()
    sb = Sandbox.create(timeout=300)
    create_s = time.monotonic() - t0
    print(f"created: id={sb.sandbox_id}  ({create_s:.3f}s client-side)")

    try:
        img = sb.screenshot()
        OUT.write_bytes(img)
        print(f"screenshot: {OUT.name}  ({len(img)} bytes — real GUI display)")

        try:
            r = sb.commands.run("uname -a")
            print(f"uname: {r.stdout.strip()}")
        except CommandExitException as e:
            print(f"uname failed: exit={e.exit_code} {e.stderr}")

        try:
            r = sb.commands.run(". /etc/os-release && echo $PRETTY_NAME")
            print(f"os: {r.stdout.strip()}")
        except CommandExitException as e:
            print(f"os probe failed: exit={e.exit_code}")
    finally:
        t1 = time.monotonic()
        sb.kill()
        print(f"destroyed: ({time.monotonic() - t1:.3f}s)")


if __name__ == "__main__":
    main()
