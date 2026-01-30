import platform
import subprocess

class PingDriver:
    def __init__(self, ip):
        self.ip = ip

    def check_status(self):
        # Detect OS
        system = platform.system().lower()
        
        # Build Command
        if system == "windows":
            # Windows: -n 1 count, -w 1000ms timeout
            command = ["ping", "-n", "1", "-w", "1000", self.ip]
        elif system == "darwin": 
            # macOS: -c 1 count, -W 1000ms timeout (This is the fix!)
            command = ["ping", "-c", "1", "-W", "1000", self.ip]
        else:
            # Linux: -c 1 count, -W 1s timeout
            command = ["ping", "-c", "1", "-W", "1", self.ip]

        try:
            # Run silently
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            is_online = (result.returncode == 0)
            
            return {
                "online": is_online,
                "serial": "---",
                "mac": "ONLINE" if is_online else "OFFLINE",
                "error": None
            }
        except Exception as e:
            return {"online": False, "serial": "---", "mac": "ERR", "error": str(e)}