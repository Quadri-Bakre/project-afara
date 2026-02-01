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
        """Advanced SSH Check: Serial, FW, Backups, PoE, Uptime, & Physical Layer Errors."""
        device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'port': 22,
            'conn_timeout': 5,
            'auth_timeout': 5,
            'banner_timeout': 10,
        }

        # Default Data Structure
        data = {
            "online": False,
            "serial": "---",
            "mac": "OFFLINE",
            "firmware": "N/A",
            "uptime": "N/A",   
            "port_errors": [],   
            "backup_file": "N/A",
            "vlans": [],
            "poe": {
                "budget": "N/A",
                "used": "N/A",
                "utilization": "N/A",
                "status": "No PoE"
            },
            "error": None
        }

        try:
            with ConnectHandler(**device_config) as connection:
                try: connection.enable()
                except: pass 
                
                data["online"] = True

                # 1. Version, Serial, UPTIME
                try:
                    ver_out = connection.send_command("show version")
                    
                    # Serial
                    proc_match = re.search(r"Processor board ID\s+(\w+)", ver_out)
                    if proc_match: data["serial"] = proc_match.group(1)
                    
                    # Firmware
                    fw_match = re.search(r"Version\s+([^,\s]+)", ver_out)
                    if fw_match: data["firmware"] = fw_match.group(1)
                    
                    # Uptime
                    up_match = re.search(r"uptime is (.*)", ver_out)
                    if up_match:
                        
                        raw_up = up_match.group(1).split(', ')
                        data["uptime"] = ", ".join(raw_up[:2]) # Take first 2 parts (e.g., "1 year, 2 weeks")
                except: pass

                # 2. MAC Address
                data["mac"] = "Unknown"
                try:
                    base_mac = re.search(r"Base [Ee]thernet MAC [Aa]ddress\s*:\s*([0-9a-fA-F:.]+)", ver_out)
                    if base_mac:
                        data["mac"] = self._normalize_mac(base_mac.group(1))
                    else:
                        int_out = connection.send_command("show interface Vlan1")
                        int_mac = re.search(r"address is ([0-9a-fA-F:.]+)", int_out)
                        if int_mac: data["mac"] = self._normalize_mac(int_mac.group(1))
                except: data["mac"] = "ONLINE"

                # 3. VLAN AUDIT
                try:
                    vlan_out = connection.send_command("show vlan brief")
                    vlan_ids = re.findall(r"^(\d+)\s+", vlan_out, re.MULTILINE)
                    data["vlans"] = vlan_ids if vlan_ids else ["1"]
                except: pass

                # 4. PHYSICAL HEALTH CHECK (NEW)
                # Scans for CRC errors (bad cables)
                try:
                    int_stats = connection.send_command("show interfaces")
                    # Regex for "GigabitEthernet0/1 is up... 5 input errors, 10 CRC"
                    # Simplified scanner
                    current_iface = "Unknown"
                    for line in int_stats.splitlines():
                        # Capture Interface Name
                        if "line protocol is" in line:
                            current_iface = line.split()[0]
                        
                        # Check Errors
                        if "input errors" in line or "CRC" in line:
                            # Extract numbers
                            errs = re.search(r"(\d+) input errors, (\d+) CRC", line)
                            if errs:
                                inputs = int(errs.group(1))
                                crcs = int(errs.group(2))
                                if inputs > 0 or crcs > 0:
                                    data["port_errors"].append(f"{current_iface} (CRC:{crcs}|In:{inputs})")
                except: pass

                # 5. POE BUDGET & UTILISATION
                try:
                    poe_out = connection.send_command("show power inline")
                    used_match = re.search(r"Used\s*:\s*([\d\.]+)", poe_out, re.IGNORECASE)
                    avail_match = re.search(r"Available\s*:\s*([\d\.]+)", poe_out, re.IGNORECASE)

                    if not used_match:
                        table_match = re.search(r"\d+\s+([\d\.]+)\s+([\d\.]+)\s+[\d\.]+", poe_out)
                        if table_match:
                            avail_val = float(table_match.group(1))
                            used_val = float(table_match.group(2))
                        else:
                            avail_val, used_val = 0.0, 0.0
                    else:
                        used_val = float(used_match.group(1))
                        avail_val = float(avail_match.group(1))

                    if avail_val > 0:
                        util_pct = (used_val / avail_val) * 100
                        data["poe"] = {
                            "budget": f"{avail_val} W",
                            "used": f"{used_val} W",
                            "utilization": f"{util_pct:.1f}%",
                            "status": "Active"
                        }
                    else:
                        data["poe"]["status"] = "No PoE Power"

                except Exception: 
                    data["poe"]["status"] = "Not Supported"

                # 6. BACKUP CONFIG
                try:
                    config = connection.send_command("show running-config")
                    if not os.path.exists("backups"): os.makedirs("backups")
                    safe_ip = self.host.replace('.', '_')
                    backup_filename = f"backups/switch_{safe_ip}.cfg"
                    with open(backup_filename, "w") as f: f.write(config)
                    data["backup_file"] = backup_filename
                except Exception:
                    data["backup_file"] = "N/A"

                connection.disconnect()
                return data

        except Exception as e:
            err_msg = str(e)
            if "Authentication" in err_msg: err_msg = "Auth Failed"
            elif "timed out" in err_msg: err_msg = "Offline"
            else: err_msg = "Conn Error"
            
            data["error"] = err_msg
            return data

    def get_environment(self):
        """Preserved Temperature Check."""
        device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'conn_timeout': 2,
            'timeout': 5
        }
        try:
            with ConnectHandler(**device_config) as conn:
                conn.enable()
                out = conn.send_command("show environment temperature")
                match = re.search(r"(\d+)\s*C", out)
                if match: return f"{match.group(1)}°C"
                out_all = conn.send_command("show env all")
                match_all = re.search(r"(\d+)\s*C", out_all)
                if match_all: return f"{match_all.group(1)}°C"
        except: return None
        return None