import os
import time
import platform

# --- NETWORK CONFIGURATION ---
# Inventory of critical cyber-physical infrastructure
# Loop through ALL IPs
NETWORK_MAP = {
    # 1. Control4 (Confirmed)
    "Control4_Controller": "192.168.1.110",
    
    # 2. Loxone (Confirmed)
    "Loxone_Miniserver": "192.168.1.100",
    
    # 3. Cisco CML Switch (Real IP and Hostname)
    "afara-switch-01": "192.168.1.150", 
    
    # 4. Crestron Mock Server (Runs on Localhost)
    "Crestron_Mock_Server": "127.0.0.1",
    
    # 5. Local System Check (Self-audit)
    "Local_System": "127.0.0.1"
}

LOG_FILE = "status_log.txt"

def ping_device(ip):
    """
    Executes an ICMP echo request to verify device reachability.
    Platform agnostic (handles Windows/Linux syntax differences).
    """
    # Windows uses '-n 1', Unix-based systems use '-c 1'
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Construct command and suppress output (quiet mode)
    if platform.system().lower() == 'windows':
        command = f"ping {param} 1 {ip} > nul 2>&1"
    else:
        command = f"ping {param} 1 {ip} > /dev/null 2>&1"
        
    # Execute (Returns 0 for Success)
    response = os.system(command)
    return response == 0

def execute_audit():
    """
    Iterates through the NETWORK_MAP.
    1. Pings the target IP.
    2. Prints status to console (for the Operator).
    3. Saves status to 'status_log.txt' (for Evidence).
    """
    timestamp = time.ctime()
    print(f"[SYSTEM] Initiating Network Audit: {timestamp}")
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"\n--- AUDIT RECORD: {timestamp} ---\n")
            
            for name, ip in NETWORK_MAP.items():
                is_online = ping_device(ip)
                status = "ONLINE" if is_online else "OFFLINE"
                
                # Console Output
                print(f"   > {name:<25} ({ip}): {status}")
                
                # Persistent Logging
                f.write(f"{name} ({ip}) : {status}\n")

        print(f"[SUCCESS] Audit complete. Data persisted to {LOG_FILE}")
        
    except IOError as e:
        print(f"[ERROR] Failed to write to log file: {e}")

if __name__ == "__main__":
    execute_audit()