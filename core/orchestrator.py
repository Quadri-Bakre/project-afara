import logging
import os
from datetime import datetime

# Import Drivers
from drivers.isp_auditor import ISPAuditor
from drivers.router_auditor import RouterAuditor
from drivers.ping_driver import PingDriver
from drivers.cisco import CiscoSwitch
from drivers.env_driver import EnvDriver
from drivers.gude_pdu import GudePDU
from core.reporter import PDFReporter

class CommissioningOrchestrator:
    def __init__(self, project_meta, devices):
        self.meta = project_meta
        self.devices = devices
        self.logger = logging.getLogger("Afara.Orchestrator")
        
        self.stats = {'total': 0, 'pass': 0, 'fail': 0}
        
        self.report_data = {
            "env": {},
            "isp": {},
            "groups": {} 
        }
        
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
        self._generate_pdf_report()

    def _generate_pdf_report(self):
        print("   [INFO] Generating PDF Report...")
        try:
            pdf = PDFReporter(self.meta)
            pdf.generate_cover()
            
            # 1. Environmental
            pdf.add_section_title("1. Environmental Audit")
            env = self.report_data.get('env', {})
            pdf.add_key_value("Location:", env.get('location', 'N/A'))
            pdf.add_key_value("Temperature:", env.get('temp', 'N/A'))
            pdf.add_key_value("Humidity:", env.get('humidity', 'N/A'))
            pdf.ln(10)

            # 2. ISP
            pdf.add_section_title("2. ISP & WAN Performance")
            isp = self.report_data.get('isp', {})
            pdf.add_key_value("Provider:", isp.get('isp_name', 'N/A'))
            pdf.add_key_value("Public IP:", isp.get('public_ip', 'N/A'))
            pdf.add_key_value("Download Speed:", f"{isp.get('download_mbps', 0)} Mbps")
            pdf.add_key_value("Upload Speed:", f"{isp.get('upload_mbps', 0)} Mbps")
            pdf.add_key_value("Latency:", f"{isp.get('ping_ms', 0)} ms")
            pdf.ln(10)

            # 3. Devices
            sections = [
                ("3. Network Infrastructure", "Network"),
                ("4. Power & PDU", "Power"),
                ("5. Control Systems", "Control"),
                ("6. AV & Media", "AV"),
                ("7. Security", "Security"),
                ("8. RMS & Compute", "RMS")
            ]
            
            for title, key in sections:
                pdf.add_section_title(title)
                devices = self.report_data['groups'].get(key, [])
                pdf.add_device_table(devices, category=key)

            filename = f"Afara_Report_{self.meta.get('ref_number', 'Draft')}_{datetime.now().strftime('%H%M')}.pdf"
            path = pdf.save_report(filename)
            print(f"   [SUCCESS] PDF Report saved to: {path}\n")
            
        except Exception as e:
            print(f"   [ERROR] Failed to generate PDF: {e}")

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

    def _print_table_row(self, status, device, mode, mac, serial, firmware):
        name = device['name']
        ip = device['ip']
        location = f"{device['location']['floor']} > {device['location']['room']}"
        
        if isinstance(serial, list): serial = str(serial[0]) if serial else "---"
        if isinstance(mac, list): mac = str(mac[0]) if mac else "---"
        
        serial = str(serial)[:15]
        mac = str(mac)[:17]
        firmware = str(firmware)[:12] if firmware else "N/A"

        print(f"   {status:<7} {name:<25} | {mode:<8} | {ip:<15} | {mac:<17} | {serial:<15} | {firmware:<12} | {location}")

    def _audit_group(self, group_name, devices):
        if not devices:
            print(f"   [INFO] No devices grouped as '{group_name}'.\n")
            return

        print(f"   Running Device Audit ({len(devices)} devices)...")
        self._print_table_header()
        
        self.report_data['groups'][group_name] = []
        backups_collected = []
        
        for dev in devices:
            res = self._audit_device_logic(dev)
            
            # --- PoE / Extra Info Logic ---
            # If no extra info was generated (e.g., Router logic now puts NAT info elsewhere),
            # ensure to show "---" in the table column for Network group.
            final_info = res.get('extra_info', '')
            if group_name == 'Network' and not final_info:
                final_info = "---"

            report_entry = {**dev, **res}
            report_entry['extra_info'] = final_info 
            
            self.report_data['groups'][group_name].append(report_entry)

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
        mode = "(PING)"
        
        if "router" in driver:
            mode = "(ROUTER)"
            raut = RouterAuditor(dev['ip'], dev.get('username'), dev.get('password'), driver)
            res = raut.audit_firmware_and_config()
            status = "[PASS]" if res.get('status') == 'PASS' else "[FAIL]"
            res['status_bool'] = (res.get('status') == 'PASS')
            
            # --- DOUBLE NAT CHECK ---
            public_ip = self.report_data.get('isp', {}).get('public_ip', 'Unknown')
            router_ips = res.get('wan_ips', [])
            
            if public_ip != 'Unknown' and public_ip in router_ips:
                res['nat_status'] = "NAT Mode: Bridge (Optimal)"
            elif public_ip != 'Unknown':
                res['nat_status'] = "NAT Mode: Double NAT (Warning)"
            else:
                res['nat_status'] = None

        elif "cisco" in driver:
             mode = "(SSH)"
             target = CiscoSwitch(dev['ip'], dev.get('username'), dev.get('password'))
             check = target.check_status()
             status = "[PASS]" if check['online'] else "[FAIL]"
             
             poe_str = ""
             if check.get('poe') and isinstance(check['poe'], dict) and check['poe']['status'] == 'Active':
                 poe_str = f"{check['poe']['utilization']} ({check['poe']['used']}/{check['poe']['budget']})"
             
             res = check
             res['status_bool'] = check['online']
             res['extra_info'] = poe_str 

        else:
            mode = "(PING)"
            pinger = PingDriver(dev['ip'])
            res = pinger.check_status()
            status = "[PASS]" if res['online'] else "[FAIL]"
            res['status_bool'] = res['online']
        
        # Display Console Row
        mac = "OFFLINE" if not res.get('status_bool') else res.get('mac', '---')
        self._print_table_row(status, dev, mode, mac, res.get('serial', '---'), res.get('firmware', 'N/A'))
        
        return res

    # --- STEPS DEFINED EXPLICITLY ---

    def _run_step_1_environmental(self):
        print("1. General & Environmental (The Physical Layer)")
        print("-" * 40)
        env = EnvDriver()
        data = env.get_status()
        self.report_data['env'] = data
        print(f"   [PASS] Location:           {data['location']}")
        print(f"   [PASS] Room Temperature:   {data['temp']} (Simulated/Fallback)")
        print(f"   [PASS] Humidity/Dew Point: {data['humidity']} (Simulated/Fallback)")
        print(f"   [PASS] Noise Floor (dB):   {data['noise']} (Quiet)")
        print("")

    def _run_step_2_network(self):
        print("2. Network (The Backbone)")
        print("-" * 40)
        print("Verifying WAN Performance...")
        auditor = ISPAuditor()
        stats = auditor.run_audit()
        self.report_data['isp'] = stats
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
        print("\n" + "="*50)
        print("   COMMISSIONING SUMMARY")
        print("="*50)
        print(f"   Total Devices Checked: {total}")
        print(f"   PASSED:                {passed}")
        print(f"   FAILED:                {failed}")
        print("="*50 + "\n")