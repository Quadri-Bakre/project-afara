import os
import datetime

class SystemLogger:
    def __init__(self, log_dir="logs"):
        # Ensure log directory exists
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Create a unique filename based on today's date
        # Example: logs/report_2023-10-27.txt
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"report_{date_str}.txt")

    def log_failure(self, device_name, location, ip):
        """
        Appends a failure entry to the log file.
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] CRITICAL FAIL | Device: {device_name} ({ip}) | Loc: {location}\n"
        
        try:
            with open(self.log_file, "a") as f:
                f.write(entry)
        except Exception as e:
            print(f"[SYSTEM ERROR] Could not write to log file: {e}")

    def log_header(self, project_name):
        """
        Writes a session start separator to the file.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"SESSION START: {project_name} at {timestamp}\n")
                f.write(f"{'='*60}\n")
        except Exception as e:
            print(f"[SYSTEM ERROR] Could not write log header: {e}")