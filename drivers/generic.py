import platform
import subprocess
import socket

class GenericDevice:
    def __init__(self, ip):
        """
        Initialize the device driver. 
        We only need the IP to perform a ping.
        """
        self.ip = ip

    def check_status(self):
        """
        Pings the target IP to verify network connectivity.
        Returns: True (Online) | False (Offline)
        """
        try:
            # Determine the OS (Windows uses -n, Linux/Mac uses -c)
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            
            # Build the ping command
            # -n 1: Send only 1 packet
            # -w 1000: Timeout after 1000ms (1 second) to keep the loop fast
            command = ['ping', param, '1', self.ip]
            
            # Windows requires explicit timeout flags for ping
            if platform.system().lower() == 'windows':
                 command.extend(['-w', '1000'])
            
            # Run the command silently (stdout=DEVNULL hides the text output)
            response = subprocess.call(
                command, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            # If response is 0, the ping was successful
            return response == 0
            
        except Exception as e:
            print(f"[DRIVER ERROR] Ping failed for {self.ip}: {e}")
            return False