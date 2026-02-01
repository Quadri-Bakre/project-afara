from netmiko import ConnectHandler
import logging
import datetime
import os
import re

# Setup Module Logger
logger = logging.getLogger("Afara.Router")

class RouterAuditor:
    def __init__(self, ip, username, password, driver_type="router_cisco"):
        self.ip = ip
        self.username = username
        self.password = password
        self.driver_type = driver_type.lower()
        self.connection = None

    def _normalize_mac(self, mac_raw):
        """Converts xxxx.xxxx.xxxx to XX:XX:XX:XX:XX:XX"""
        if not mac_raw: return "N/A"
        clean = re.sub(r'[.\-:]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def connect(self):
        """Establishes SSH connection."""
        device_type = 'cisco_ios'
        
        if "draytek" in self.driver_type:
            device_type = 'generic_termserver'

        try:
            self.connection = ConnectHandler(
                device_type=device_type,
                host=self.ip,
                username=self.username,
                password=self.password,
                secret=self.password,
                timeout=15,       
                auth_timeout=10,
                global_delay_factor=2 
            )
            self.connection.enable()
            return True
        except Exception as e:
            return False

    def audit_firmware_and_config(self):
        """
        Gets Firmware, Uptime, WAN IPs, Backs up Config, and Gets MAC.
        """
        audit_data = {
            "status": "FAIL",
            "firmware": "N/A",
            "serial": "---",
            "mac": "N/A",
            "uptime": "N/A",
            "wan_ips": [], # List of IPs found on the router
            "backup_file": "N/A"
        }

        if not self.connect():
            return audit_data

        try:
            audit_data["status"] = "PASS"

            # --- 1. FIRMWARE, SERIAL & UPTIME ---
            ver_out = self.connection.send_command("show version")
            
            # Firmware
            ver_match = re.search(r"Version\s+([^,\s]+)", ver_out)
            if ver_match:
                audit_data['firmware'] = ver_match.group(1)
            
            # Serial
            sn_match = re.search(r"Processor board ID\s+(\w+)", ver_out)
            if sn_match:
                audit_data['serial'] = sn_match.group(1)

            # Uptime
            up_match = re.search(r"uptime is (.*)", ver_out, re.IGNORECASE)
            if up_match:
                raw_parts = up_match.group(1).split(',')
                audit_data['uptime'] = ", ".join(raw_parts[:2])
            else:
                if "draytek" in self.driver_type:
                    audit_data['uptime'] = "Online (Draytek)"

            # --- 2. GET ROUTER IPs (WAN DETECTION) ---
            # Need to find what IPs are assigned to this device
            if "draytek" in self.driver_type:
                # Drayteks often show IPs in 'show ip route' or 'show status'
                ip_out = self.connection.send_command("show ip route")
            else:
                # Cisco Standard
                ip_out = self.connection.send_command("show ip interface brief")
            
            # Regex to find all valid IP addresses in the output
            found_ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", ip_out)
            
            # Filter out localhost (127.x.x.x) and default route (0.0.0.0)
            audit_data['wan_ips'] = [ip for ip in found_ips if not ip.startswith('127.') and ip != '0.0.0.0']

            # --- 3. MAC ADDRESS ---
            cmd_arp = f"show ip arp {self.ip}"
            arp_out = self.connection.send_command(cmd_arp)
            mac_match = re.search(r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", arp_out)
            
            if mac_match:
                audit_data['mac'] = self._normalize_mac(mac_match.group(1))
            else:
                int_out = self.connection.send_command("show interfaces GigabitEthernet0/0 | include bia")
                fallback_match = re.search(r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", int_out)
                if fallback_match:
                     audit_data['mac'] = self._normalize_mac(fallback_match.group(1))

            # --- 4. CONFIG BACKUP ---
            config = self.connection.send_command("show running-config")
            
            if not os.path.exists("backups"):
                os.makedirs("backups")
            
            filename = f"backups/router_{self.ip}.cfg"
            with open(filename, "w") as f:
                f.write(config)
            audit_data['backup_file'] = filename

        except Exception as e:
            logger.error(f"Audit Error: {e}")
            audit_data['status'] = "FAIL"
        
        finally:
            if self.connection:
                self.connection.disconnect()

        return audit_data