import os
import time
from datetime import datetime
from netmiko import ConnectHandler
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

# Load infrastructure credentials from environment
# Maps generic 'DEVICE_IP' to specific Cisco target
CISCO_IP = os.getenv("DEVICE_IP")
CISCO_USERNAME = os.getenv("CISCO_USERNAME")
CISCO_PASSWORD = os.getenv("CISCO_PASSWORD")
CISCO_SECRET = os.getenv("CISCO_SECRET")

# Verify configuration integrity
if not all([CISCO_IP, CISCO_USERNAME, CISCO_PASSWORD, CISCO_SECRET]):
    print("[SYSTEM ERROR] Critical configuration missing in environment variables.")
    exit(1)

CISCO_DEVICE = {
    'device_type': 'cisco_ios',
    'host':   CISCO_IP,
    'username': CISCO_USERNAME,
    'password': CISCO_PASSWORD,
    'secret':   CISCO_SECRET,
    'port': 22,
}

TARGET_INTERFACE = "GigabitEthernet0/0" 

def get_interface_status():
    """
    Establishes SSH connection to the network device and retrieves
    status output for the target interface.
    """
    print(f"[NET] Connecting to {CISCO_DEVICE['host']}...")
    try:
        connection = ConnectHandler(**CISCO_DEVICE)
        connection.enable()
        
        command = f"show interface {TARGET_INTERFACE}"
        output = connection.send_command(command)
        
        connection.disconnect()
        return output
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return None

def analyze_health(interface_data):
    """
    Parses raw interface data to determine operational health.
    """
    if interface_data is None:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # --- LOGIC ENGINE ---
    if "administratively down" in interface_data:
        status = "DISABLED"
        action = "No action required (Manual Override)."
        indicator = "[GRAY]"
    elif "line protocol is down" in interface_data:
        status = "CRITICAL"
        action = "ALERT: Link failure detected."
        indicator = "[RED]"
    elif "line protocol is up" in interface_data:
        status = "HEALTHY"
        action = "System optimal."
        indicator = "[GREEN]"
    else:
        status = "UNKNOWN"
        action = "Manual inspection required."
        indicator = "[YELLOW]"

    print(f"[{timestamp}] {indicator} {TARGET_INTERFACE} Status: {status}")
    print(f"           Action: {action}")
    print("-" * 50)

def main():
    print("--- STARTING NETWORK INTERFACE MONITOR ---\n")
    raw_data = get_interface_status()
    analyze_health(raw_data)

if __name__ == "__main__":
    main()