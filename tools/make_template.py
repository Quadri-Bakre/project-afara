import pandas as pd

# 1. PROJECT INFO SHEET
info_data = {
    "Key": ["Project Name", "Ref Number", "Address", "Engineer", "Mode", "Date"],
    "Value": ["Project Afara Demo", "AF-001", "London, UK", "Quadri Bakre", "Onsite", "2026-02-08"]
}
df_info = pd.DataFrame(info_data)

# 2. DEVICES SHEET (Empty Template)
device_headers = ["Name", "IP", "Driver", "Username", "Password", "Group", "Floor", "Room", "Type"]
df_devices = pd.DataFrame(columns=device_headers)

# 3. KEYS / LEGEND SHEET (Merged Guide)
keys_data = {
    "Category": [
        "DRIVER TYPES", "DRIVER TYPES", 
        "DRIVER TYPES", 
        "DRIVER TYPES", 
        "DRIVER TYPES", 
        "DRIVER TYPES",
        "DRIVER TYPES",
        "", 
        "GROUPS", "GROUPS", "GROUPS", "GROUPS", "GROUPS", "GROUPS"
    ],
    "Keyword / Driver": [
        "draytek_router", "cisco_router", 
        "cisco_switch", 
        "gude_pdu", 
        "windows", 
        "crestron",
        "generic",
        "",
        "Network", "Power", "Control", "AV", "Security", "RMS"
    ],
    "Description": [
        "Use for DrayTek Vigor series. Audits WAN/ISP status.", 
        "Use for Cisco ISR/ASR routers. Audits WAN/ISP status.",
        "Use for Catalyst/Nexus switches. Audits VLANs and PoE.", 
        "Use for Gude PDUs (HTTP). Audits Voltage/Amps.", 
        "Use for Windows NUC/Server (SSH). Audits OS & Uptime.", 
        "Use for Crestron Processors (SSH). Audits connected devices.",
        "Use for non-smart devices (TVs, APs). Pings only.",
        "",
        "For Routers, Switches, Access Points.",
        "For PDUs, UPS, and Power meters.",
        "For Processors and Touch Panels.",
        "For Video Matrix, DSPs, TVs, and Projectors.",
        "For Cameras, NVRs, and Intercoms.",
        "For Servers, NUCs, and Virtual Machines."
    ]
}
df_keys = pd.DataFrame(keys_data)

# WRITE TO EXCEL
file_name = "template_project_schedule.xlsx"
with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
    df_info.to_excel(writer, sheet_name='Project Info', index=False)
    df_devices.to_excel(writer, sheet_name='Devices', index=False)
    df_keys.to_excel(writer, sheet_name='KEYS', index=False)

    # Adjust column widths for readability
    worksheet = writer.sheets['KEYS']
    worksheet.column_dimensions['A'].width = 15
    worksheet.column_dimensions['B'].width = 25
    worksheet.column_dimensions['C'].width = 60

print(f"Created {file_name} successfully!")