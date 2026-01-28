import time
import os
import datetime
from dotenv import load_dotenv

# Import core modules
from core.loader import load_project_topology
from core.logger import SystemLogger
from drivers.generic import GenericDevice
from drivers.loxone import LoxoneManager

# Load Credentials
load_dotenv()

def main():
    print("\n" + "="*50)
    print("   PROJECT AFARA: PHASE 5 (LOGGING ENGINE)")
    print("="*50 + "\n")

    # 1. SETUP: Initialize Logger and Paths
    logger = SystemLogger() # Initialize the logging system
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'templates', 'project_demo.yaml')
    
    # 2. LOAD: Read the Digital Twin (YAML)
    project_meta, devices = load_project_topology(yaml_path)

    if not devices:
        print("[ERROR] No devices found in template. Exiting.")
        return

    # Log the start of this session to the text file
    logger.log_header(project_meta['name'])
    
    print(f"\n[START] Monitoring {len(devices)} assets for {project_meta['name']}...\n")

    # 3. LOOP: Continuous Monitoring Cycle
    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"--- Scan Cycle: {timestamp} ---")
            
            critical_errors = []

            for device in devices:
                name = device['name']
                ip = device['ip']
                location = f"{device['location']['floor']} > {device['location']['room']}"
                is_critical = device['critical']

                # --- DRIVER SELECTION ---
                target = GenericDevice(ip)
                is_online = target.check_status()

                # --- REPORTING ---
                if is_online:
                    print(f"   [PASS] {name:<25} | {location}")
                else:
                    status_msg = f"   [FAIL] {name:<25} | {location} (OFFLINE)"
                    print(status_msg)
                    
                    if is_critical:
                        # 1. Add to screen report
                        critical_errors.append(f"{name} | {location}")
                        
                        # 2. Write to permanent log file <--- NEW
                        logger.log_failure(name, location, ip)

            # 4. SUMMARY: Process Critical Failures
            if critical_errors:
                print("\n   !!! CRITICAL FAILURE REPORT !!!")
                print(f"   [SAVED] {len(critical_errors)} errors written to logs/")
            
            print("-" * 40)
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n[STOP] Commissioning Engine halted by user.")

if __name__ == "__main__":
    main()