import os
from datetime import datetime
from fpdf import FPDF

class PDFReporter(FPDF):
    def __init__(self, meta):
        # 'L' = Landscape, 'mm' = millimeters, 'A4' = page size
        super().__init__(orientation='L', unit='mm', format='A4')
        self.meta = meta
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()

    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, f"Project Afara - Commissioning Report: {self.meta.get('ref_number', 'N/A')}", 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def generate_cover(self):
        self.set_font('Arial', 'B', 24)
        self.ln(40)
        self.cell(0, 10, "COMMISSIONING CERTIFICATE", 0, 1, 'C')
        self.ln(10)
        
        self.set_font('Arial', '', 14)
        self.cell(0, 10, f"Project: {self.meta.get('address', 'Unknown Location')}", 0, 1, 'C')
        self.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
        self.cell(0, 10, f"Engineer: {self.meta.get('engineer', 'N/A')}", 0, 1, 'C')
        self.ln(30)
        self.add_page()

    def add_section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 1, 1, 'L', fill=True)
        self.ln(5)

    def add_key_value(self, key, value):
        self.set_font('Arial', 'B', 10)
        self.cell(40, 8, key, 0)
        self.set_font('Arial', '', 10)
        self.cell(0, 8, str(value), 0, 1)

    def add_device_table(self, devices, category="General"):
        if not devices:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, "No devices in this category.", 0, 1)
            self.ln(5)
            return

        # --- TABLE CONFIGURATION ---
        if category == "Network":
            widths = [15, 40, 28, 32, 45, 30, 35, 50] 
            headers = ["Status", "Name", "IP Addr", "MAC Addr", "Serial", "FW", "Location", "PoE Status"]
        else:
            widths = [15, 55, 35, 35, 50, 35, 50] 
            headers = ["Status", "Name", "IP Addr", "MAC Addr", "Serial", "FW", "Location"]

        # HEADER
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(240, 240, 240)
        for i, h in enumerate(headers):
            self.cell(widths[i], 8, h, 1, 0, 'C', fill=True)
        self.ln()

        # ROWS
        self.set_font('Arial', '', 7)
        for d in devices:
            status = "PASS" if d.get('status_bool') else "FAIL"
            
            name = d.get('name', 'N/A')[:35]
            ip = d.get('ip', 'N/A')
            
            mac = d.get('mac', '---')
            if isinstance(mac, list): mac = str(mac[0])
            
            serial = d.get('serial', '---')
            if isinstance(serial, list): serial = str(serial[0])
            
            fw = str(d.get('firmware', 'N/A'))[:20]
            
            loc_raw = d.get('location', {})
            location = f"{loc_raw.get('floor', '')} > {loc_raw.get('room', '')}"[:30]

            row_data = [status, name, ip, mac, serial, fw, location]

            if category == "Network":
                poe_status = d.get('extra_info', '')
                row_data.append(poe_status)

            # Draw Cells
            for i, data in enumerate(row_data):
                text = str(data)
                self.cell(widths[i], 8, text, 1, 0, 'L')
            self.ln()
        
        self.ln(5)

        # --- DIAGNOSTICS SUMMARY (NETWORK ONLY) ---
        if category == "Network":
            self._add_network_health_summary(devices)

    def _add_network_health_summary(self, devices):
        """Analyzes Uptime, Port Errors, VLANs, and NAT Status."""
        self.set_font('Arial', 'B', 9)
        self.cell(0, 8, "Diagnostics & Health Check for Online Devices:", 0, 1)
        
        has_warnings = False
        self.set_font('Arial', '', 8)

        for d in devices:
            # 1. Port Errors (Red)
            errors = d.get('port_errors', [])
            if errors and isinstance(errors, list) and len(errors) > 0:
                has_warnings = True
                self.set_text_color(200, 0, 0) 
                error_str = ", ".join(errors)
                self.cell(0, 6, f" [WARNING] {d['name']}: Detected Physical Layer Errors - {error_str}", 0, 1)
            
            # 2. Uptime (Green)
            uptime = d.get('uptime')
            if uptime and uptime != "N/A":
                self.set_text_color(0, 100, 0)
                self.cell(0, 6, f" [INFO] {d['name']} Uptime: {uptime}", 0, 1)

            # 3. VLAN Database (Blue)
            vlans = d.get('vlans')
            if vlans and isinstance(vlans, list) and len(vlans) > 0:
                self.set_text_color(0, 0, 150) # Dark Blue
                vlan_str = ", ".join(vlans[:15]) 
                if len(vlans) > 15: vlan_str += "..."
                self.cell(0, 6, f" [INFO] {d['name']} VLAN Database (Configured): {vlan_str}", 0, 1)

            # 4. NAT Status (Orange for Double NAT, Green for Bridge) - NEW
            nat = d.get('nat_status')
            if nat:
                if "Double" in nat:
                    self.set_text_color(200, 100, 0) # Orange
                    self.cell(0, 6, f" [WARNING] {d['name']}: {nat}", 0, 1)
                else:
                    self.set_text_color(0, 100, 0) # Green
                    self.cell(0, 6, f" [INFO] {d['name']}: {nat}", 0, 1)

        if not has_warnings:
            self.set_text_color(0, 0, 0) # Black
            self.cell(0, 6, " No physical cabling errors (CRC/Input drops) detected on any active ports.", 0, 1)
        
        # Reset color
        self.set_text_color(0, 0, 0) 
        self.ln(10)

    def save_report(self, filename="commissioning_report.pdf"):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        path = f"reports/{filename}"
        self.output(path)
        return path