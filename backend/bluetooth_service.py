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
        self._server_sock: socket.socket | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        if self._running:
            return self.bound_address

        self._server_sock = self._create_server_socket()
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return self.bound_address

    def stop(self):
        self._running = False
        if self._server_sock is not None:
            try:
                self._server_sock.close()
            except OSError:
                pass
            finally:
                self._server_sock = None

    @property
    def bound_address(self):
        if self._server_sock is None:
            return None
        return self._server_sock.getsockname()

    def _create_server_socket(self):
        server_sock = socket.socket(
            socket.AF_BLUETOOTH,
            socket.SOCK_STREAM,
            socket.BTPROTO_RFCOMM,
        )
        bind_addr = self._resolve_bind_address()
        server_sock.bind((bind_addr, config.BT_CHANNEL))
        server_sock.listen(1)
        server_sock.settimeout(2.0)
        return server_sock

    @staticmethod
    def _resolve_bind_address():
        if config.BT_MAC and config.BT_MAC.lower() != "any":
            return config.BT_MAC
        return getattr(socket, "BDADDR_ANY", "00:00:00:00:00:00")

    def _listen_loop(self):
        if self._server_sock is None:
            return

        try:
            while self._running:
                try:
                    client_sock, addr = self._server_sock.accept()
                except socket.timeout:
                    continue
                except OSError as e:
                    if self._running:
                        print(f"bluetooth accept failed: {e}")
                    break

                print(f"bluetooth client connected: {addr}")
                self._handle_client(client_sock)
                print(f"bluetooth client disconnected: {addr}")
        finally:
            if self._server_sock is not None:
                try:
                    self._server_sock.close()
                except OSError:
                    pass
                finally:
                    self._server_sock = None

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
        if line == "telemetry":
            return {"status": "ok", "telemetry": self._car.get_telemetry()}

        try:
            telemetry = self._car.execute_command(line)
            return {"status": "ok", "telemetry": telemetry}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
