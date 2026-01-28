import os
import time
import requests
from netmiko import ConnectHandler
from dotenv import load_dotenv
from datetime import datetime

# --- CONFIGURATION ---
load_dotenv()

# 1. Cisco Credentials (Input)
CISCO_DEVICE = {
    'device_type': 'cisco_ios',
    'host':   os.getenv("DEVICE_IP"),     # 192.168.1.150
    'username': os.getenv("CISCO_USERNAME"),
    'password': os.getenv("CISCO_PASSWORD"),
    'secret':   os.getenv("CISCO_SECRET"),
    'port': 22,
}
TARGET_INTERFACE = "GigabitEthernet0/0"

# 2. Loxone Credentials (Output)
LOX_IP = os.getenv("LOXONE_IP")           # 192.168.1.100
LOX_USER = os.getenv("LOXONE_USER")
LOX_PASS = os.getenv("LOXONE_PASS")

# Loxone Virtual Input Name (Create this in Loxone Config if needed)
# For testing, we can use a known lighting output or a virtual input
LOX_COMMAND_RED = f"http://{LOX_IP}/dev/sps/io/VI1/On"   # Turn Alarm ON
LOX_COMMAND_GREEN = f"http://{LOX_IP}/dev/sps/io/VI1/Off" # Turn Alarm OFF

def set_loxone_alarm(state):
    """
    Sends an HTTP GET request to the Loxone Miniserver to trigger a state change.
    State: True (Alarm ON), False (Alarm OFF)
    """
    url = LOX_COMMAND_RED if state else LOX_COMMAND_GREEN
    status_text = "ACTIVATING ALARM" if state else "CLEARING ALARM"
    
    try:
        # Send request with Basic Auth
        requests.get(url, auth=(LOX_USER, LOX_PASS), timeout=2)
        print(f"[ACTION] {status_text} -> Loxone Miniserver")
    except Exception as e:
        print(f"[ERROR] Failed to contact Loxone: {e}")

def check_cisco_health():
    """
    Connects to Cisco via SSH to check interface status.
    Returns: True (Healthy), False (Critical/Down)
    """
    try:
        connection = ConnectHandler(**CISCO_DEVICE)
        connection.enable()
        output = connection.send_command(f"show interface {TARGET_INTERFACE}")
        connection.disconnect()
        
        # Logic: If 'line protocol is up', it is healthy
        if "line protocol is up" in output:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[ERROR] Cisco Connection Failed: {e}")
        return False # Assume failure if we can't connect

def run_lifecycle():
    print("--- STARTING INTEGRATED MONITORING SYSTEM ---")
    print(f"Watching: {CISCO_DEVICE['host']} ({TARGET_INTERFACE})")
    print(f"Actuator: {LOX_IP}")
    print("-" * 50)

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 1. READ (Input)
            is_healthy = check_cisco_health()
            
            # 2. DECIDE & ACT (Logic & Output)
            if is_healthy:
                print(f"[{timestamp}] [GREEN] System Healthy.")
                # Optional: Ensure alarm is off (Self-Healing)
                set_loxone_alarm(False) 
            else:
                print(f"[{timestamp}] [RED] CRITICAL FAILURE DETECTED!")
                set_loxone_alarm(True)
            
            # 3. WAIT (Polling Interval)
            # We wait 15 seconds to avoid spamming the SSH connection
            time.sleep(15)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Monitor stopped by user.")

if __name__ == "__main__":
    run_lifecycle()