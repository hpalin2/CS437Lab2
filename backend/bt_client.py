#!/usr/bin/env python3
"""Simple Bluetooth RFCOMM client for the Pi car backend.

Usage:
    python bt_client.py [pi_mac] [channel]

Defaults to the current Pi controller MAC on channel 1.
"""

import json
import socket
import sys
import time


DEFAULT_PI_MAC = "88:A2:9E:57:1F:88"
DEFAULT_CHANNEL = 1


def send_line(sock: socket.socket, line: str) -> dict:
    sock.sendall((line + "\n").encode("utf-8"))

    buf = ""
    while "\n" not in buf:
        data = sock.recv(4096)
        if not data:
            raise ConnectionError("bluetooth server closed the connection")
        buf += data.decode("utf-8", errors="replace")

    response_line, _rest = buf.split("\n", 1)
    return json.loads(response_line)


def main():
    pi_mac = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PI_MAC
    channel = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CHANNEL

    print(f"connecting to {pi_mac} on channel {channel}")
    sock = socket.socket(
        socket.AF_BLUETOOTH,
        socket.SOCK_STREAM,
        socket.BTPROTO_RFCOMM,
    )

    try:
        sock.connect((pi_mac, channel))

        print("\n--- telemetry ---")
        print(json.dumps(send_line(sock, "telemetry"), indent=2))

        for cmd in ["forward", "backward", "stop"]:
            print(f"\n--- {cmd} ---")
            print(json.dumps(send_line(sock, cmd), indent=2))
            time.sleep(1.0)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
