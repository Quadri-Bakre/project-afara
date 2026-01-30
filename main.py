import time
import os
import datetime
from dotenv import load_dotenv

# Import core modules
from core.loader import load_project_topology
from core.logger import SystemLogger

# Import Drivers
from drivers.loxone import LoxoneManager
from drivers.cisco import CiscoSwitch
from drivers.crestron import CrestronNVX  
from drivers.ping_driver import PingDriver 

# Load Credentials (still needed for fallbacks/environment variables)
load_dotenv()

def main():
    print("\n" + "="*50)
    print("   PROJECT AFARA: PHASE 7 (CRESTRON INTEGRATION)")
    print("="*50 + "\n")

    logger = SystemLogger()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'templates', 'project_demo.yaml')
    
    # Load topology (which now includes usernames/passwords from Excel)
    project_meta, devices = load_project_topology(yaml_path)

    if not devices:
        print("[ERROR] No devices found. Exiting.")
        return

    logger.log_header(project_meta['name'])
    print(f"\n[START] Monitoring {len(devices)} assets...\n")

    # Define Header String
    header = f"   {'STATUS':<7} {'NAME':<25} | {'MODE':<8} | {'IP ADDRESS':<15} | {'MAC ADDRESS':<17} | {'SERIAL':<15} | LOCATION"
    separator = "   " + "-"*120

    try:
        while True:
            # 1. Print Timestamp
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"\n--- Scan Cycle: {timestamp} ---")
            
            # 2. Print Header
            print(header)
            print(separator)
            
            critical_errors = []

            for device in devices:
                name = device['name']
                ip = device['ip']
                driver_type = device['driver']
                location = f"{device['location']['floor']} > {device['location']['room']}"
                is_critical = device['critical']
                
                # --- NEW: Extract Credentials from Excel Data ---
                username = device.get('username')
                password = device.get('password')

                # --- DRIVER SELECTION ---
                target = None
                mode_tag = "(PING)" # Default

                if "cisco" in driver_type:
                    # Pass the Excel credentials to the driver
                    target = CiscoSwitch(ip, username, password)
                    mode_tag = "(SSH)"
                elif "crestron" in driver_type:
                    target = CrestronNVX(ip)
                    mode_tag = "(REST)"
                elif "loxone" in driver_type:
                    target = LoxoneManager(ip, username, password)
                    mode_tag = "(REST)"
                else:
                    # Use the Mac-Compatible Ping Driver for everything else
                    target = PingDriver(ip)
                    mode_tag = "(PING)"

                # --- CHECK STATUS ---
                result = target.check_status()
                is_online = result['online']
                
                # Extract Data
                serial = result.get('serial', '---')
                mac = result.get('mac', '---')
                error_msg = result.get('error')

                # --- PRINTING ---
                if is_online:
                    print(f"   [PASS] {name:<25} | {mode_tag:<8} | {ip:<15} | {mac:<17} | {serial:<15} | {location}")
                else:
                    fail_mac = "OFFLINE"
                    fail_serial = "---"
                    
                    # If we have a specific error (like "Auth Failed"), show it in the MAC column
                    if error_msg and "Timeout" not in error_msg:
                        fail_mac = str(error_msg)[:17] # Truncate to fit column

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