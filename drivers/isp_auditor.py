import speedtest
import json
import logging
from datetime import datetime

# Configure module-level logger
logger = logging.getLogger("Afara.ISP")

class ISPAuditor:
    def __init__(self):
        self.results = {}
        try:
            logger.info("Initializing Speedtest client...")
            self.st = speedtest.Speedtest()
        except Exception as e:
            logger.error(f"Failed to initialize Speedtest: {e}")
            self.st = None

    def run_audit(self):
        """
        Runs a full WAN performance audit: Download, Upload, Ping, and Public IP.
        """
        if not self.st:
            return {"error": "Speedtest client not initialized"}

        logger.info("Selecting best server based on ping...")
        self.st.get_best_server()

        logger.info("Running Download Test...")
        download_speed = self.st.download() / 1_000_000  # Convert bits to Mbps

        logger.info("Running Upload Test...")
        upload_speed = self.st.upload() / 1_000_000  # Convert bits to Mbps

        # Get metadata
        ping = self.st.results.ping
        client_info = self.st.results.client  # Contains Public IP, ISP Name
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.results = {
            "timestamp": timestamp,
            "isp_name": client_info.get("isp", "Unknown"),
            "public_ip": client_info.get("ip", "Unknown"),
            "country": client_info.get("country", "Unknown"),
            "download_mbps": round(download_speed, 2),
            "upload_mbps": round(upload_speed, 2),
            "ping_ms": round(ping, 2),
            "status": "PASS" if download_speed > 50 else "WARN_LOW_SPEED" # Example threshold
        }

        self._log_results()
        return self.results

    def _log_results(self):
        """
        Formats the output for the Commissioning Report.
        """
        r = self.results
        logger.info(f"--- ISP AUDIT COMPLETE ---")
        logger.info(f"Provider:  {r['isp_name']} ({r['country']})")
        logger.info(f"Public IP: {r['public_ip']}")
        logger.info(f"Download:  {r['download_mbps']} Mbps")
        logger.info(f"Upload:    {r['upload_mbps']} Mbps")
        logger.info(f"Latency:   {r['ping_ms']} ms")
        logger.info("--------------------------")

    def get_report_json(self):
        """Returns the data structure for the PDF generator."""
        return self.results

if __name__ == "__main__":
    # Self-test block
    logging.basicConfig(level=logging.INFO)
    auditor = ISPAuditor()
    print(json.dumps(auditor.run_audit(), indent=4))