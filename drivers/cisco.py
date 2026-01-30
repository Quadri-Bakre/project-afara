import os
import re
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

class CiscoSwitch:
    """
    Unified Cisco Driver.
    
    Provides an abstraction layer for communicating with heterogeneous Cisco hardware
    (Catalyst 1300/SMB vs. Enterprise IOS/CML) by implementing an automatic driver
    fallback strategy and normalizing hardware identifiers (MAC/Serial).
    """
    def __init__(self, ip, username=None, password=None):
        self.host = ip
        # Resolution precedence: Explicit argument > Environment variable
        self.username = username if (username and len(username) > 0) else os.getenv("CISCO_USER")
        self.password = password if (password and len(password) > 0) else os.getenv("CISCO_PASS")

    def _normalize_mac(self, mac_raw):
        """
        Normalizes MAC addresses to standard colon-separated format (XX:XX:XX:XX:XX:XX).
        """
        if not mac_raw: return "Unknown"
        clean = re.sub(r'[.\-:]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def check_status(self):
        """
        Connects to the device, determines the appropriate driver, and retrieves 
        hardware telemetry (Serial Number and MAC Address).
        """
        # Strategy: Attempt 'cisco_s300' first (optimized for Catalyst 1300/SMB),
        # failing over to 'cisco_ios' (standard Enterprise/CML).
        drivers_to_try = ['cisco_s300', 'cisco_ios']
        
        last_error = ""

        for driver in drivers_to_try:
            device_config = {
                'device_type': driver,
                'host': self.host,
                'username': self.username,
                'password': self.password,
                'port': 22,
                'conn_timeout': 30,
                'global_delay_factor': 2,
                'banner_timeout': 60,
            }

            try:
                with ConnectHandler(**device_config) as connection:
                    
                    # Connection established
                    
                    # Attempt privilege escalation to ensure command access (Critical for CML/Virtual)
                    try: connection.enable()
                    except: pass 

                    # --- RETRIEVE SERIAL NUMBER ---
                    serial = "N/A"
                    try:
                        inv_out = connection.send_command("show inventory")
                        
                        # Match Catalyst 1300 Series format (PID and SN on same line)
                        c1300_match = re.search(r"PID:.*SN:\s*([A-Z0-9]+)", inv_out, re.IGNORECASE)
                        
                        # Match Standard IOS format (SN on dedicated line)
                        ios_match = re.search(r"SN:\s*(\w+)", inv_out)

                        if c1300_match:
                            serial = c1300_match.group(1)
                        elif ios_match:
                            serial = ios_match.group(1)

                    except:
                        pass

                    # Fallback: Virtual Processor ID (Required for CML instances)
                    if serial == "N/A":
                        try:
                            ver_out = connection.send_command("show version")
                            proc_match = re.search(r"Processor board ID\s+(\w+)", ver_out)
                            if proc_match:
                                serial = proc_match.group(1) + " (Virt)"
                        except:
                            pass

                    # --- RETRIEVE MAC ADDRESS ---
                    mac = "Unknown"
                    try:
                        sys_out = connection.send_command("show system")
                        
                        # Match Catalyst 1300/SMB 'System MAC Address' syntax
                        sys_mac = re.search(r"System MAC Address:\s*([0-9a-fA-F:.]+)", sys_out, re.IGNORECASE)
                        
                        # Match Standard 'MAC Address' syntax
                        std_mac = re.search(r"MAC Address:\s*([0-9a-fA-F:.]+)", sys_out, re.IGNORECASE)

                        if sys_mac:
                            mac = self._normalize_mac(sys_mac.group(1))
                        elif std_mac:
                            mac = self._normalize_mac(std_mac.group(1))
                        
                        # Fallback A: IOS Base Ethernet MAC
                        if mac == "Unknown":
                            ver_out = connection.send_command("show version")
                            base_mac = re.search(r"Base [Ee]thernet MAC [Aa]ddress\s*:\s*([0-9a-fA-F:.]+)", ver_out)
                            if base_mac:
                                mac = self._normalize_mac(base_mac.group(1))
                            
                            # Fallback B: Vlan1 Interface MAC
                            if mac == "Unknown":
                                int_out = connection.send_command("show interface Vlan1")
                                int_mac = re.search(r"address is ([0-9a-fA-F:.]+)", int_out)
                                if int_mac:
                                    mac = self._normalize_mac(int_mac.group(1))

                    except:
                        mac = "ONLINE"

                    connection.disconnect()
                    
                    return {
                        "online": True,
                        "serial": serial,
                        "mac": mac,
                        "error": None
                    }

            except Exception as e:
                # Log error and proceed to next driver candidate
                last_error = str(e)
                continue

        # --- EXHAUSTED ALL DRIVERS ---
        err_msg = last_error.split('\n')[0]
        if "Authentication" in err_msg:
             err_msg = "Auth Failed"
        elif "TCP" in err_msg or "timed out" in err_msg:
             err_msg = "Offline / No Route"

        return {
            "online": False,
            "serial": "---",
            "mac": "OFFLINE",
            "error": err_msg[:40]
        }