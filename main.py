import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Driver Imports
try:
    # 1. The Watchdog (Standardized Ping/Port Check)
    from drivers.generic import GenericDevice
    
    # 2. The Controller (Loxone Hardware Integration)
    from drivers.loxone import LoxoneManager
    
except ImportError as e:
    print(f"[CRITICAL] Driver Import Error: {e}")
    sys.exit(1)

# Load Environment Variables
load_dotenv()

# Configuration
TARGET_ASSET = os.getenv("DEVICE_IP", "8.8.8.8")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 10))

def start_engine():
    print("--- PROJECT AFARA COMMISSIONING ENGINE ---")
    print(f"Target Asset: {TARGET_ASSET}")

    # Initialize Hardware Drivers
    try:
        # A. Create the Monitor (The "Eyes")
        monitor = GenericDevice(name="Primary_Asset", ip=TARGET_ASSET)
        
        # B. Create the Automation (The "Hands")
        automation = LoxoneManager()
        
    except Exception as e:
        print(f"[ERROR] Driver initialization failed: {e}")
        sys.exit(1)

    previous_state = "UNKNOWN"

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Execute Network Check
            is_reachable = monitor.ping_device()

            if is_reachable:
                if previous_state != "ONLINE":
                    print(f"[{timestamp}] [INFO] Asset {TARGET_ASSET} is REACHABLE.")
                    automation.set_state(False) # Deactivate Alarm
                    previous_state = "ONLINE"
            
            else:
                print(f"[{timestamp}] [CRITICAL] Asset {TARGET_ASSET} is UNREACHABLE.")
                
                if previous_state != "OFFLINE":
                    print(f"[{timestamp}] [ACTION] Activating Alarm.")
                    automation.set_state(True) # Activate Alarm
                    previous_state = "OFFLINE"
                    
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Engine terminated.")

if __name__ == "__main__":
    start_engine()