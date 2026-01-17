import os
import re
from dotenv import load_dotenv
from netmiko import ConnectHandler
# We keep the error handling we fixed earlier
from netmiko import NetmikoTimeoutException, NetmikoAuthenticationException

load_dotenv()

class CiscoManager:
    """
    Controller class for interacting with lab infrastructure.
    """
    def __init__(self):
        self.host = os.getenv("DEVICE_IP")
        self.username = os.getenv("CISCO_USERNAME")
        self.password = os.getenv("CISCO_PASSWORD")
        self.secret = os.getenv("CISCO_SECRET")
        
        self.device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'secret': self.secret,
            'port': 22,
        }

    def get_system_status(self):
        """
        Connects to the device and retrieves vital telemetry (Uptime, Serial).
        """
        print(f"[*] Connecting to {self.host} for telemetry...")
        
        try:
            # Use 'with' context manager for auto-disconnecting
            with ConnectHandler(**self.device_config) as connection:
                # 1. Elevate to Enable Mode (for privileged commands)
                connection.enable()
                
                # 2. Send Command
                print("[*] Sending: 'show version'")
                output = connection.send_command("show version")
                
                # 3. Parse Data (Using Regex to extract specific values)
                # Find "uptime is..."
                uptime_match = re.search(r"uptime is (.+)", output)
                uptime = uptime_match.group(1) if uptime_match else "Unknown"

                # Find Serial Number (Processor board ID)
                serial_match = re.search(r"Processor board ID (\w+)", output)
                serial = serial_match.group(1) if serial_match else "Unknown"

                return {
                    "status": "Online",
                    "uptime": uptime,
                    "serial_number": serial
                }

        except Exception as e:
            print(f"[!] Telemetry Failed: {e}")
            return None

if __name__ == "__main__":
    manager = CiscoManager()
    
    # Execute Telemetry Check
    data = manager.get_system_status()
    
    if data:
        print("\n--- DEVICE REPORT ---")
        print(f"Status: {data['status']}")
        print(f"Serial: {data['serial_number']}")
        print(f"Uptime: {data['uptime']}")
        print("---------------------")