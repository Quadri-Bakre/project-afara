import socket
import time
import threading
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Network Configuration
HOST = '0.0.0.0'
# Default to 8085 if not defined in .env
PORT = int(os.getenv("AFARA_PORT", 8085)) 
BUFFER_SIZE = 1024

def start_tcp_listener():
    """
    Initializes a background TCP server to listen for state changes 
    initiated by the Control4 controller.
    """
    print(f"[SYSTEM] Initializing TCP Listener on port {PORT}...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Enable address reuse to facilitate quick restarts
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()
            
            while True:
                # Blocking call; waits for incoming connection
                conn, addr = s.accept()
                with conn:
                    # Connection logging
                    # print(f"[NET] Connection established: {addr[0]}")
                    
                    while True:
                        data = conn.recv(BUFFER_SIZE)
                        if not data:
                            break
                        
                        # Decode payload and remove transmission artifacts
                        command = data.decode('utf-8').strip()
                        if command:
                            handle_command(command)
                        
    except OSError as e:
        print(f"[CRITICAL] Socket binding failed: {e}")
        sys.exit(1)

def handle_command(command):
    """
    Routes incoming commands to the appropriate logic handlers.
    
    Args:
        command (str): The raw command string received from Control4.
    """
    print(f"[EVENT] Received: {command}")
    
    if command == "LIGHT_ON":
        # TODO: Trigger occupancy active state
        print("[ACTION] State Set: Active")
        
    elif command == "LIGHT_OFF":
        # TODO: Trigger occupancy inactive state
        print("[ACTION] State Set: Inactive")

def main_loop():
    """
    Primary application runtime loop. 
    Handles sensor polling and facial recognition tasks.
    """
    try:
        while True:
            # Placeholder for main thread operations
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutdown sequence initiated.")

if __name__ == "__main__":
    # 1. Initialize TCP Listener in a daemon thread
    listener = threading.Thread(target=start_tcp_listener, daemon=True)
    listener.start()

    # 2. Begin Main Execution Loop
    print("[SYSTEM] Afara Manager is running.")
    main_loop()