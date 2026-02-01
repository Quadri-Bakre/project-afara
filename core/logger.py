import logging
import os
import datetime

class SystemLogger:
    def __init__(self, log_dir="logs"):
        # 1. log directory must exist
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 2. Generate daily log filename
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"report_{date_str}.txt")

        # 3. Setup the native Python logger
        self.logger = logging.getLogger("AfaraSystem")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Prevent double logging if attached to root

        # 4. Adding File Handler (if not already added to avoid duplicates)
        if not self.logger.handlers:
            fh = logging.FileHandler(self.log_file)
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def info(self, message):
        """
        Logs an INFO message to file and prints to console.
        Usage: logger.info("Starting audit...")
        """
        self.logger.info(message)
        print(f"[INFO] {message}")

    def error(self, message):
        """
        Logs an ERROR message to file and prints to console.
        Usage: logger.error("Connection failed")
        """
        self.logger.error(message)
        print(f"[ERROR] {message}")

    def log_header(self, project_name):
        """
        Writes session delimiter and metadata to the log file.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.info("="*60)
        self.info(f"SESSION START: {project_name} at {timestamp}")
        self.info("="*60)

    def log_failure(self, device_name, location, ip):
        """
        Appends failure event details to the persistent log.
        """
        msg = f"CRITICAL FAIL | Device: {device_name} ({ip}) | Loc: {location}"
        self.error(msg)