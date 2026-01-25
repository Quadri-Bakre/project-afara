import time
import os
import platform
import sys
from datetime import datetime
from dotenv import load_dotenv

# --- DEPENDENCY CHECK ---
# This import requires 'loxone_controller.py' to be in the same directory.
try:
    from loxone_controller import LoxoneManager
except ImportError:
    print("[CRITICAL] Module 'loxone_controller.py' not found. Ensure driver file is present.")
    sys.exit(1)

# Load Environment Variables
load_dotenv()

TARGET_ASSET = os.getenv("DEVICE_IP")
POLL_INTERVAL = 10

def verify_reachability(ip):
    """
    Checks network reachability via system ICMP.
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    redirect = "NUL" if platform.system().lower() == 'windows' else "/dev/null"
    
    command = f"ping {param} 1 {ip} > {redirect} 2>&1"
    response = os.system(command)
    
    return response == 0

def start_monitor_service():
    print("--- INFRASTRUCTURE MONITORING SERVICE ---")
    print(f"Target: {TARGET_ASSET}")

    # Initialize Driver
    try:
        automation = LoxoneManager()
    except Exception as e:
        print(f"[ERROR] Driver initialization failed: {e}")
        sys.exit(1)

    previous_state = "UNKNOWN"

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            is_reachable = verify_reachability(TARGET_ASSET)

            if is_reachable:
                if previous_state != "ONLINE":
                    print(f"[{timestamp}] [INFO] Asset {TARGET_ASSET} is REACHABLE.")
                    # Turn the Alarm OFF (Green)
                    automation.set_state(False)
                    previous_state = "ONLINE"
            
            else:
                # Failure Logic
                print(f"[{timestamp}] [CRITICAL] Asset {TARGET_ASSET} is UNREACHABLE.")
                
                if previous_state != "OFFLINE":
                    print(f"[{timestamp}] [ACTION] Setting Alarm State to ON.")
                    # Turn the Alarm ON (Red) and KEEP it on
                    automation.set_state(True)
                    previous_state = "OFFLINE"
                    
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Service terminated.")

if __name__ == "__main__":
    start_monitor_service()