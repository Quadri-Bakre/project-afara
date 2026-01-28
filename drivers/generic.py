import socket
import subprocess
import platform

class GenericDevice:
    """
    Universal Driver for devices without specific APIs (Sky Q, Apple TV, etc).
    """
    def __init__(self, name, ip, check_port=None):
        self.name = name
        self.ip = ip
        self.check_port = check_port 

    def ping_device(self):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        try:
            return subprocess.call(['ping', param, '1', self.ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        except:
            return False

    def check_open_port(self):
        if not self.check_port: return True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((self.ip, self.check_port))
        sock.close()
        return result == 0

    def run_diagnostics(self):
        status = "PASS" if self.ping_device() else "FAIL"
        if self.check_port and status == "PASS":
            if not self.check_open_port(): status = "PARTIAL_FAIL"
        return {"device": self.name, "ip": self.ip, "status": status}