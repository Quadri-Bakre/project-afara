import yaml
import os

def load_project_topology(yaml_path):
    """
    Parses the YAML topology file and flattens the hierarchy into a linear list of devices.
    Performs metadata normalization for downstream compatibility.
    """
    # Validate file existence
    if not os.path.exists(yaml_path):
        print(f"[ERROR] Topology file not found: {yaml_path}")
        return {'name': 'Unknown Project'}, []

    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[ERROR] Failed to parse YAML: {e}")
        return {'name': 'Error Loading Project'}, []

    # Normalize project metadata key to 'name' for consumer compatibility
    if 'name' not in data:
        data['name'] = data.get('project_name', 'Project Afara')

    devices = []
    
    # Flatten topology hierarchy (Floor -> Section -> Room -> Devices)
    for floor in data.get('topology', []):
        floor_name = floor.get('floor', 'Unknown')
        
        for section in floor.get('sections', []):
            area_type = section.get('type', 'Unknown')
            
            for room in section.get('rooms', []):
                room_name = room.get('name', 'Unknown')
                
                for device in room.get('devices', []):
                    # Create isolated copy to prevent mutation of source data
                    clean_device = device.copy()
                    
                    # Inject location context
                    clean_device['location'] = {
                        'floor': floor_name,
                        'area': area_type,
                        'room': room_name
                    }
                    
                    devices.append(clean_device)
    
    return data, devices