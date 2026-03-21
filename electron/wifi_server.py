import socket
import json
import time
import random

# Bind to all available interfaces (recommended for development). If you need a specific interface, set HOST to that local IP.
HOST = "0.0.0.0"
PORT = 65432          # Port to listen on (non-privileged ports are > 1023)

# Simulated robot state
robot_state = {
    "battery": 85.0,
    "temperature": 45.2,
    "distance": 0.0,
    "speed": 0.0,
    "direction": "IDLE"
}

# Simulate battery drain over time
battery_drain_rate = 0.1  # Decrease battery by 0.1% every update
last_battery_update = time.time()

def update_battery():
    """Update battery level based on time elapsed"""
    """Replace with REAL FUNCTIONS when testing with actual hardware"""
    global last_battery_update
    current_time = time.time()
    if current_time - last_battery_update > 2:  # Update every 2 seconds
        robot_state["battery"] = max(0, robot_state["battery"] - battery_drain_rate)
        last_battery_update = current_time

def handle_command(command):
    """Handle incoming commands from the frontend"""
    command = command.strip().upper()
    
    if command == "FORWARD":
        robot_state["direction"] = "FORWARD"
        robot_state["speed"] = 1.0
    elif command == "BACKWARD":
        robot_state["direction"] = "BACKWARD"
        robot_state["speed"] = -1.0
    elif command == "LEFT":
        robot_state["direction"] = "LEFT"
        robot_state["speed"] = 0.0
    elif command == "RIGHT":
        robot_state["direction"] = "RIGHT"
        robot_state["speed"] = 0.0
    else:
        # Default or passthrough for other commands
        robot_state["direction"] = command
    
    # Simulate temperature increase during movement
    if robot_state["speed"] != 0:
        robot_state["temperature"] = min(75, robot_state["temperature"] + 0.5)
    
    # Simulate distance traveled
    if robot_state["speed"] != 0:
        robot_state["distance"] += abs(robot_state["speed"]) * 0.1

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"WiFi server listening on {HOST}:{PORT} (use the host's reachable IP with client)")

    try:
        while 1:
            client, clientInfo = s.accept()
            print("server recv from: ", clientInfo)
            data = client.recv(1024)      # receive 1024 Bytes of message in binary format
            if data != b"":
                command = data.decode().strip()
                print(f"Received command: {command}")
                
                # Handle the incoming command
                handle_command(command)
                
                # Update battery
                update_battery()
                
                # Send back telemetry data as JSON
                response = json.dumps(robot_state)
                client.sendall(response.encode())
                print(f"Sent telemetry: {response}")
    except: 
        print("Closing socket")
        client.close()
        s.close()    