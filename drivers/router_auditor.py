from netmiko import ConnectHandler
import logging
import os
import re
import paramiko
import time

# Setup Module Logger
logger = logging.getLogger("Afara.Router")

class RouterAuditor:
    def __init__(self, ip, username, password, driver_type="router_cisco"):
        self.ip = ip
        self.username = username
        self.password = password
        self.driver_type = driver_type.lower()
        self.is_draytek = "draytek" in self.driver_type

    def _normalize_mac(self, mac_raw):
        """Standardizes MAC to XX:XX:XX:XX:XX:XX format."""
        if not mac_raw: return "N/A"
        clean = re.sub(r'[.\-:]', '', mac_raw).upper()
        if len(clean) == 12:
            return ":".join(clean[i:i+2] for i in range(0, 12, 2))
        return mac_raw

    def connect(self):
        """Establishes SSH connection with Legacy KEX Support."""
        
        # 1. Select Valid Netmiko Driver
        # 'generic_termserver' is used for Draytek because it handles the '>' prompt better
        device_type = 'generic_termserver' if self.is_draytek else 'cisco_ios'
        
        # 2. Inject Legacy Key Exchange (CRITICAL for Vigor 2862)
        if self.is_draytek:
            if 'diffie-hellman-group1-sha1' not in paramiko.Transport._preferred_kex:
                paramiko.Transport._preferred_kex = (
                    'diffie-hellman-group1-sha1', 
                    'diffie-hellman-group14-sha1'
                ) + paramiko.Transport._preferred_kex

        # 3. Connection Parameters (Robust Timeouts)
        connect_params = {
            'device_type': device_type,
            'host': self.ip,
            'username': self.username,
            'password': self.password,
            'secret': self.password,
            'port': 22,
            'conn_timeout': 20,   # 20s timeout to prevent "Error reading banner"
            'auth_timeout': 20,
            'banner_timeout': 20,
            'global_delay_factor': 2,
        }
        
        # Disable strict checking for compatibility
        try:
            connect_params['ssh_strict'] = False
        except: pass

        try:
            self.connection = ConnectHandler(**connect_params)
            
            # Cisco requires enable mode; Draytek does not
            if not self.is_draytek:
                self.connection.enable()
            
            return True
        except Exception as e:
            # print(f"[DEBUG] Connection Failed: {e}") # Uncomment for debugging
            return False

    def audit_firmware_and_config(self):
        """Main entry point that branches to the correct audit logic."""
        audit_data = {
            "status": "FAIL",
            "firmware": "N/A",
            "serial": "---",
            "mac": "N/A",
            "uptime": "N/A",
            "wan_ips": [], 
            "backup_file": "N/A"
        }

        if not self.connect():
            return audit_data

        try:
            audit_data["status"] = "PASS"

            # Branch Logic based on Driver Type
            if self.is_draytek:
                self._audit_draytek(audit_data)
            else:
                self._audit_cisco(audit_data)

        except Exception as e:
            logger.error(f"Audit Error: {e}")
            audit_data['status'] = "FAIL"
        
        finally:
            if self.connection:
                self.connection.disconnect()

        return audit_data

    def _audit_draytek(self, data):
        """Commands specifically for Draytek Vigor Routers."""
        
        # 1. FIRMWARE & SERIAL (sys version)
        self.connection.clear_buffer()
        # Using timing-based send for stability
        output_ver = self.connection.send_command_timing("sys version", delay_factor=2)
        
        # Regex for Firmware "Version: 3.9.4.1_BT English"
        fw_match = re.search(r"Version\s*[:\s]+\s*([0-9\._a-zA-Z]+)", output_ver, re.IGNORECASE)
        if fw_match: data['firmware'] = fw_match.group(1)

        # Regex for Serial "Router serial no: 179003400482"
        sn_match = re.search(r"Router serial no\s*[:\s]+\s*([A-Z0-9]+)", output_ver, re.IGNORECASE)
        if sn_match: data['serial'] = sn_match.group(1)

        # 2. MAC ADDRESS
        self.connection.clear_buffer()
        output_iface = self.connection.send_command_timing("sys iface", delay_factor=2)
        
        # Regex allowing both Colons (:) and Dashes (-)
        mac_match = re.search(r"([0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2}[:-][0-9A-F]{2})", output_iface, re.IGNORECASE)
        if mac_match: 
            data['mac'] = self._normalize_mac(mac_match.group(1))

        # 3. WAN IP
        try:
            self.connection.clear_buffer()
            route_out = self.connection.send_command_timing("ip route status")
            found_ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", route_out)
            data['wan_ips'] = [ip for ip in found_ips if not ip.startswith('127.') and ip != '0.0.0.0']
        except: pass

        # 4. BACKUP
        try:
            self.connection.clear_buffer()
            config = self.connection.send_command_timing("sys conf show", delay_factor=4)
            if not os.path.exists("backups"): os.makedirs("backups")
            filename = f"backups/draytek_{self.ip}.txt"
            with open(filename, "w") as f: f.write(config)
            data['backup_file'] = filename
        except: pass
        
        data['uptime'] = "Online (Draytek)"

    def _audit_cisco(self, data):
        """Standard Commands for Cisco IOS Routers."""
        
        # 1. VERSION & SERIAL
        ver_out = self.connection.send_command("show version")
        
        ver_match = re.search(r"Version\s+([^,\s]+)", ver_out)
        if ver_match: data['firmware'] = ver_match.group(1)
        
        sn_match = re.search(r"Processor board ID\s+(\w+)", ver_out)
        if sn_match: data['serial'] = sn_match.group(1)

        up_match = re.search(r"uptime is (.*)", ver_out, re.IGNORECASE)
        if up_match:
            raw_parts = up_match.group(1).split(',')
            data['uptime'] = ", ".join(raw_parts[:2])

        # 2. WAN IP
        ip_out = self.connection.send_command("show ip interface brief")
        found_ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", ip_out)
        data['wan_ips'] = [ip for ip in found_ips if not ip.startswith('127.') and ip != '0.0.0.0']

        # 3. MAC ADDRESS (Try ARP first, then Interface)
        cmd_arp = f"show ip arp {self.ip}"
        arp_out = self.connection.send_command(cmd_arp)
        mac_match = re.search(r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", arp_out)
        if mac_match:
            data['mac'] = self._normalize_mac(mac_match.group(1))
        else:
            int_out = self.connection.send_command("show interfaces GigabitEthernet0/0 | include bia")
            fallback = re.search(r"([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})", int_out)
            if fallback: data['mac'] = self._normalize_mac(fallback.group(1))

        # 4. BACKUP
        config = self.connection.send_command("show running-config")
        if not os.path.exists("backups"): os.makedirs("backups")
        filename = f"backups/cisco_{self.ip}.cfg"
        with open(filename, "w") as f: f.write(config)
        data['backup_file'] = filename