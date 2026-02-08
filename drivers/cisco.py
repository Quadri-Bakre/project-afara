import os
import re
import logging
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

class CiscoSwitch:
    """
    Unified Cisco Driver (Advanced).
    
    Combines:
    1. Driver Fallback (SMB/S300 -> IOS) for mixed environments.
    2. Deep Diagnostics (Uptime, CRC Errors, PoE).
    3. Robust Connection (Paging disabled, Slower timing for old hardware).
    """
    def __init__(self, ip, username=None, password=None):
        self.host = ip
        self.username = username if (username and len(username) > 0) else os.getenv("CISCO_USER")
        self.password = password if (password and len(password) > 0) else os.getenv("CISCO_PASS")
        self.secret = os.getenv("CISCO_SECRET")

    def _normalize_mac(self, mac_raw):
        if not mac_raw: return "Unknown"
        clean = re.sub(r'[.\-:]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def _log_debug(self, message):
        try:
            with open("ssh_debug.log", "a") as f:
                f.write(f"[{self.host}] {message}\n")
        except: pass

    def check_status(self):
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
            "poe": {"status": "No PoE", "utilization": "N/A", "used": "N/A", "budget": "N/A"},
            "error": None
        }

        # Strategy: Try 'cisco_s300' (SMB) first, then 'cisco_ios' (Enterprise)
        drivers_to_try = ['cisco_s300', 'cisco_ios']
        
        for driver in drivers_to_try:
            device_config = {
                'device_type': driver,
                'host': self.host,
                'username': self.username,
                'password': self.password,
                'secret': self.secret or self.password,
                'port': 22,
                'conn_timeout': 15,       # Increased for slow switches
                'auth_timeout': 15,
                'banner_timeout': 30,     # Increased for legal banners
                'global_delay_factor': 4, # 4x Slower (Critical for reliability)
                'fast_cli': False         # Disable fast mode
            }

            try:
                with ConnectHandler(**device_config) as connection:
                    # --- CRITICAL: DISABLE PAGING ---
                    try: 
                        connection.enable()
                        # Send both types of paging disable commands to cover all bases
                        connection.send_command("terminal length 0") # IOS
                        connection.send_command("terminal datadump") # SMB
                    except: pass
                    
                    data["online"] = True

                    # 1. HARDWARE INFO (Serial/FW/Uptime)
                    try:
                        # Try IOS version command first
                        ver_out = connection.send_command("show version")
                        
                        # Serial (Try IOS pattern first, then SMB pattern)
                        ios_sn = re.search(r"Processor board ID\s+(\w+)", ver_out, re.IGNORECASE)
                        smb_sn = re.search(r"System Serial Number\s*:\s*(\w+)", ver_out, re.IGNORECASE)
                        
                        # Inventory check for SMBs that hide SN in 'show inventory'
                        if not ios_sn and not smb_sn:
                            inv_out = connection.send_command("show inventory")
                            smb_sn = re.search(r"SN:\s*(\w+)", inv_out, re.IGNORECASE)

                        if ios_sn: data["serial"] = ios_sn.group(1)
                        elif smb_sn: data["serial"] = smb_sn.group(1)

                        # --- FIRMWARE FIX ---
                        # Pattern 1: "Version 15.2(4)E" (IOS Standard)
                        # Pattern 2: "Version: 1.4.2.02" (SMB Standard - Note the colon)
                        # Pattern 3: "SW version    : 2.5.0.83" (Some Catalyst types)
                        
                        fw_patterns = [
                            r"Version\s+([0-9a-zA-Z\.\(\)\-]+)",      # IOS
                            r"Version:\s*([0-9a-zA-Z\.\(\)\-]+)",     # SMB
                            r"SW [Vv]ersion\s*:\s*([0-9a-zA-Z\.\(\)\-]+)" # Fallback
                        ]
                        
                        for pat in fw_patterns:
                            fw_match = re.search(pat, ver_out, re.IGNORECASE)
                            if fw_match:
                                data["firmware"] = fw_match.group(1)
                                break

                        # Uptime
                        up_match = re.search(r"uptime is (.*)", ver_out, re.IGNORECASE)
                        if up_match:
                            raw_up = up_match.group(1).split(', ')
                            data["uptime"] = ", ".join(raw_up[:2])
                    except: pass

                    # 2. MAC ADDRESS
                    data["mac"] = "Unknown"
                    try:
                        # Try 'show system' (SMB) then 'show version' (IOS)
                        sys_out = connection.send_command("show system")
                        sys_mac = re.search(r"System MAC Address:\s*([0-9a-fA-F:.]+)", sys_out, re.IGNORECASE)
                        
                        if sys_mac:
                            data["mac"] = self._normalize_mac(sys_mac.group(1))
                        else:
                            base_mac = re.search(r"Base [Ee]thernet MAC [Aa]ddress\s*:\s*([0-9a-fA-F:.]+)", ver_out, re.IGNORECASE)
                            if base_mac:
                                data["mac"] = self._normalize_mac(base_mac.group(1))
                            else:
                                # Final Fallback: Vlan1
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

                    # 4. PHYSICAL HEALTH (Port Errors)
                    try:
                        int_stats = connection.send_command("show interfaces")
                        current_iface = "Unknown"
                        for line in int_stats.splitlines():
                            if "line protocol is" in line:
                                current_iface = line.split()[0]
                            if "input errors" in line or "CRC" in line:
                                errs = re.search(r"(\d+) input errors.*?(\d+) CRC", line)
                                if errs:
                                    inputs = int(errs.group(1))
                                    crcs = int(errs.group(2))
                                    if inputs > 0 or crcs > 0:
                                        data["port_errors"].append(f"{current_iface} (CRC:{crcs}|In:{inputs})")
                    except: pass

                    # 5. POE AUDIT
                    try:
                        poe_out = connection.send_command("show power inline")
                        used_match = re.search(r"Used\s*:\s*([\d\.]+)", poe_out, re.IGNORECASE)
                        avail_match = re.search(r"Available\s*:\s*([\d\.]+)", poe_out, re.IGNORECASE)

                        if not used_match:
                            # Try Table Format
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
                    except: 
                        data["poe"]["status"] = "Not Supported"

                    # 6. BACKUP
                    try:
                        config = connection.send_command("show running-config")
                        if not os.path.exists("backups"): os.makedirs("backups")
                        safe_ip = self.host.replace('.', '_')
                        backup_filename = f"backups/switch_{safe_ip}.cfg"
                        with open(backup_filename, "w") as f: f.write(config)
                        data["backup_file"] = backup_filename
                    except: pass

                    connection.disconnect()
                    return data # SUCCESS - RETURN DATA

            except Exception as e:
                # Log specific error for this driver attempt
                self._log_debug(f"Driver '{driver}' failed: {e}")
                last_error = str(e)
                continue # Try next driver

        # If loop finishes without returning, all drivers failed
        err_msg = last_error
        if "Authentication" in err_msg: err_msg = "Auth Failed"
        elif "timed out" in err_msg: err_msg = "Offline"
        else: err_msg = "Conn Error"
        
        data["error"] = err_msg
        return data

    def get_environment(self):
        """Preserved Temperature Check."""
        # Simple single-driver attempt for temp (speed optimization)
        device_config = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'conn_timeout': 5,
            'timeout': 10
        }
        try:
            with ConnectHandler(**device_config) as conn:
                try: conn.enable()
                except: pass
                out = conn.send_command("show environment temperature")
                match = re.search(r"(\d+)\s*C", out)
                if match: return f"{match.group(1)}°C"
                out_all = conn.send_command("show env all")
                match_all = re.search(r"(\d+)\s*C", out_all)
                if match_all: return f"{match_all.group(1)}°C"
        except: return None
        return None