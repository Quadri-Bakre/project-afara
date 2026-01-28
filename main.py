import time
import os
import datetime
from dotenv import load_dotenv

# Import core modules
from core.loader import load_project_topology
from core.logger import SystemLogger
from drivers.generic import GenericDevice
from drivers.loxone import LoxoneManager
from drivers.cisco import CiscoSwitch

# Load Credentials
load_dotenv()

def main():
    print("\n" + "="*50)
    print("   PROJECT AFARA: PHASE 6 (UNIFORM GRID REPORTING)")
    print("="*50 + "\n")

    logger = SystemLogger()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'templates', 'project_demo.yaml')
    project_meta, devices = load_project_topology(yaml_path)

    if not devices:
        print("[ERROR] No devices found. Exiting.")
        return

    logger.log_header(project_meta['name'])
    print(f"\n[START] Monitoring {len(devices)} assets...\n")

    # Define Header String (kept outside loop for cleanliness)
    header = f"   {'STATUS':<7} {'NAME':<25} | {'MODE':<8} | {'IP ADDRESS':<15} | {'MAC ADDRESS':<17} | {'SERIAL':<15} | LOCATION"
    separator = "   " + "-"*120

    try:
        while True:
            # 1. Print Timestamp (Top of the Block)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"\n--- Scan Cycle: {timestamp} ---")
            
            # 2. Print Header (Every Cycle)
            print(header)
            print(separator)
            
            critical_errors = []

            for device in devices:
                name = device['name']
                ip = device['ip']
                driver_type = device['driver']
                location = f"{device['location']['floor']} > {device['location']['room']}"
                is_critical = device['critical']

                target = None
                if driver_type == "cisco":
                    target = CiscoSwitch(ip)
                elif driver_type == "loxone":
                    target = GenericDevice(ip)
                else:
                    target = GenericDevice(ip)

                # --- CHECK STATUS ---
                result = target.check_status()
                is_online = result['online']
                
                # Extract Data
                serial = result.get('serial', '---')
                mac = result.get('mac', '---')
                
                # Determine Mode Tag
                mode_tag = "(SSH)" if driver_type == "cisco" else "(PING)"

                # --- PRINTING ---
                if is_online:
                    print(f"   [PASS] {name:<25} | {mode_tag:<8} | {ip:<15} | {mac:<17} | {serial:<15} | {location}")
                else:
                    fail_mac = "OFFLINE"
                    fail_serial = "---"
                    print(f"   [FAIL] {name:<25} | {mode_tag:<8} | {ip:<15} | {fail_mac:<17} | {fail_serial:<15} | {location}")
                    
                    if is_critical:
                        critical_errors.append(f"{name} | {location}")
                        logger.log_failure(name, location, ip)

            if critical_errors:
                print(f"\n   !!! CRITICAL FAILURES: {len(critical_errors)} !!!")
            
            # Pause before next clear cycle
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n[STOP] Halting Engine.")

if __name__ == "__main__":
    main()