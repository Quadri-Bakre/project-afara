import requests
import logging
import re
import os
import subprocess
import platform

# Setup Module Logger
logger = logging.getLogger("Afara.GudeDriver")

class GudeAuditor:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        # Magic URL for Status
        self.url_status = f"http://{self.ip}/status.json?components=1073741823"
        # Config Backup URL (Text format)
        self.url_backup = f"http://{self.ip}/config.txt"
        
        self.auth = (self.username, self.password) if self.username and self.password else None

    def _normalize_mac(self, mac_raw):
        """Standardizes MAC to XX:XX:XX:XX:XX:XX format."""
        if not mac_raw or "N/A" in mac_raw: return "N/A"
        clean = re.sub(r'[.\-:]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def _get_mac_from_arp(self):
        """Resolves MAC using local ARP table (Fallback)."""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        try:
            subprocess.run(['ping', param, '1', self.ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
            arp_out = subprocess.check_output(['arp', '-a']).decode('utf-8', errors='ignore')
            escaped_ip = self.ip.replace('.', r'\.')
            pattern = f"({escaped_ip}).+?([0-9a-fA-F]{{1,2}}[:-][0-9a-fA-F]{{1,2}}[:-][0-9a-fA-F]{{1,2}}[:-][0-9a-fA-F]{{1,2}}[:-][0-9a-fA-F]{{1,2}}[:-][0-9a-fA-F]{{1,2}})"
            match = re.search(pattern, arp_out)
            if match:
                return self._normalize_mac(match.group(2))
        except: pass
        return "N/A"

    def audit_firmware_and_config(self):
        """Main entry point for Gude Audit."""
        audit_data = {
            "status": "FAIL",
            "firmware": "N/A",
            "serial": "---",
            "mac": "N/A",
            "uptime": "N/A",
            "wan_ips": [], 
            "backup_file": "N/A",
            "port_status": [],
            "power_metrics": "N/A"
        }

        try:
            # 1. FETCH STATUS
            response = requests.get(self.url_status, auth=self.auth, timeout=5)
            
            if response.status_code == 200:
                audit_data["status"] = "PASS"
                json_data = response.json()
                
                # Firmware
                misc = json_data.get("misc", {})
                if "firm_v" in misc: audit_data['firmware'] = misc['firm_v']
                elif "firmware" in misc: audit_data['firmware'] = misc['firmware']

                # MAC Address
                eth = json_data.get("ethernet", {})
                ipv4 = json_data.get("ipv4", {})
                if "mac" in eth: audit_data['mac'] = self._normalize_mac(eth['mac'])
                elif "mac" in ipv4: audit_data['mac'] = self._normalize_mac(ipv4['mac'])
                else: audit_data['mac'] = self._get_mac_from_arp()

                # Serial (Use MAC)
                audit_data['serial'] = audit_data['mac']

                # Power Metrics
                sensors = json_data.get("sensor_values", [])
                for s in sensors:
                    if s.get("type") == 9: 
                        try:
                            vals = s.get("values", [])[0]
                            volt = vals[0]['v']
                            curr = vals[1]['v']
                            watt = vals[4]['v']
                            audit_data['power_metrics'] = f"{volt}V / {curr}A"
                        except: pass
                        break

                # Port Status
                outputs = json_data.get("outputs", [])
                status_list = []
                for out in outputs:
                    state = "ON" if out.get("state") == 1 else "OFF"
                    name = out.get("name", f"Port {out.get('index')}")
                    status_list.append(f"{name}: {state}")
                audit_data['port_status'] = status_list
                
                audit_data['uptime'] = "Online (HTTP)"

                # 2. PERFORM BACKUP (Download config.txt)
                try:
                    bkp_resp = requests.get(self.url_backup, auth=self.auth, timeout=10)
                    if bkp_resp.status_code == 200:
                        if not os.path.exists("backups"): os.makedirs("backups")
                        filename = f"backups/gude_{self.ip}.txt"
                        with open(filename, "wb") as f:
                            f.write(bkp_resp.content)
                        audit_data['backup_file'] = filename
                except Exception:
                    # Silently ignore backup failure
                    pass

            else:
                # Silently fail if HTTP error
                # logger.error(f"Gude HTTP Failed: {response.status_code}")
                audit_data['status'] = "FAIL"
                
        except Exception:
            # Silently fail connection errors (Timeout/Refused)
            # logger.error(f"Gude Audit Error: {e}")
            audit_data['status'] = "FAIL"

        return audit_data