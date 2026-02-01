import time
import os
import datetime
from dotenv import load_dotenv

# Import Core Modules
from core.loader import load_project_topology
from core.logger import SystemLogger
from core.orchestrator import CommissioningOrchestrator
from drivers.cisco import CiscoSwitch
from drivers.ping_driver import PingDriver 

load_dotenv()

def main():
    logger = SystemLogger()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'templates', 'project_demo.yaml')
    
    # 1. Load Data (Reads Project Info + Devices from Excel)
    project_meta, devices = load_project_topology(yaml_path)

    if not devices:
        print("[ERROR] No devices found in Excel. Exiting.")
        return

    # Log the session start
    logger.log_header(project_meta.get('name', 'Project Afara'))
    
    # ==================================================
    # COMMISSIONING ORCHESTRATOR
    # ==================================================
    # This runs the "Master Spec" sequence
    try:
        orchestrator = CommissioningOrchestrator(project_meta, devices)
        orchestrator.run_full_sequence()
    except KeyboardInterrupt:
        print("\n\n[STOP] Commissioning sequence aborted by user.")
        return
    except Exception as e:
        print(f"\n[ERROR] Orchestrator crashed: {e}")
        return
    
    # ==================================================
    # LIVE MONITORING LOOP (Post-Commissioning)
    # ==================================================
    print(f"[START] Entering Live Monitoring Mode for {len(devices)} assets...\n")
    
    # Define Header String (Matched to Orchestrator with Firmware Column)
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
                
                location = f"{device['location']['floor']} > {device['location']['room']}"
                
                # --- Driver Selection ---
                target = None
                mode_tag = "(PING)"
                
                # Use CiscoSwitch for SSH if type is switch + cisco
                if "cisco" in driver_type and "switch" in driver_type:
                     target = CiscoSwitch(ip, device.get('username'), device.get('password'))
                     mode_tag = "(SSH)"
                else:
                     target = PingDriver(ip)
                     mode_tag = "(PING)"

                # --- Check Status ---
                res = target.check_status()
                
                # --- Format Data (Sanitize Lists to prevent crashes) ---
                is_online = res['online']
                status = "[PASS]" if is_online else "[FAIL]"
                
                mac = res.get('mac', '---')
                if isinstance(mac, list): mac = str(mac[0])
                
                serial = res.get('serial', '---')
                if isinstance(serial, list): serial = str(serial[0])
                
                # Firmware default for live loop
                firmware = "N/A"

                # Normalize length for table alignment
                mac = str(mac)[:17]
                serial = str(serial)[:15]

                if not is_online:
                    mac = "OFFLINE"
                    # If there's a specific error (like Auth Fail), show it instead of OFFLINE
                    if res.get('error'): 
                        mac = str(res['error'])[:17]
                
                # Print Row
                print(f"   {status:<7} {name:<25} | {mode_tag:<8} | {ip:<15} | {mac:<17} | {serial:<15} | {firmware:<10} | {location}")
            
            # Wait 15 seconds before next scan
            time.sleep(15)

    except KeyboardInterrupt:
        
        print("\n\n[STOP] Halting Engine. Goodbye.")

if __name__ == "__main__":
    main()