import requests
import os
from requests.auth import HTTPBasicAuth
import urllib3

# Suppress "Unverified HTTPS" warnings (Standard for local AV hardware)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CrestronNVX:
    def __init__(self, ip, username=None, password=None):
        self.ip = ip
        # Use credentials from .env, or default to admin/admin
        self.username = username or os.getenv("CRESTRON_USER") or "admin"
        self.password = password or os.getenv("CRESTRON_PASS") or "admin"
        self.base_url = f"https://{self.ip}"

    def check_status(self):
        """
        Connects via HTTPS/REST to fetch device details.
        Returns: {online, serial, mac, info}
        """
        try:
            # Attempt to reach the root page or a known API endpoint
            # Timeout is fast (3s) because local devices should answer quickly
            response = requests.get(
                self.base_url, 
                auth=HTTPBasicAuth(self.username, self.password),
                verify=False, 
                timeout=3
            )
            
            # 200 means "OK" (Authorized and Online)
            # 401 means "Unauthorized" (Online, but wrong password)
            if response.status_code == 200:
                return {
                    "online": True,
                    "serial": "NVX-SIM-001",    # Placeholder (Needs real HW to parse JSON)
                    "mac": "00:10:7F:00:00:01", # Placeholder
                    "error": None
                }
            elif response.status_code == 401:
                return {
                    "online": False,
                    "serial": "---",
                    "mac": "AUTH FAIL",
                    "error": "Wrong Password"
                }
            else:
                return {
                    "online": False,
                    "serial": "---",
                    "mac": "OFFLINE",
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "online": False,
                "serial": "---",
                "mac": "OFFLINE",
                "error": "Connection Timeout"
            }