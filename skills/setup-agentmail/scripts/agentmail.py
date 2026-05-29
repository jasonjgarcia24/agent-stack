#!/usr/bin/env python3
"""Dependency-free AgentMail client (stdlib urllib only).

Sends a message from an AgentMail inbox and lists messages in an inbox.
Reads the API key from the AGENTMAIL_API_KEY environment variable — source
~/.hermes/.env before running; the key is never accepted as a CLI argument
(so it can't leak into shell history).

Usage:
  AGENTMAIL_API_KEY=... python3 agentmail.py send \
      --inbox you-1234@agentmail.to --to dest@example.com \
      --subject "Hi" --text "body"

  AGENTMAIL_API_KEY=... python3 agentmail.py list --inbox you-1234@agentmail.to

Endpoints follow AgentMail's v0 REST shape as of 2026-05; if a call 4xxs,
re-check the current paths at docs.agentmail.to and adjust API_BASE / routes.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.agentmail.to/v0"


def _key():
    k = os.environ.get("AGENTMAIL_API_KEY")
    if not k:
        sys.exit("ERROR: AGENTMAIL_API_KEY not set — source ~/.hermes/.env first.")
    return k


def _request(method, path, payload=None):
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_key()}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        # Print status + body for debugging, but never echo the key.
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:500]}")
    except urllib.error.URLError as e:
        sys.exit(f"network error: {e.reason}")


def cmd_send(args):
    status, body = _request(
        "POST",
        f"/inboxes/{args.inbox}/messages/send",
        {"to": [args.to], "subject": args.subject, "text": args.text},
    )
    mid = body.get("message_id") or body.get("id") or "<no id in response>"
    print(f"sent: HTTP {status}  message_id={mid}")


def cmd_list(args):
    status, body = _request("GET", f"/inboxes/{args.inbox}/messages")
    msgs = body.get("messages") or body.get("data") or (body if isinstance(body, list) else [])
    print(f"inbox {args.inbox}: HTTP {status}  count={len(msgs)}")
    for m in msgs[: args.limit]:
        subj = (m.get("subject") if isinstance(m, dict) else None) or "<no subject>"
        frm = (m.get("from") if isinstance(m, dict) else None) or "<unknown>"
        print(f"  - from={frm!s:40.40}  subject={subj}")


def main():
    p = argparse.ArgumentParser(description="Minimal AgentMail client (stdlib only).")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("send", help="send a message from an inbox")
    s.add_argument("--inbox", required=True, help="sender inbox address")
    s.add_argument("--to", required=True, help="recipient address")
    s.add_argument("--subject", required=True)
    s.add_argument("--text", required=True)
    s.set_defaults(func=cmd_send)

    l = sub.add_parser("list", help="list messages in an inbox")
    l.add_argument("--inbox", required=True)
    l.add_argument("--limit", type=int, default=10)
    l.set_defaults(func=cmd_list)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
