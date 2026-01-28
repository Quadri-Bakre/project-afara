import yaml
import os
import sys

def load_project_topology(file_path):
    """
    Reads the project YAML file and flattens the hierarchy into a list of devices.
    Returns a tuple: (project_metadata, device_list)
    """
    # 1. Validate File Exists
    if not os.path.exists(file_path):
        print(f"[ERROR] Configuration file not found at: {file_path}")
        return None, []

    try:
        # 2. Load the YAML data
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)

        project_meta = {
            "name": data.get("project_name", "Unknown Project"),
            "code": data.get("site_code", "UNKNOWN")
        }

        devices = []
        topology = data.get("topology", [])

        print(f"--- PARSING PROJECT: {project_meta['name']} ---")

        # 3. Crawl through the nested structure (Floors -> Rooms -> Devices)
        for floor in topology:
            floor_name = floor.get("floor", "Unknown Floor")
            
            for section in floor.get("sections", []):
                section_type = section.get("type", "General")
                
                for room in section.get("rooms", []):
                    room_name = room.get("name", "Unknown Room")
                    
                    for device in room.get("devices", []):
                        # Create the flattened device object
                        device_entry = {
                            "name": device.get("name"),
                            "ip": device.get("ip"),
                            "driver": device.get("driver"),
                            "critical": device.get("critical", False),
                            # Attach location data so we know where this device is
                            "location": {
                                "floor": floor_name,
                                "section": section_type,
                                "room": room_name
                            }
                        }
                        devices.append(device_entry)

        print(f"--- SUCCESSFULLY LOADED {len(devices)} ASSETS ---")
        return project_meta, devices

    except yaml.YAMLError as exc:
        print(f"[CRITICAL] Error parsing YAML file: {exc}")
        sys.exit(1)
    except Exception as e:
        print(f"[CRITICAL] Unexpected error loading topology: {e}")
        sys.exit(1)

# --- TEST BLOCK ---
if __name__ == "__main__":
    # INTELLIGENT PATH FINDER
    # This block calculates the absolute path to 'templates' based on where this script lives.
    
    # 1. Get the folder where THIS script (loader.py) is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Go up one level (to project-afara root) and then down into templates
    project_root = os.path.dirname(current_dir)
    test_path = os.path.join(project_root, 'templates', 'project_demo.yaml')
    
    print(f"Looking for file at: {test_path}")
    
    # 3. Run the loader
    meta, devs = load_project_topology(test_path)
    
    if devs:
        print("\n[RESULT] Parser is working! Here is the first device found:")
        first = devs[0]
        print(f"  - Device: {first['name']}")
        print(f"  - IP: {first['ip']}")
        print(f"  - Location: {first['location']['floor']} > {first['location']['room']}")