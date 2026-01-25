import os
import requests
from dotenv import load_dotenv

# Load local configuration secrets
load_dotenv()

class LoxoneManager:
    """
    Controller class for interacting with Loxone Miniserver via REST API.
    """
    def __init__(self):
        # Retrieve credentials from .env
        self.ip = os.getenv("LOXONE_IP")
        self.user = os.getenv("LOXONE_USER")
        self.password = os.getenv("LOXONE_PASS")
        self.vi_name = "V_input1"  # Ensure this Virtual Input exists in Loxone Config

    def send_pulse(self):
        """
        Sends a digital pulse to a specific Virtual Input on the Miniserver.
        Returns:
            dict: The API response status and data.
        """
        if not all([self.ip, self.user, self.password]):
            print("[!] Error: Missing Loxone credentials in .env.")
            return {"status": "error", "message": "Missing Credentials"}

        # Construct authenticated endpoint
        # Format: http://user:pass@IP/dev/sps/io/{VI}/pulse
        endpoint = f"http://{self.user}:{self.password}@{self.ip}/dev/sps/io/{self.vi_name}/pulse"

        print(f"[*] Sending Pulse to Loxone Node: {self.vi_name}...")

        try:
            # Execute HTTP Request
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                print(f"[+] Success: Miniserver accepted command.")
                return {"status": "success", "code": 200, "message": response.text}
            elif response.status_code == 401:
                print("[!] Auth Failure: Check username/password.")
                return {"status": "auth_error", "code": 401}
            else:
                print(f"[!] Failure: HTTP {response.status_code}")
                return {"status": "error", "code": response.status_code}

        except requests.exceptions.RequestException as error:
            print(f"[!] Network Error: {error}")
            return {"status": "network_error", "message": str(error)}

if __name__ == "__main__":
    # Manual execution test
    loxone = LoxoneManager()
    result = loxone.send_pulse()
    print(f"DEBUG OUTPUT: {result}")