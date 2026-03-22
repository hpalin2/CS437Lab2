# CS437 Lab 2 -- Backend

Flask REST backend that runs on the Raspberry Pi. It drives the PiCar-X motors in real time, reads battery voltage from the ADC, and reports CPU temperature -- all exposed as a REST API over Wi-Fi. An optional Bluetooth RFCOMM service can run alongside Flask for extra credit.

On a Raspberry Pi with `picar-x` and `robot_hat` installed, commands move the real car and battery readings come from the hardware ADC. On any other machine, it falls back to mock hardware automatically.

## Quick start

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

The server binds to `0.0.0.0:65432` by default. Override with environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PI_IP` | `0.0.0.0` | Interface to bind to |
| `FLASK_PORT` | `65432` | HTTP port |
| `DEFAULT_POWER` | `50` | Motor power for forward/backward (0-100) |
| `TURN_POWER` | `30` | Motor power during turns (0-100) |
| `CORS_ENABLED` | `true` | Allow cross-origin requests |
| `BT_ENABLED` | `false` | Start Bluetooth RFCOMM listener on boot |
| `BT_MAC` | `DC:A6:32:80:7D:87` | Pi Bluetooth adapter MAC |
| `BT_CHANNEL` | `1` | RFCOMM channel |

Example with overrides:

```bash
PI_IP=192.168.0.209 DEFAULT_POWER=40 python server.py
```

## API reference

All responses are JSON. The `Content-Type` for POST bodies must be `application/json`.

### `GET /health`

Connectivity check.

```
Response: {"status": "ok"}
```

### `GET /telemetry`

Returns the current car state with 5 data points.

```json
{
  "direction": "forward",
  "speed": 50,
  "temperature": 55.6,
  "battery_voltage": 8.15,
  "battery_percentage": 89
}
```

| Field | Type | Description |
|-------|------|-------------|
| `direction` | string | Current heading: `forward`, `backward`, `left`, `right`, or `stopped` |
| `speed` | int | Motor power level (0 when stopped, `DEFAULT_POWER` when moving) |
| `temperature` | float | Pi CPU temperature in celsius (real sysfs reading, 0.0 on non-Pi) |
| `battery_voltage` | float | Real battery voltage from ADC (2-cell Li-ion, ~6.0V empty to ~8.4V full) |
| `battery_percentage` | int | Estimated charge level 0-100 derived from voltage |

### `POST /command`

Send a driving command to the car. On the Pi this moves real motors.

**Request body:**

```json
{"command": "forward"}
```

Valid commands: `forward`, `backward`, `left`, `right`, `stop`

**Success response (200):**

```json
{
  "status": "ok",
  "telemetry": {
    "direction": "forward",
    "speed": 50,
    "temperature": 55.6,
    "battery_voltage": 8.15,
    "battery_percentage": 89
  }
}
```

**Error -- invalid command (400):**

```json
{
  "status": "error",
  "message": "unknown command: 'fly'",
  "valid_commands": ["backward", "forward", "left", "right", "stop"]
}
```

**Error -- missing field (400):**

```json
{
  "status": "error",
  "message": "missing 'command' field"
}
```

## Frontend integration

The Electron app (or any HTTP client) can consume the API with standard `fetch()`. No Node.js-specific modules or `nodeIntegration` required.

```javascript
const PI = "http://192.168.0.209:65432";

// send a command
async function sendCommand(cmd) {
  const res = await fetch(`${PI}/command`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({command: cmd})
  });
  return res.json();
}

// poll telemetry
async function getTelemetry() {
  const res = await fetch(`${PI}/telemetry`);
  return res.json();
}

// example: poll every 500ms
setInterval(async () => {
  const data = await getTelemetry();
  document.getElementById("speed").textContent = data.speed;
  document.getElementById("temperature").textContent = data.temperature;
  document.getElementById("battery").textContent = data.battery_percentage + "%";
}, 500);
```

## Testing

A zero-dependency test client is included. Start the server in one terminal, then run:

```bash
source venv/bin/activate
python test_client.py
```

**Warning:** on a real Pi this will physically move the car. Make sure it is on a flat surface or elevated.

It exercises every endpoint (health, telemetry, valid commands, invalid command, missing field) and prints the results. You can also point it at a remote Pi:

```bash
python test_client.py http://192.168.0.209:65432
```

Manual testing with curl:

```bash
# health check
curl http://localhost:65432/health

# get telemetry
curl http://localhost:65432/telemetry

# send a command (this WILL move the car on Pi)
curl -X POST http://localhost:65432/command \
  -H "Content-Type: application/json" \
  -d '{"command": "forward"}'

# stop the car
curl -X POST http://localhost:65432/command \
  -H "Content-Type: application/json" \
  -d '{"command": "stop"}'
```

## Bluetooth (extra credit)

The Bluetooth service uses Python's built-in `socket.AF_BLUETOOTH` (Python 3.9+, Linux only) -- no pip packages needed. It runs as a background thread alongside Flask, sharing the same `CarController` and hardware. Commands from either interface drive the same motors.

### 1. Pair the devices

Before anything can connect, the Pi and client must be paired at the OS level. On the Pi:

```bash
bluetoothctl
# inside bluetoothctl:
power on
discoverable on
pairable on
# on the client device, scan and select the Pi
# back in bluetoothctl, confirm the pairing when prompted:
yes
quit
```

### 2. Find the Pi's Bluetooth MAC

```bash
hciconfig | grep "BD Address"
# example output: BD Address: DC:A6:32:80:7D:87
```

### 3. Start the server with Bluetooth enabled

```bash
source venv/bin/activate
BT_ENABLED=true BT_MAC=DC:A6:32:80:7D:87 python server.py
```

You should see `bluetooth service started on channel 1` in the output alongside the Flask startup.

### 4. Connect a client

The RFCOMM protocol is line-based: send a command string followed by `\n`, receive a JSON response followed by `\n`.

```
Client sends:  forward\n
Server returns: {"status": "ok", "telemetry": {"direction": "forward", ...}}\n
```

Here is a minimal Python client (runs on a paired PC or another Pi):

```python
import socket
import json

PI_MAC = "DC:A6:32:80:7D:87"  # your Pi's Bluetooth MAC
CHANNEL = 1

sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
sock.connect((PI_MAC, CHANNEL))

# send a command
sock.sendall(b"forward\n")

# read the JSON response (terminated by newline)
buf = b""
while b"\n" not in buf:
    buf += sock.recv(1024)
response = json.loads(buf.decode())
print(response)

sock.sendall(b"stop\n")
buf = b""
while b"\n" not in buf:
    buf += sock.recv(1024)
print(json.loads(buf.decode()))

sock.close()
```

The same valid commands work over Bluetooth as over HTTP: `forward`, `backward`, `left`, `right`, `stop`. The watchdog auto-stop also applies -- if the client stops sending commands, the car halts after the timeout.

## Project structure

```
backend/
  config.py              -- env-var-driven configuration
  server.py              -- flask app entry point
  car_controller.py      -- shared car state, hardware dispatch, telemetry
  hardware.py            -- PiCar-X hardware abstraction (real on Pi, mock on PC)
  bluetooth_service.py   -- optional threaded RFCOMM listener
  test_client.py         -- standalone endpoint exerciser
  requirements.txt       -- pip dependencies
  venv/                  -- virtual environment (not committed)
```

## Hardware dependencies

On the Raspberry Pi, the backend uses these libraries (installed from local source in Lab 1):

- `picar-x` (2.1.0a1) -- motor control, steering servo, ultrasonic sensor
- `robot_hat` (2.5.1) -- low-level I2C/ADC/GPIO/PWM, battery voltage reading

These are expected to already be installed system-wide from Lab 1. The venv will find them via the system path fallback in `hardware.py`. If they are not available, the backend falls back to mock hardware with print-based output.
