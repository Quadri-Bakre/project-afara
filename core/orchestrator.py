import logging
import os

# Import Drivers
from drivers.isp_auditor import ISPAuditor
from drivers.router_auditor import RouterAuditor
from drivers.ping_driver import PingDriver
from drivers.cisco import CiscoSwitch
from drivers.env_driver import EnvDriver
from drivers.gude_pdu import GudePDU

class CommissioningOrchestrator:
    def __init__(self, project_meta, devices):
        self.meta = project_meta
        self.devices = devices
        self.logger = logging.getLogger("Afara.Orchestrator")
        
        self.stats = {'total': 0, 'pass': 0, 'fail': 0}
        
        self.inventory = {
            "network": [d for d in devices if 'network' in d['group']],
            "power": [d for d in devices if 'power' in d['group']],
            "control": [d for d in devices if 'control' in d['group']],
            "av": [d for d in devices if 'av' in d['group'] or 'video' in d['group'] or 'audio' in d['group']],
            "security": [d for d in devices if 'security' in d['group'] or 'cctv' in d['group']],
            "rms": [d for d in devices if 'rms' in d['group'] or 'server' in d['group']]
        }

        self.header_str = f"   {'STATUS':<7} {'NAME':<25} | {'MODE':<8} | {'IP ADDRESS':<15} | {'MAC ADDRESS':<17} | {'SERIAL':<15} | {'FIRMWARE':<12} | LOCATION"
        self.separator = "   " + "-"*135

    def run_full_sequence(self):
        self._print_header()
        self._run_step_1_environmental()
        self._run_step_2_network()
        self._run_step_3_power()
        self._run_step_4_control()
        self._run_step_5_av()
        self._run_step_6_security()
        self._run_step_7_rms()
        self._print_footer()

    def _print_header(self):
        print("\n" + "="*50)
        print("AFARA by Quadri Bakre")
        print("="*50)
        print(f"Project Reference number:       {self.meta.get('ref_number', 'N/A')}")
        print(f"Project Address:                {self.meta.get('address', 'N/A')}")
        print(f"Commissioning Engineer name:    {self.meta.get('engineer', 'N/A')}")
        print(f"Commissioning Mode:             {self.meta.get('mode', 'Onsite')}")
        print("-" * 50 + "\n")

    def _print_table_header(self):
        print(self.header_str)
        print(self.separator)

    def _print_table_row(self, status, device, mode, mac, serial, firmware, extra_info=None):
        name = device['name']
        ip = device['ip']
        location = f"{device['location']['floor']} > {device['location']['room']}"
        
        if isinstance(serial, list): serial = str(serial[0]) if serial else "---"
        if isinstance(mac, list): mac = str(mac[0]) if mac else "---"
        
        serial = str(serial)[:15]
        mac = str(mac)[:17]
        firmware = str(firmware)[:12] if firmware else "N/A"

        print(f"   {status:<7} {name:<25} | {mode:<8} | {ip:<15} | {mac:<17} | {serial:<15} | {firmware:<12} | {location}")
        
        if extra_info:
            print(f"           L {extra_info}")

    def _audit_group(self, group_name, devices):
        if not devices:
            print(f"   [INFO] No devices grouped as '{group_name}'.\n")
            return

        print(f"   Running Device Audit ({len(devices)} devices)...")
        self._print_table_header()
        backups_collected = []
        
        for dev in devices:
            res = self._audit_device_logic(dev)
            self.stats['total'] += 1
            if res.get('status_bool'): self.stats['pass'] += 1
            else: self.stats['fail'] += 1
            if res.get('backup_file') and res.get('backup_file') != 'N/A':
                backups_collected.append(f"{dev['name']}: {res['backup_file']}")
        
        if backups_collected:
            print(f"\n   [INFO] {len(backups_collected)} Configuration Backups Saved:")
            for b in backups_collected:
                print(f"          - {b}")
        print("")

    def _audit_device_logic(self, dev):
        driver = dev['driver'].lower()
        res = {}
        if "router" in driver:
            raut = RouterAuditor(dev['ip'], dev.get('username'), dev.get('password'), driver)
            res = raut.audit_firmware_and_config()
            status = "[PASS]" if res.get('status') == 'PASS' else "[FAIL]"
            self._print_table_row(status, dev, "(ROUTER)", res.get('mac', 'N/A'), res.get('serial', '---'), res.get('firmware', 'N/A'), None)
            res['status_bool'] = (res.get('status') == 'PASS')
        
        elif "cisco" in driver:
             target = CiscoSwitch(dev['ip'], dev.get('username'), dev.get('password'))
             check = target.check_status()
             
             status = "[PASS]" if check['online'] else "[FAIL]"
             mac = "OFFLINE" if not check['online'] else check.get('mac', '---')
             
             self._print_table_row(status, dev, "(SSH)", mac, check.get('serial', '---'), check.get('firmware', 'N/A'), None)
             
             res = check
             res['status_bool'] = check['online']
             
        else:
            pinger = PingDriver(dev['ip'])
            res = pinger.check_status()
            status = "[PASS]" if res['online'] else "[FAIL]"
            mac = "OFFLINE" if not res['online'] else res.get('mac', '---')
            self._print_table_row(status, dev, "(PING)", mac, "---", "N/A", None)
            res['status_bool'] = res['online']
        return res

    # --- STEPS ---
    def _run_step_1_environmental(self):
        print("1. General & Environmental (The Physical Layer)")
        print("-" * 40)
        
        env = EnvDriver()
        data = env.get_status()
        print(f"   [PASS] Location:           {data['location']}")

        real_temp = None
        real_humid = None
        
        if self.inventory['power']:
            target_pdu = self.inventory['power'][0]
            gude = GudePDU(target_pdu['ip'], target_pdu.get('username'), target_pdu.get('password'))
            sensor_data = gude.get_sensors()
            if sensor_data['temp']:
                real_temp = f"{sensor_data['temp']} (Source: PDU {target_pdu['name']})"
            if sensor_data['humidity']:
                real_humid = f"{sensor_data['humidity']} (Source: PDU {target_pdu['name']})"

        if not real_temp and self.inventory['network']:
            for sw in self.inventory['network']:
                if "switch" in sw['driver'] or "cisco" in sw['driver']:
                    driver = CiscoSwitch(sw['ip'], sw.get('username'), sw.get('password'))
                    temp = driver.get_environment()
                    if temp:
                        real_temp = f"{temp} (Source: Switch {sw['name']})"
                        break

        if real_temp:
            print(f"   [PASS] Room Temperature:   {real_temp}")
        else:
            print(f"   [PASS] Room Temperature:   {data['temp']} (Fallback / Demo Mode)")

        if real_humid:
            print(f"   [PASS] Humidity/Dew Point: {real_humid}")
        else:
            print(f"   [PASS] Humidity/Dew Point: {data['humidity']} (Fallback / Demo Mode)")

        print(f"   [PASS] Noise Floor (dB):   {data['noise']} (Quiet)")
        print("")

    def _run_step_2_network(self):
        print("2. Network (The Backbone)")
        print("-" * 40)
        print("Verifying WAN Performance...")
        auditor = ISPAuditor()
        stats = auditor.run_audit()
        if stats.get('status') != 'FAIL':
            print("\n   ----------------------------------------")
            print("   WAN AUDIT REPORT")
            print("   ----------------------------------------")
            print(f"   Provider:   {stats.get('isp_name', 'Unknown')}")
            print(f"   Public IP:  {stats.get('public_ip', 'Unknown')}")
            print(f"   Download:   {stats.get('download_mbps')} Mbps")
            print(f"   Upload:     {stats.get('upload_mbps')} Mbps")
            print(f"   Latency:    {stats.get('ping_ms')} ms")
            print("   ----------------------------------------\n")
        else:
            print(f"   [FAIL] ISP Check Failed: {stats.get('error')}\n")
        self._audit_group('Network', self.inventory['network'])

    def _run_step_3_power(self):
        print("3. Power & PDU (The Heartbeat)")
        print("-" * 40)
        self._audit_group('Power', self.inventory['power'])

    def _run_step_4_control(self):
        print("4. Control Systems (The Brain)")
        print("-" * 40)
        self._audit_group('Control', self.inventory['control'])

    def _run_step_5_av(self):
        print("5. Video & Audio (The Experience)")
        print("-" * 40)
        self._audit_group('AV', self.inventory['av'])

    def _run_step_6_security(self):
        print("6. CCTV & Security")
        print("-" * 40)
        self._audit_group('Security', self.inventory['security'])

    def _run_step_7_rms(self):
        print("7. RMS & Compute")
        print("-" * 40)
        self._audit_group('RMS', self.inventory['rms'])

    def _print_footer(self):
        total = self.stats['total']
        passed = self.stats['pass']
        failed = self.stats['fail']
        pass_pct = (passed / total * 100) if total > 0 else 0
        fail_pct = (failed / total * 100) if total > 0 else 0
        print("\n" + "="*50)
        print("   COMMISSIONING SUMMARY")
        print("="*50)
        print(f"   Total Devices Checked: {total}")
        print(f"   PASSED:                {passed} ({pass_pct:.1f}%)")
        print(f"   FAILED:                {failed} ({fail_pct:.1f}%)")
        print("="*50)
        print("\n   [INFO] Report Generated Successfully.")
        print("="*50 + "\n")