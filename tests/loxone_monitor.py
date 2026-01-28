import time
import os
import platform
from datetime import datetime

# --- CONFIGURATION ---
TARGET_NAME = "Loxone Miniserver"
TARGET_IP = "192.168.1.100"  # Loxone IP
CHECK_INTERVAL = 10          # Seconds between checks

def is_device_online(ip):
    """
    Sends a single ping to the target IP.
    Returns True if online, False if offline.
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Construct the ping command (quiet mode)
    if platform.system().lower() == 'windows':
        command = f"ping {param} 1 {ip} > nul 2>&1"
    else:
        command = f"ping {param} 1 {ip} > /dev/null 2>&1"
    
    response = os.system(command)
    return response == 0

def start_monitoring():
    print(f"[SYSTEM] Starting Persistent Monitor for {TARGET_NAME} ({TARGET_IP})...")
    print(f"[INFO] Press Ctrl+C to stop.")
    print("-" * 60)

    try:
        # --- THE INFINITE LOOP ---
        while True:
            # 1. Get current timestamp
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 2. Perform the check
            online = is_device_online(TARGET_IP)
            
            # 3. Text-based Status Logging
            if online:
                print(f"[{now}] [ONLINE]  {TARGET_NAME} is reachable.")
            else:
                print(f"[{now}] [OFFLINE] {TARGET_NAME} is unreachable.")

            # 4. The Pause
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Monitoring stopped by user.")

if __name__ == "__main__":
    start_monitoring()