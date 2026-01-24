import os
import sys
from netmiko import ConnectHandler
from dotenv import load_dotenv

# Load security credentials
load_dotenv()

# --- CONFIGURATION SCHEMA ---
# List of Critical VLANs to deploy
VLAN_SCHEMA = [10, 20, 30, 40, 50]

# Device Connection Profile
CISCO_SWITCH = {
    'device_type': 'cisco_ios',
    'host':   os.getenv("DEVICE_IP"),
    'username': os.getenv("CISCO_USERNAME"),
    'password': os.getenv("CISCO_PASSWORD"),
    'secret':   os.getenv("CISCO_SECRET"),
}

def deploy_vlans():
    print(f"--- CONNECTING TO {CISCO_SWITCH['host']} ---")
    
    try:
        connection = ConnectHandler(**CISCO_SWITCH)
        connection.enable()
        
        # Verify we are on the correct device
        hostname = connection.find_prompt()
        print(f"[SYSTEM] Connected to: {hostname}")

        # Loop through list and configure
        for vlan_id in VLAN_SCHEMA:
            print(f"[CONFIG] Provisioning VLAN {vlan_id}...")
            
            commands = [
                f"vlan {vlan_id}",
                f"name AUTOMATED_VLAN_{vlan_id}",
                "exit"
            ]
            connection.send_config_set(commands)
            
        # Save to startup-config
        print("[SYSTEM] Saving configuration...")
        connection.save_config()
        connection.disconnect()
        print("--- DEPLOYMENT COMPLETE ---")

    except Exception as e:
        print(f"[CRITICAL] Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_vlans()