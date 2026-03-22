"""
Fake PiCar HTTP API for testing the Electron app on a laptop (no Pi, no hardware).

Same routes and JSON shape as server.py: GET /health, GET /telemetry, POST /command.

Run (from repo root or backend/):

  cd backend
  pip install -r requirements.txt
  python dummy_server.py

Defaults: http://127.0.0.1:65432 — matches electron/index.js server_addr.
Override with DUMMY_PI_HOST, FLASK_PORT.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request
from flask_cors import CORS

VALID_COMMANDS = frozenset({"forward", "backward", "left", "right", "stop"})
DEFAULT_POWER = int(os.environ.get("DEFAULT_POWER", "50"))

HOST = os.environ.get("DUMMY_PI_HOST", "127.0.0.1")
PORT = int(os.environ.get("FLASK_PORT", "65432"))

app = Flask(__name__)
CORS(app)

_state = {
    "direction": "stopped",
    "speed": 0,
    "temperature": 48.3,
    "battery_voltage": 7.65,
    "battery_percentage": 68,
}

_polls = 0


def _snapshot() -> dict:
    global _polls
    _polls += 1
    # Tiny drift so telemetry polling is visibly "alive" in the UI
    t = _state["temperature"] + 0.01 * ((_polls % 10) - 5)
    return {
        **_state,
        "temperature": round(t, 1),
    }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/telemetry", methods=["GET"])
def telemetry():
    return jsonify(_snapshot())


@app.route("/command", methods=["POST"])
def command():
    body = request.get_json(silent=True)
    if not body or "command" not in body:
        return jsonify({"status": "error", "message": "missing 'command' field"}), 400

    cmd = str(body["command"]).strip().lower()
    if cmd not in VALID_COMMANDS:
        return jsonify({
            "status": "error",
            "message": f"unknown command: {cmd!r}",
            "valid_commands": sorted(VALID_COMMANDS),
        }), 400

    if cmd == "stop":
        _state["direction"] = "stopped"
        _state["speed"] = 0
    else:
        _state["direction"] = cmd
        _state["speed"] = DEFAULT_POWER

    return jsonify({"status": "ok", "telemetry": _snapshot()})


if __name__ == "__main__":
    print(f"dummy Pi API at http://{HOST}:{PORT} (Ctrl+C to stop)")
    app.run(host=HOST, port=PORT, debug=False)
