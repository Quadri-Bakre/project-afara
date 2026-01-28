import http.server
import socketserver
import re

# Port 5001 used (or any free port) so it doesn't clash with real web servers
PORT = 5001

class LoxoneMockHandler(http.server.SimpleHTTPRequestHandler):
    """
    Simulates a Loxone Miniserver REST API.
    Accepts commands like: /dev/sps/io/{VI_NAME}/{COMMAND}
    """
    def do_GET(self):
        # 1. Capture the Virtual Input Name and Command (On/Off/Pulse) from URL
        # Regex looks for pattern: /dev/sps/io/(anything)/(anything)
        match = re.search(r"/dev/sps/io/([^/]+)/([^/]+)", self.path)
        
        if match:
            vi_name = match.group(1)  # e.g., "V_input1"
            command = match.group(2)  # e.g., "On", "Off", "pulse"
            
            # 2. Log it to the console (Visual Feedback)
            print(f"\n[MOCK SERVER] -----------------------------")
            print(f"   Input Target: {vi_name}")
            print(f"   Action rcvd:  {command}")
            print(f"-------------------------------------------")
            
            # 3. Send fake XML success response (what Loxone would send)
            response_xml = f"""<LL control="dev/sps/io/{vi_name}/{command}" value="1" Code="200"/>"""
            
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.end_headers()
            self.wfile.write(response_xml.encode('utf-8'))
        else:
            # If URL is wrong
            self.send_error(404, "Not Found: Use format /dev/sps/io/{VI}/{CMD}")

print(f"--- VIRTUAL LOXONE ENVIRONMENT ---")
print(f"Status:  Running")
print(f"Address: http://127.0.0.1:{PORT}")
print(f"Action:  Waiting for Watchdog commands...")

with socketserver.TCPServer(("", PORT), LoxoneMockHandler) as httpd:
    httpd.serve_forever()