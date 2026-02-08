import time
import os
import datetime
from dotenv import load_dotenv

# Import Core Modules
from core.loader import load_project_topology
from core.logger import SystemLogger
from core.orchestrator import CommissioningOrchestrator

# Import Drivers
from drivers.cisco import CiscoSwitch
from drivers.ping_driver import PingDriver 
from drivers.gude_driver import GudeAuditor
from drivers.crestron_driver import CrestronAuditor

load_dotenv()

def main():
    logger = SystemLogger()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'templates', 'project_demo.yaml')
    
    project_meta, devices = load_project_topology(yaml_path)

    if not devices:
        print("[ERROR] No devices found in Excel. Exiting.")
        return

    logger.log_header(project_meta.get('name', 'Project Afara'))
    
    # ==================================================
    # COMMISSIONING (Run Audit & Cache Data)
    # ==================================================
    try:
        orchestrator = CommissioningOrchestrator(project_meta, devices)
        # Update devices list with cached serials/macs
        devices = orchestrator.run_full_sequence() 
    except KeyboardInterrupt:
        print("\n\n[STOP] Commissioning sequence aborted by user.")
        return
    except Exception as e:
        print(f"\n[ERROR] Orchestrator crashed: {e}")
        return
    
    # ==================================================
    # LIVE MONITORING
    # ==================================================
    print(f"[START] Entering Live Monitoring Mode for {len(devices)} assets...\n")
    
    header = f"   {'STATUS':<7} {'NAME':<25} | {'MODE':<8} | {'IP ADDRESS':<15} | {'MAC ADDRESS':<17} | {'SERIAL':<15} | {'FIRMWARE':<10} | LOCATION"
    separator = "   " + "-"*135

    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"\n--- Scan Cycle: {timestamp} ---")
            print(header)
            print(separator)
            
            for device in devices:
                name = device['name']
                ip = device['ip']
                driver_type = device['driver'].lower()
                group = device.get('group', '').lower()
                location = f"{device['location']['floor']} > {device['location']['room']}"
                
                target = None
                mode_tag = "(PING)"
                res = {}

                # 1. GUDE (HTTP)
                if "gude" in driver_type:
                     mode_tag = "(HTTP)"
                     target = GudeAuditor(ip, device.get('username'), device.get('password'))
                     full_audit = target.audit_firmware_and_config()
                     res = {
                         'online': (full_audit.get('status') == 'PASS'),
                         'mac': full_audit.get('mac'),
                         'serial': full_audit.get('serial'),
                         'firmware': full_audit.get('firmware')
                     }

                # 2. CRESTRON (SSH)
                elif "crestron" in driver_type:
                     mode_tag = "(SSH)"
                     target = CrestronAuditor(ip, device.get('username'), device.get('password'))
                     full_audit = target.audit_firmware_and_config()
                     res = {
                         'online': (full_audit.get('status') == 'PASS'),
                         'mac': full_audit.get('mac'),
                         'serial': full_audit.get('serial'),
                         'firmware': full_audit.get('firmware')
                     }

                # 3. CISCO (SSH)
                elif "cisco" in driver_type and "switch" in driver_type:
                     target = CiscoSwitch(ip, device.get('username'), device.get('password'))
                     mode_tag = "(SSH)"
                     res = target.check_status()

                # 4. DEFAULT (PING)
                else:
                     target = PingDriver(ip)
                     mode_tag = "(PING)"
                     res = target.check_status()

                # DATA DISPLAY LOGIC
                is_online = res.get('online', False)
                status = "[PASS]" if is_online else "[FAIL]"
                
                # Fetch Persistent Info (Cached from Commissioning Step)
                # This ensures info gathered during startup is shown even in Ping mode
                mac = res.get('mac') or device.get('mac', '---')
                serial = res.get('serial') or device.get('serial', '---')
                firmware = res.get('firmware') or device.get('firmware', 'N/A')

                # Normalize Strings
                if isinstance(mac, list): mac = str(mac[0])
                if isinstance(serial, list): serial = str(serial[0])
                
                if not is_online:
                    mac = "OFFLINE"
                    if res.get('error'): mac = str(res['error'])[:17]
                
                print(f"   {status:<7} {name:<25} | {mode_tag:<8} | {ip:<15} | {str(mac)[:17]:<17} | {str(serial)[:15]:<15} | {str(firmware)[:10]:<10} | {location}")
            
            time.sleep(15)

    except KeyboardInterrupt:
        print("\n\n[STOP] Halting Engine. Goodbye.")

if __name__ == "__main__":
    main()