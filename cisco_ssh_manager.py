import os
from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutException, NetmikoAuthenticationException

# Load local configuration secrets
load_dotenv()

class CiscoManager:
    """
    Controller class for interacting with lab infrastructure.
    """
    def __init__(self):
        # Retrieve credentials from .env
        self.host = os.getenv("DEVICE_IP")
        self.username = os.getenv("CISCO_USERNAME")
        self.password = os.getenv("CISCO_PASSWORD")
        self.secret = os.getenv("CISCO_SECRET")
        
        # Netmiko connection profile
        self.device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'secret': self.secret,
            'port': 22,
        }

    def check_connection(self):
        """
        Validates SSH session establishment with the switch.
        """
        print(f"[*] Initiating connection to {self.host}...")
        
        try:
            # Execute connection attempt
            connection = ConnectHandler(**self.device_config)
            print(f"[+] Connection active: {self.host}")
            
            # Grab the prompt to confirm target identity
            prompt = connection.find_prompt()
            print(f"[+] Verified Hostname: {prompt}")
            
            connection.disconnect()
            return True

        except NetmikoTimeoutException:
            print(f"[!] Timeout: {self.host} is unreachable.")
            return False
        except NetmikoAuthenticationException:
            print("[!] Authentication Failed. Verify values in .env.")
            return False
        except Exception as e:
            print(f"[!] Error: {e}")
            return False

if __name__ == "__main__":
    # Execution entry point
    manager = CiscoManager()
    manager.check_connection()