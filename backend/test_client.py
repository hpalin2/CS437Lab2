#!/usr/bin/env python3
"""Standalone test client for the Flask backend.

Usage:
    python test_client.py [base_url]

Defaults to http://localhost:65432 if no argument is given.
"""

import sys
import json
import urllib.request
import urllib.error


def _url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


def get(base: str, path: str):
    req = urllib.request.Request(_url(base, path))
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def post(base: str, path: str, body: dict):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        _url(base, path),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:65432"
    print(f"targeting {base}\n")

    print("--- GET /health ---")
    print(json.dumps(get(base, "/health"), indent=2))

    print("\n--- GET /telemetry (initial) ---")
    print(json.dumps(get(base, "/telemetry"), indent=2))

    for cmd in ["forward", "left", "forward", "right", "stop"]:
        print(f"\n--- POST /command  {{'command': '{cmd}'}} ---")
        status, body = post(base, "/command", {"command": cmd})
        print(f"status={status}")
        print(json.dumps(body, indent=2))

    print("\n--- POST /command  (invalid) ---")
    status, body = post(base, "/command", {"command": "fly"})
    print(f"status={status}")
    print(json.dumps(body, indent=2))

    print("\n--- POST /command  (missing field) ---")
    status, body = post(base, "/command", {})
    print(f"status={status}")
    print(json.dumps(body, indent=2))

    print("\n--- GET /telemetry (final) ---")
    print(json.dumps(get(base, "/telemetry"), indent=2))

    print("\nall tests passed")


if __name__ == "__main__":
    main()
