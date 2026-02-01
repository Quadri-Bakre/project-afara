import os
import yaml
import pandas as pd

def load_project_topology(yaml_path):
    # Default Defaults
    project_meta = {
        'name': 'Project Afara', 'ref_number': 'REF-0000',
        'address': 'Unknown Address', 'engineer': 'Unassigned', 'mode': 'Onsite'
    }
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
    excel_path = os.path.join(base_dir, 'project_schedule.xlsx')

    if not os.path.exists(excel_path):
        return project_meta, []

    # 1. METADATA (Project Info Tab)
    try:
        meta_df = pd.read_excel(excel_path, sheet_name='Project Info', header=None)
        for index, row in meta_df.iterrows():
            key = str(row[0]).lower().strip()
            val = str(row[1]).strip()
            if 'project name' in key: project_meta['name'] = val
            elif 'ref' in key: project_meta['ref_number'] = val
            elif 'address' in key: project_meta['address'] = val
            elif 'engineer' in key: project_meta['engineer'] = val
            elif 'mode' in key: project_meta['mode'] = val
    except: pass

    # 2. DEVICES (First Tab)
    devices = []
    try:
        df = pd.read_excel(excel_path, sheet_name=0)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        for index, row in df.iterrows():
            ip_col = next((c for c in df.columns if c in ['ip address', 'ip']), None)
            if not ip_col or pd.isna(row[ip_col]): continue

            name_col = next((c for c in df.columns if c in ['device name', 'name']), None)
            driver_col = next((c for c in df.columns if c in ['driver', 'type']), None)
            group_col = next((c for c in df.columns if c in ['group', 'category']), None)
            
            # --- LOCATION FIX ---
            floor_col = next((c for c in df.columns if 'floor' in c), None)
            room_col = next((c for c in df.columns if 'room' in c or 'area' in c), None)

            raw_driver = str(row[driver_col]).strip() if driver_col else "ping_driver"
            if raw_driver == 'nan': raw_driver = 'ping_driver'

            dev = {
                'name': str(row[name_col]) if name_col else "Unknown",
                'ip': str(row[ip_col]).strip(),
                'driver': raw_driver,
                'group': str(row[group_col]).strip().lower() if group_col else "general",
                'username': str(row.get('username', '')).strip(),
                'password': str(row.get('password', '')).strip(),
                'critical': False,
                'location': {
                    'floor': str(row[floor_col]) if floor_col else "Unknown",
                    'room': str(row[room_col]) if room_col else "Unknown"
                }
            }
            devices.append(dev)
    except Exception as e:
        print(f"[ERROR] Loader Error: {e}")

    return project_meta, devices