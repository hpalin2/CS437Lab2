"""Threaded Bluetooth RFCOMM service using stdlib socket.AF_BLUETOOTH.

Shares the CarController with the Flask server so both Wi-Fi and Bluetooth
clients can drive the car and read telemetry through a single state.
"""

import json
import socket
import threading

import config


class BluetoothService:
    """RFCOMM listener that accepts one client at a time in a daemon thread."""

    def __init__(self, car_controller):
        self._car = car_controller
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._listen_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def _listen_loop(self):
        while self._running:
            server_sock = socket.socket(
                socket.AF_BLUETOOTH,
                socket.SOCK_STREAM,
                socket.BTPROTO_RFCOMM,
            )
            server_sock.bind((config.BT_MAC, config.BT_CHANNEL))
            server_sock.listen(1)
            server_sock.settimeout(2.0)

            try:
                while self._running:
                    try:
                        client_sock, addr = server_sock.accept()
                    except socket.timeout:
                        continue

                    print(f"bluetooth client connected: {addr}")
                    self._handle_client(client_sock)
                    print(f"bluetooth client disconnected: {addr}")
            finally:
                server_sock.close()

    def _handle_client(self, sock: socket.socket):
        buf = ""
        try:
            while self._running:
                data = sock.recv(1024)
                if not data:
                    break

                buf += data.decode("utf-8", errors="replace")

                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    response = self._process_line(line)
                    sock.sendall((json.dumps(response) + "\n").encode())
        except OSError:
            pass
        finally:
            sock.close()

    def _process_line(self, line: str) -> dict:
        try:
            telemetry = self._car.execute_command(line)
            return {"status": "ok", "telemetry": telemetry}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
