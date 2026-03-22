from flask import Flask, jsonify, request

import config
from car_controller import CarController, VALID_COMMANDS

app = Flask(__name__)

if config.CORS_ENABLED:
    from flask_cors import CORS
    CORS(app)

car = CarController()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/telemetry", methods=["GET"])
def telemetry():
    return jsonify(car.get_telemetry())


@app.route("/command", methods=["POST"])
def command():
    body = request.get_json(silent=True)
    if not body or "command" not in body:
        return jsonify({"status": "error", "message": "missing 'command' field"}), 400

    cmd = body["command"]
    if cmd not in VALID_COMMANDS:
        return jsonify({
            "status": "error",
            "message": f"unknown command: {cmd!r}",
            "valid_commands": sorted(VALID_COMMANDS),
        }), 400

    telemetry_snapshot = car.execute_command(cmd)
    return jsonify({"status": "ok", "telemetry": telemetry_snapshot})


def start(bluetooth=False):
    """Start the Flask server and optionally the Bluetooth service."""
    if bluetooth or config.BT_ENABLED:
        try:
            from bluetooth_service import BluetoothService
            bt = BluetoothService(car)
            bt.start()
            print(f"bluetooth service started on channel {config.BT_CHANNEL}")
        except ImportError:
            print("pybluez not installed -- skipping bluetooth service")
        except Exception as e:
            print(f"bluetooth service failed to start: {e}")

    print(f"starting flask on {config.PI_IP}:{config.FLASK_PORT}")
    app.run(host=config.PI_IP, port=config.FLASK_PORT)


if __name__ == "__main__":
    start()
