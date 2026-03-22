import socket
import json

HOST = "0.0.0.0"
PORT = 65432          # Port to listen on (non-privileged ports are > 1023)

print("Enter commands: FORWARD, BACKWARD, LEFT, RIGHT, or STATUS")
print("Type quit to exit")

while True:
    command = input("Command > ").strip()
    if command.lower() == "quit":
        break
    if command == "":
        continue

    # Normalize commands
    normalized = command.strip().upper()
    if normalized not in ["FORWARD", "BACKWARD", "LEFT", "RIGHT", "STATUS"]:
        print("Invalid command; use FORWARD/BACKWARD/LEFT/RIGHT/STATUS")
        continue

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            s.sendall((normalized + "\n").encode())

            data = s.recv(4096)
            if not data:
                print("No response from server")
                continue

            payload = data.decode().strip()
            try:
                telemetry = json.loads(payload)
                print("--- Telemetry from Pi ---")
                print(f"Direction   : {telemetry.get('direction', 'N/A')}")
                print(f"Speed       : {telemetry.get('speed', 0):.1f}")
                print(f"Distance    : {telemetry.get('distance', 0):.1f}")
                print(f"Temperature : {telemetry.get('temperature', 0):.1f}")
                print(f"Battery     : {telemetry.get('battery', 0):.1f}%")
                print("------------------------")
            except json.JSONDecodeError:
                print("Raw response:", payload)

        except Exception as e:
            print("Connection error:", e)

print("Client exited")
