import os
import sys
from netmiko import ConnectHandler
from dotenv import load_dotenv

# Initialize Environment Configuration
load_dotenv()

# --- ASSET SCHEMA ---
# Defines the target Cisco node parameters.
# Identity attributes (Hostname, OS) are initialized as None for dynamic population.
CISCO_NODE = {
    'ip_address': os.getenv("DEVICE_IP"),
    'username':   os.getenv("CISCO_USERNAME"),
    'password':   os.getenv("CISCO_PASSWORD"),
    'secret':     os.getenv("CISCO_SECRET"),
    'device_type': 'cisco_ios',
    'hostname': None,          # Pending Discovery
    'os_version': None,        # Pending Discovery
    'is_critical': True
}

def execute_discovery():
    """
    Connects to the Cisco device to extract identity and version telemetry.
    Updates the local asset schema with live data.
    """
    if not CISCO_NODE['ip_address']:
        print("[CRITICAL] Target IP undefined in environment variables.")
        sys.exit(1)

    print(f"--- INITIATING CISCO DISCOVERY: {CISCO_NODE['ip_address']} ---")

    try:
        # Establish SSH Session
        connection = ConnectHandler(
            device_type=CISCO_NODE['device_type'],
            host=CISCO_NODE['ip_address'],
            username=CISCO_NODE['username'],
            password=CISCO_NODE['password'],
            secret=CISCO_NODE['secret']
        )
        connection.enable()

        # 1. Retrieve Hostname
        print("[SYSTEM] Querying device hostname...")
        prompt = connection.find_prompt()
        # Sanitize prompt string (remove CLI mode characters '#' or '>')
        clean_hostname = prompt.replace('#', '').replace('>', '').strip()
        CISCO_NODE['hostname'] = clean_hostname

        # 2. Retrieve IOS Version
        print("[SYSTEM] Querying IOS version...")
        version_out = connection.send_command("show version | include Version")
        # Extract primary version string
        clean_version = version_out.splitlines()[0].strip()
        CISCO_NODE['os_version'] = clean_version

        connection.disconnect()
        print("[SUCCESS] Device telemetry captured.")

    except Exception as e:
        print(f"[ERROR] Discovery failed: {e}")
        sys.exit(1)

def print_audit_log():
    """
    Generates a structured audit record from the discovered data.
    """
    print("\n--- CISCO ASSET AUDIT ---")
    print(f"IP Address:     {CISCO_NODE['ip_address']}")
    print(f"Hostname:       {CISCO_NODE['hostname']}")
    print(f"IOS Version:    {CISCO_NODE['os_version']}")
    
    if CISCO_NODE['is_critical']:
        print("Asset Class:    CRITICAL INFRASTRUCTURE")
    else:
        print("Asset Class:    STANDARD EDGE")
    print("-" * 30)

if __name__ == "__main__":
    execute_discovery()
    print_audit_log()