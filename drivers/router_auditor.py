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
                timeout=15,       #Increased timeout
                auth_timeout=10,
                global_delay_factor=2 # Slowed down for virtual routers
            )
            self.connection.enable()
            return True
        except Exception as e:
            # logger.error(f"Conn Error: {e}")
            return False

    def audit_firmware_and_config(self):
        """
        Gets Firmware, Backs up Config, and Gets MAC.
        """
        audit_data = {
            "status": "FAIL",
            "firmware": "N/A",
            "serial": "---",
            "mac": "N/A",
            "backup_file": "N/A"
        }

        if not self.connect():
            return audit_data

        try:
            audit_data["status"] = "PASS"

            # --- 1. FIRMWARE & SERIAL ---
            ver_out = self.connection.send_command("show version")
            
            ver_match = re.search(r"Version\s+([^,\s]+)", ver_out)
            if ver_match:
                audit_data['firmware'] = ver_match.group(1)
            
            sn_match = re.search(r"Processor board ID\s+(\w+)", ver_out)
            if sn_match:
                audit_data['serial'] = sn_match.group(1)

            # --- 2. MAC ADDRESS ---
            # Method A: ARP Table (Checks the router's own IP to find its MAC)
            cmd_arp = f"show ip arp {self.ip}"
            arp_out = self.connection.send_command(cmd_arp)
            
            # Look for xxxx.xxxx.xxxx
            mac_match = re.search(r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", arp_out)
            
            if mac_match:
                raw_mac = mac_match.group(1)
                audit_data['mac'] = self._normalize_mac(raw_mac)
            else:
                # Method B: Fallback to Interface (Specific)
                # Specifically asking for the 'bia' line to ignore the header text
                int_out = self.connection.send_command("show interfaces GigabitEthernet0/0 | include bia")
                
                # Use very broad regex to catch anything that looks like the mac
                fallback_match = re.search(r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", int_out)
                if fallback_match:
                     audit_data['mac'] = self._normalize_mac(fallback_match.group(1))

            # --- 3. CONFIG BACKUP ---
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