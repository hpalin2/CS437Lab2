import threading
import collections

import config
from hardware import get_hardware

VALID_COMMANDS = {"forward", "backward", "left", "right", "stop"}

# 2-cell li-ion voltage thresholds
_V_FULL = 8.4
_V_EMPTY = 6.0


_VOLTAGE_WINDOW = 10
_voltage_samples: collections.deque = collections.deque(maxlen=_VOLTAGE_WINDOW)


def _read_battery_voltage() -> float:
    """Read real battery voltage from the robot_hat ADC, smoothed over a
    rolling window to reduce fluctuation from motor load and ADC noise.

    Returns 0.0 on non-Pi systems or if robot_hat is unavailable.
    """
    try:
        from robot_hat import utils
        raw = utils.get_battery_voltage()
        if raw > 0.0:
            _voltage_samples.append(raw)
        if _voltage_samples:
            return round(sum(_voltage_samples) / len(_voltage_samples), 2)
        return 0.0
    except Exception:
        return 0.0

def _voltage_to_percentage(voltage: float) -> int:
    if voltage >= _V_FULL:
        return 100
    if voltage <= _V_EMPTY:
        return 0
    return int(((voltage - _V_EMPTY) / (_V_FULL - _V_EMPTY)) * 100)


class CarController:
    """Shared car state accessed by both Flask routes and the Bluetooth service.

    All public methods are thread-safe. On a Raspberry Pi the commands drive
    real PiCar-X motors; on other systems they fall back to mock prints.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._hw = get_hardware()
        self._direction = "stopped"
        self._watchdog: threading.Timer | None = None
        print(f"hardware backend: {self._hw['hardware_type']}")

    def execute_command(self, cmd: str) -> dict:
        """Apply a driving command and return the updated telemetry snapshot."""
        cmd = cmd.strip().lower()
        if cmd not in VALID_COMMANDS:
            raise ValueError(f"unknown command: {cmd!r}")

        with self._lock:
            self._dispatch(cmd)
            self._direction = cmd if cmd != "stop" else "stopped"
            self._reset_watchdog(cmd)

        return self.get_telemetry()

    def _reset_watchdog(self, cmd: str):
        """Cancel any pending auto-stop and schedule a new one for movement commands."""
        if self._watchdog is not None:
            self._watchdog.cancel()
            self._watchdog = None

        if cmd == "stop" or config.COMMAND_TIMEOUT <= 0:
            return

        self._watchdog = threading.Timer(config.COMMAND_TIMEOUT, self._auto_stop)
        self._watchdog.daemon = True
        self._watchdog.start()

    def _auto_stop(self):
        """Watchdog callback -- stop the car when no command arrives in time."""
        with self._lock:
            if self._direction != "stopped":
                self._dispatch("stop")
                self._direction = "stopped"

    def get_telemetry(self) -> dict:
        """Return a snapshot of all car stats."""
        voltage = _read_battery_voltage()
        with self._lock:
            return {
                "direction": self._direction,
                "speed": config.DEFAULT_POWER if self._direction != "stopped" else 0,
                "temperature": self._read_cpu_temp(),
                "battery_voltage": round(voltage, 2),
                "battery_percentage": _voltage_to_percentage(voltage),
            }

    def _dispatch(self, cmd: str):
        """Send the command to the hardware layer (called under lock)."""
        if cmd == "forward":
            # reset steering to straight before driving forward
            px = self._hw.get("px")
            if px is not None:
                px.set_dir_servo_angle(0)
            self._hw["forward"](config.DEFAULT_POWER)
        elif cmd == "backward":
            px = self._hw.get("px")
            if px is not None:
                px.set_dir_servo_angle(0)
            self._hw["backward"](config.DEFAULT_POWER)
        elif cmd == "left":
            self._hw["turn_left"](config.TURN_POWER)
        elif cmd == "right":
            self._hw["turn_right"](config.TURN_POWER)
        elif cmd == "stop":
            px = self._hw.get("px")
            if px is not None:
                px.set_dir_servo_angle(0)
            self._hw["stop"]()

    @staticmethod
    def _read_cpu_temp() -> float:
        """Read the Pi CPU temperature in celsius.

        Falls back to 0.0 on non-Pi systems so development/testing still works.
        """
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return round(int(f.read().strip()) / 1000.0, 1)
        except (FileNotFoundError, ValueError):
            return 0.0
