import os
import re
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

class CiscoSwitch:
    def __init__(self, ip, username=None, password=None):
        self.host = ip
        self.username = username if (username and len(username) > 0) else os.getenv("CISCO_USER")
        self.password = password if (password and len(password) > 0) else os.getenv("CISCO_PASS")

    def _normalize_mac(self, mac_raw):
        if not mac_raw: return "Unknown"
        clean = re.sub(r'[.\-:]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def check_status(self):
        """Standard SSH Check (Serial, Firmware, MAC)."""
        device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'port': 22,
            'conn_timeout': 5,  # 5s timeout for main check
            'auth_timeout': 5,
            'banner_timeout': 10,
        }

        try:
            with ConnectHandler(**device_config) as connection:
                try: connection.enable()
                except: pass 

                serial = "N/A"
                firmware = "N/A"
                
                # 1. Version & Serial
                try:
                    ver_out = connection.send_command("show version")
                    proc_match = re.search(r"Processor board ID\s+(\w+)", ver_out)
                    if proc_match: serial = proc_match.group(1)
                    
                    fw_match = re.search(r"Version\s+([^,\s]+)", ver_out)
                    if fw_match: firmware = fw_match.group(1)
                except: pass

                # 2. MAC Address
                mac = "Unknown"
                try:
                    base_mac = re.search(r"Base [Ee]thernet MAC [Aa]ddress\s*:\s*([0-9a-fA-F:.]+)", ver_out)
                    if base_mac:
                        mac = self._normalize_mac(base_mac.group(1))
                    else:
                        int_out = connection.send_command("show interface Vlan1")
                        int_mac = re.search(r"address is ([0-9a-fA-F:.]+)", int_out)
                        if int_mac: mac = self._normalize_mac(int_mac.group(1))
                except: mac = "ONLINE"

                connection.disconnect()
                
                return {
                    "online": True,
                    "serial": serial,
                    "mac": mac,
                    "firmware": firmware,
                    "error": None
                }

        except Exception as e:
            err_msg = str(e)
            if "Authentication" in err_msg: err_msg = "Auth Failed"
            elif "timed out" in err_msg: err_msg = "Offline"
            else: err_msg = "Conn Error"

            return {
                "online": False,
                "serial": "---",
                "mac": "OFFLINE",
                "firmware": "N/A",
                "error": err_msg
            }

    # --- NEW FUNCTION: GET TEMPERATURE ---
    def get_environment(self):
        """Attempts to fetch temperature from the switch chassis."""
        device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'conn_timeout': 2,  # <--- CRITICAL FIX: Fail fast (2s) if offline
            'timeout': 5        # Command execution timeout
        }
        
        try:
            with ConnectHandler(**device_config) as conn:
                conn.enable()
                # Try standard command
                out = conn.send_command("show environment temperature")
                
                # Regex for "Temperature Value: 24 C" (Catalyst/Nexus)
                match = re.search(r"(\d+)\s*C", out)
                if match:
                    return f"{match.group(1)}°C"
                
                # If that failed, try "show env all"
                out_all = conn.send_command("show env all")
                match_all = re.search(r"(\d+)\s*C", out_all)
                if match_all:
                    return f"{match_all.group(1)}°C"
                    
        except Exception:
            return None
            
        return None