import pandas as pd
import yaml
import os

# Base directory configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(BASE_DIR, 'project_schedule.xlsx')
YAML_PATH = os.path.join(BASE_DIR, 'templates', 'project_demo.yaml')

def create_template():
    """
    Initializes a blank Excel schema if the source file is missing.
    Populates headers including credential fields for secure access.
    """
    headers = [
        "Device Name", 
        "IP Address", 
        "Driver (cisco/crestron/loxone/generic)", 
        "Critical (True/False)", 
        "Floor", 
        "Area Type (Internal/External)", 
        "Room Name",
        "Username",  # Credential support
        "Password"   # Credential support
    ]
    
    # Seed data for immediate schema validation
    data = [
        ["Main_Rack_Switch", "192.168.1.150", "cisco", True, "Ground Floor", "Internal", "Plant Room", "admin", "P521P@s5w0rd"],
        ["Cinema_NVX", "192.168.1.101", "crestron", True, "Ground Floor", "Internal", "Cinema", "", ""],
        ["Garden_CCTV", "192.168.1.201", "generic", False, "Ground Floor", "External", "Garden South", "", ""],
    ]

    df = pd.DataFrame(data, columns=headers)
    df.to_excel(EXCEL_PATH, index=False)
    print(f"[SUCCESS] Schema initialized at: {EXCEL_PATH}")

def convert_excel_to_yaml():
    """
    ETL Process: Extracts device inventory from Excel, transforms it into 
    a hierarchical topology, and loads it into the YAML configuration engine.
    """
    if not os.path.exists(EXCEL_PATH):
        print(f"[ERROR] Source file missing: {EXCEL_PATH}")
        return

    print(f"[READING] {EXCEL_PATH}...")
    
    # Load source data; fillna prevents NaN propagation into YAML
    df = pd.read_excel(EXCEL_PATH).fillna("")

    # Phase 1: Aggregation
    # Build a nested dictionary representing the physical topology:
    # structure[floor][area_type][room] = [device_list]
    structure = {}

    for index, row in df.iterrows():
        # Data sanitization
        name = str(row.get("Device Name", "")).strip()
        ip = str(row.get("IP Address", "")).strip()
        driver_raw = str(row.get("Driver (cisco/crestron/loxone/generic)", "")).strip().lower()
        
        # Driver mode resolution
        if "cisco" in driver_raw:
            driver = "(SSH)"
        elif "crestron" in driver_raw:
            driver = "(REST)"
        elif "ping" in driver_raw or "generic" in driver_raw:
            driver = "(PING)"
        else:
            driver = "(PING)" # Default fallback

        # Metadata extraction
        critical = bool(row.get("Critical (True/False)", False))
        floor = str(row.get("Floor", "Unknown")).strip()
        area = str(row.get("Area Type (Internal/External)", "Internal")).strip()
        room = str(row.get("Room Name", "General")).strip()

        # Credential extraction
        # Empty strings are converted to None for cleaner YAML representation (null)
        raw_user = str(row.get("Username", "")).strip()
        username = raw_user if raw_user else None

        raw_pass = str(row.get("Password", "")).strip()
        password = raw_pass if raw_pass else None

        # Validation: Ensure essential networking data exists
        if not name or not ip:
            continue

        # Hierarchy construction
        if floor not in structure:
            structure[floor] = {}
        if area not in structure[floor]:
            structure[floor][area] = {}
        if room not in structure[floor][area]:
            structure[floor][area][room] = []

        # Device object assembly
        structure[floor][area][room].append({
            "name": name,
            "ip": ip,
            "driver": driver_raw, # Retain raw driver for debugging
            "mode": driver,       # Operational mode
            "critical": critical,
            "username": username,
            "password": password
        })

    # Phase 2: Transformation
    # Convert aggregation structure into the engine-compliant list format
    topology_list = []
    
    for floor_name, areas in structure.items():
        floor_obj = {
            "floor": floor_name,
            "sections": []
        }
        
        for area_name, rooms in areas.items():
            section_obj = {
                "type": area_name,
                "rooms": []
            }
            
            for room_name, devices in rooms.items():
                room_obj = {
                    "name": room_name,
                    "devices": devices
                }
                section_obj["rooms"].append(room_obj)
            
            floor_obj["sections"].append(section_obj)
        
        topology_list.append(floor_obj)

    # Phase 3: Loading
    # Serialize the final topology object to YAML
    final_yaml = {
        "project_name": "Project Afara: Excel Generated",
        "site_code": "LDN-EXCEL-01",
        "topology": topology_list
    }

    with open(YAML_PATH, 'w') as f:
        # Disable sort_keys to preserve logical topological order
        yaml.dump(final_yaml, f, sort_keys=False, default_flow_style=False)
    
    print(f"[SUCCESS] Configuration generated: {YAML_PATH}")
    print(f"[INFO] Processed {len(df)} assets.")

if __name__ == "__main__":
    if not os.path.exists(EXCEL_PATH):
        create_template()
    else:
        convert_excel_to_yaml()