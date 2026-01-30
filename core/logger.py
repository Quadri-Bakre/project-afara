import os
import datetime

class SystemLogger:
    def __init__(self, log_dir="logs"):
        # Ensure log directory structure exists
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Generate daily log filename
        # Format: logs/report_YYYY-MM-DD.txt
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"report_{date_str}.txt")

    def log_failure(self, device_name, location, ip):
        """
        Appends failure event details to the persistent log.
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] CRITICAL FAIL | Device: {device_name} ({ip}) | Loc: {location}\n"
        
        try:
            with open(self.log_file, "a") as f:
                f.write(entry)
        except Exception as e:
            print(f"[SYSTEM ERROR] Write failure in log subsystem: {e}")

    def log_header(self, project_name):
        """
        Writes session delimiter and metadata to the log file.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"SESSION START: {project_name} at {timestamp}\n")
                f.write(f"{'='*60}\n")
        except Exception as e:
            print(f"[SYSTEM ERROR] Failed to write log header: {e}")