from netmiko import ConnectHandler
import logging
import re
import os
import time

# Setup Module Logger
logger = logging.getLogger("Afara.Crestron")

class CrestronAuditor:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.device_config = {
            'device_type': 'generic_termserver',
            'host': self.ip,
            'username': self.username,
            'password': self.password,
            'port': 22,
            'global_delay_factor': 2, 
            'session_log_record_writes': True
        }

    def _normalize_mac(self, mac_raw):
        """Standardizes MAC to XX:XX:XX:XX:XX:XX format."""
        if not mac_raw or "N/A" in mac_raw: return "N/A"
        clean = re.sub(r'[.\-:\s]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def audit_firmware_and_config(self):
        """Main entry point for Crestron Audit."""
        audit_data = {
            "status": "FAIL",
            "firmware": "N/A",
            "serial": "---",
            "mac": "N/A",
            "uptime": "N/A",
            "connected_devices": [], 
            "backup_file": "N/A"
        }

        try:
            # 1. CONNECT
            net_connect = ConnectHandler(**self.device_config)
            net_connect.send_command("\n") 
            time.sleep(1)
            
            audit_data["status"] = "PASS"

            # 2. GET VERSION
            ver_out = net_connect.send_command("ver", expect_string=r">")
            fw_match = re.search(r"\[v([0-9\.]+)", ver_out)
            if fw_match:
                audit_data['firmware'] = fw_match.group(1)

            # 3. GET UPTIME
            up_out = net_connect.send_command("uptime", expect_string=r">")
            up_match = re.search(r"running for\s+(.*)", up_out)
            if up_match:
                audit_data['uptime'] = up_match.group(1).split('\n')[0].strip()

            # 4. GET MAC & NETWORK
            ip_out = net_connect.send_command("ipconfig /all", expect_string=r">")
            mac_match = re.search(r"MAC Address\s*\.+\s*:\s*([0-9a-fA-F\.]+)", ip_out)
            if mac_match:
                audit_data['mac'] = self._normalize_mac(mac_match.group(1))
            
            audit_data['serial'] = audit_data['mac']

            # 5. DISCOVER CRESNET (Legacy)
            cresnet_out = net_connect.send_command("reportcresnet", expect_string=r">")
            cres_devices = re.findall(r"^(\d{2}|[0-9A-F]{2})\s+:\s+(.+)", cresnet_out, re.MULTILINE)
            for dev_id, dev_type in cres_devices:
                audit_data['connected_devices'].append(f"Cresnet ID {dev_id}: {dev_type.strip()}")

            # 6. DISCOVER NETWORK DEVICES (NAX/Touchpanels)
            try:
                # Increased timeout to 20s to prevent "Pattern not detected" error
                auto_out = net_connect.send_command("autodiscover query table", expect_string=r">", read_timeout=20)
                
                # Parse Output Format: 
                # 10.20.30.100 :  C : NAX-01 : DM-NAX-8ZSA [v3...] @E-c4...
                lines = auto_out.splitlines()
                for line in lines:
                    if ":" in line and "IP Address" not in line:
                        parts = line.split(":")
                        if len(parts) >= 4:
                            # ip = parts[0].strip()
                            # ip_id = parts[1].strip()
                            # name = parts[2].strip()
                            model_raw = parts[3].strip() 
                            
                            # Clean up model (remove [version] garbage)
                            model = model_raw.split('[')[0].strip()
                            
                            # Add to list: "NAX-01 (DM-NAX-8ZSA)"
                            dev_str = f"{parts[2].strip()} ({model})"
                            audit_data['connected_devices'].append(dev_str)

            except Exception:
                # Silently ignore autodiscovery failures
                # logger.warning(f"Autodiscovery failed: {e}")
                pass

            # 7. CREATE BACKUP
            err_log = net_connect.send_command("errlog", expect_string=r">")
            
            backup_content = (
                f"--- CRESTRON SYSTEM REPORT ---\nIP: {self.ip}\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"--- VERSION ---\n{ver_out}\n\n"
                f"--- IP CONFIG ---\n{ip_out}\n\n"
                f"--- DISCOVERY (NAX/ETHERNET) ---\n{auto_out}\n\n"
                f"--- ERROR LOG ---\n{err_log}\n"
            )

            if not os.path.exists("backups"): os.makedirs("backups")
            filename = f"backups/crestron_{self.ip}.txt"
            with open(filename, "w") as f:
                f.write(backup_content)
            audit_data['backup_file'] = filename

            net_connect.disconnect()

        except Exception:
            # Silently fail connection errors (SSH refused, Timeout, Auth fail)
            # logger.error(f"Crestron Connection Failed: {e}")
            audit_data["status"] = "FAIL"

        return audit_data