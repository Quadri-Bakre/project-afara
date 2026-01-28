import platform
import subprocess
from getmac import get_mac_address

class GenericDevice:
    def __init__(self, ip):
        self.ip = ip

    def check_status(self):
        try:
            # 1. Ping
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w', '1000', self.ip]
            
            if platform.system().lower() == 'windows':
                 pass 
            
            response = subprocess.call(
                command, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            is_online = (response == 0)

            # 2. MAC Lookup
            mac_str = "Unknown"
            if is_online:
                try:
                    mac = get_mac_address(ip=self.ip)
                    if mac:
                        mac_str = mac.upper()
                    else:
                        mac_str = "N/A (Routed)"
                except:
                    mac_str = "Error"

            # RETURN SEPARATE KEYS
            return {
                "online": is_online,
                "serial": "N/A", # Generic devices don't show serials via Ping
                "mac": mac_str,
                "error": None
            }

        except Exception:
            return {
                "online": False,
                "serial": "---",
                "mac": "---",
                "error": "Driver Error"
            }