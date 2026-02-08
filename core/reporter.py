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
        headers = ["Status", "Name", "IP Addr", "MAC Addr", "Serial", "FW", "Location"]
        widths =  [15,       50,     30,        35,         35,       25,   50]

        # Add Specific Columns
        if category == "Network":
            headers.append("PoE Status")
            widths = [15, 40, 28, 32, 35, 25, 35, 50] 
        elif category == "Power":
            headers.append("Load (V/A)")
            widths = [15, 40, 28, 32, 35, 25, 35, 50] 

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
            
            name = str(d.get('name', 'N/A'))[:35]
            ip = str(d.get('ip', 'N/A'))
            
            mac = d.get('mac', '---')
            if isinstance(mac, list): mac = str(mac[0])
            
            serial = d.get('serial', '---')
            if isinstance(serial, list): serial = str(serial[0])
            
            fw = str(d.get('firmware', 'N/A'))[:20]
            
            loc_raw = d.get('location', {})
            location = f"{loc_raw.get('floor', '')} > {loc_raw.get('room', '')}"[:30]

            row_data = [status, name, ip, mac, serial, fw, location]

            if category == "Network" or category == "Power":
                extra = str(d.get('extra_info', '---'))
                row_data.append(extra)

            # Draw Cells
            for i, data in enumerate(row_data):
                self.cell(widths[i], 8, str(data), 1, 0, 'L')
            self.ln()
        
        self.ln(5)

        # --- DIAGNOSTICS SUMMARIES ---
        if category == "Network":
            self._add_network_health_summary(devices)
        elif category == "Power":
            self._add_power_health_summary(devices)

    def _add_network_health_summary(self, devices):
        """Restores the full network diagnostics block."""
        self.set_font('Arial', 'B', 9)
        self.cell(0, 8, "Diagnostics & Health Check for Online Devices:", 0, 1)
        self.set_font('Arial', '', 8)
        
        has_warnings = False

        for d in devices:
            # 1. NAT Status (Routers)
            nat = d.get('nat_status')
            if nat:
                if "Double" in nat:
                    self.set_text_color(200, 100, 0) # Orange
                    self.cell(0, 6, f" [WARNING] {d['name']}: {nat}", 0, 1)
                else:
                    self.set_text_color(0, 100, 0) # Green
                    self.cell(0, 6, f" [INFO] {d['name']}: {nat}", 0, 1)

            # 2. VLAN Database (Switches)
            vlans = d.get('vlans')
            if vlans and isinstance(vlans, list):
                self.set_text_color(0, 0, 150) # Blue
                v_str = ", ".join(vlans[:10])
                if len(vlans) > 10: v_str += "..."
                self.cell(0, 6, f" [INFO] {d['name']} VLAN Database (Configured): {v_str}", 0, 1)

            # 3. Port Errors (Switches)
            errors = d.get('port_errors')
            if errors and isinstance(errors, list):
                has_warnings = True
                self.set_text_color(200, 0, 0) # Red
                err_str = ", ".join(errors)
                self.cell(0, 6, f" [WARNING] {d['name']} Port Errors: {err_str}", 0, 1)

        # 4. Global Clean Bill of Health (if no specific errors found)
        if not has_warnings:
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, " No physical cabling errors (CRC/Input drops) detected on any active ports.", 0, 1)
        
        self.set_text_color(0, 0, 0) 
        self.ln(10)

    def _add_power_health_summary(self, devices):
        """New diagnostics block for Power/PDU."""
        self.set_font('Arial', 'B', 9)
        self.cell(0, 8, "Diagnostics & Power Load Analysis:", 0, 1)
        self.set_font('Arial', '', 8)

        for d in devices:
            # 1. Power Metrics
            metrics = d.get('power_metrics')
            if metrics and metrics != "N/A":
                # Parse current to see if we should warn (e.g., >14A on a 16A circuit)
                # Format is usually: "230V / 1.5A (345W)"
                is_high_load = False
                try:
                    # Simple heuristic: find 'A' and check number before it
                    import re
                    amp_match = re.search(r'/\s*([0-9\.]+)\s*A', metrics)
                    if amp_match and float(amp_match.group(1)) > 14.0:
                        is_high_load = True
                except: pass

                if is_high_load:
                    self.set_text_color(200, 0, 0) # Red
                    self.cell(0, 6, f" [WARNING] {d['name']} HIGH LOAD DETECTED: {metrics}", 0, 1)
                else:
                    self.set_text_color(0, 100, 0) # Green
                    self.cell(0, 6, f" [INFO] {d['name']} Input Load: {metrics}", 0, 1)

            # 2. Port Status (Summary)
            ports = d.get('port_status', [])
            if ports:
                on_count = sum(1 for p in ports if "ON" in p)
                off_count = sum(1 for p in ports if "OFF" in p)
                self.set_text_color(0, 0, 150) # Blue
                self.cell(0, 6, f" [INFO] {d['name']} Outlet Status: {on_count} ON / {off_count} OFF", 0, 1)

        self.set_text_color(0, 0, 0)
        self.ln(10)

    def save_report(self, filename="commissioning_report.pdf"):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        path = f"reports/{filename}"
        self.output(path)
        return path