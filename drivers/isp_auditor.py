import speedtest
import logging
import socket
import time
import urllib.request

class ISPAuditor:
    def __init__(self):
        self.logger = logging.getLogger("Afara.ISP")

    def check_connectivity(self, host="8.8.8.8", port=53, timeout=3):
        """
        Simple check to see if we can reach the outside world.
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception:
            return False

    def _measure_http_speed(self):
        """
        Fallback: Downloads a 10MB file to calculate raw download speed.
        Returns: Speed in Mbps (float) or None if failed.
        """
        # Tele2 Speedtest Service (Open for public testing)
        url = "http://speedtest.tele2.net/10MB.zip" 
        try:
            start_time = time.time()
            # Download the file (timeout 15s)
            with urllib.request.urlopen(url, timeout=15) as response:
                data = response.read()
                file_size = len(data) # Size in bytes
                
            duration = time.time() - start_time
            
            # Calculate Mbps: (Bytes * 8 bits) / (Seconds * 1,000,000)
            speed_bps = (file_size * 8) / duration
            speed_mbps = speed_bps / 1_000_000
            
            return round(speed_mbps, 2)
        except Exception:
            return None

    def _get_public_ip(self):
        try:
            return urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode('utf8')
        except:
            return "Unknown"

    def run_audit(self):
        stats = {
            'isp_name': 'Unknown',
            'public_ip': 'Unknown',
            'download_mbps': 0.0,
            'upload_mbps': 0.0,
            'ping_ms': 0.0,
            'status': 'FAIL',
            'error': None
        }

        print("   > Contacting Speedtest Servers...")

        # --- ATTEMPT 1: OOKLA SPEEDTEST ---
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            
            # ISP Info
            config = st.get_config()
            stats['isp_name'] = config['client']['isp']
            stats['public_ip'] = config['client']['ip']
            
            # Speed
            print("   > Measuring Download Speed (Ookla)...")
            dl = st.download()
            print("   > Measuring Upload Speed (Ookla)...")
            ul = st.upload()
            
            stats['download_mbps'] = round(dl / 1_000_000, 2)
            stats['upload_mbps'] = round(ul / 1_000_000, 2)
            stats['ping_ms'] = round(st.results.ping, 1)
            stats['status'] = 'PASS'
            return stats

        except Exception as e:
            self.logger.warning(f"Ookla Failed ({e}). Switching to Fallback...")

        # --- ATTEMPT 2: HTTP DOWNLOAD FALLBACK ---
        print("   > Attempting HTTP Download Fallback...")
        http_speed = self._measure_http_speed()
        
        if http_speed:
            stats['download_mbps'] = http_speed
            stats['upload_mbps'] = "N/A" # HTTP test is download only
            stats['status'] = 'PASS (Fallback)'
            stats['isp_name'] = "Standard Connection"
            stats['public_ip'] = self._get_public_ip()
            stats['error'] = "Used HTTP Fallback (Ookla Blocked)"
            return stats

        # --- ATTEMPT 3: BASIC CONNECTIVITY ---
        if self.check_connectivity():
            stats['status'] = 'PASS (Basic)'
            stats['error'] = "Speedtest Failed (Internet OK)"
            stats['isp_name'] = "Connected"
            stats['public_ip'] = self._get_public_ip()
        else:
            stats['error'] = "No Internet Connection"

        return stats