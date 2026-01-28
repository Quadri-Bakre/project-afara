import os
import re
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

class CiscoSwitch:
    def __init__(self, ip, username=None, password=None):
        self.host = ip
        self.username = username or os.getenv("CISCO_USER") or os.getenv("CISCO_USERNAME")
        self.password = password or os.getenv("CISCO_PASS") or os.getenv("CISCO_PASSWORD")
        self.secret = os.getenv("CISCO_SECRET")
        
        self.device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'secret': self.secret,
            'timeout': 10,
            'port': 22,
        }

    def _normalize_mac(self, mac_raw):
        clean = re.sub(r'[.\-:]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def check_status(self):
        try:
            with ConnectHandler(**self.device_config) as connection:
                if self.secret:
                    connection.enable()
                
                output_ver = connection.send_command("show version")
                
                # 1. Serial
                serial_match = re.search(r"Processor board ID (\w+)", output_ver)
                if not serial_match:
                     serial_match = re.search(r"System Serial Number\s*:\s*(\w+)", output_ver)
                serial = serial_match.group(1) if serial_match else "Unknown"

                # 2. MAC
                mac = "Unknown"
                mac_patterns = [
                    r"[Bb]ase [Ee]thernet MAC [Aa]ddress\s*:\s*([0-9a-fA-F:.]+)",
                    r"[Ss]ystem MAC [Aa]ddress\s*:\s*([0-9a-fA-F:.]+)",
                ]
                for pattern in mac_patterns:
                    match = re.search(pattern, output_ver)
                    if match:
                        mac = match.group(1)
                        break

                if mac == "Unknown":
                    output_iface = connection.send_command("show interface vlan 1")
                    fallback_match = re.search(r"address is ([0-9a-fA-F.]+)", output_iface)
                    if fallback_match:
                        mac = fallback_match.group(1)

                if mac != "Unknown":
                    mac = self._normalize_mac(mac)

                # RETURN DICTIONARY WITH SEPARATE KEYS
                return {
                    "online": True,
                    "serial": serial,
                    "mac": mac,
                    "error": None
                }

        except Exception as e:
            error_msg = str(e).replace('\n', ' ').replace('\r', '')
            if "Authentication failed" in error_msg:
                error_msg = "Auth Failed"
            
            return {
                "online": False,
                "serial": "---",
                "mac": "---",
                "error": error_msg
            }