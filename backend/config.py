import os

PI_IP = os.environ.get("PI_IP", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "65432"))

BT_ENABLED = os.environ.get("BT_ENABLED", "false").lower() == "true"
BT_MAC = os.environ.get("BT_MAC", "DC:A6:32:80:7D:87")
BT_CHANNEL = int(os.environ.get("BT_CHANNEL", "1"))

CORS_ENABLED = os.environ.get("CORS_ENABLED", "true").lower() == "true"

DEFAULT_POWER = int(os.environ.get("DEFAULT_POWER", "50"))
TURN_POWER = int(os.environ.get("TURN_POWER", "30"))

# auto-stop the car if no command received within this many seconds (0 to disable)
COMMAND_TIMEOUT = float(os.environ.get("COMMAND_TIMEOUT", "0.6"))
