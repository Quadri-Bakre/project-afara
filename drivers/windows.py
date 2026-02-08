import paramiko
import re

class WindowsProbe:
    def __init__(self, ip, username, password, port=22):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.mode = "ssh" 

    def run(self):
        """
        Connects via SSH to Windows NUC and retrieves audit data.
        """
        data = {
            "status": "FAIL",
            "hostname": "Unknown",
            "ip": self.ip,
            "mac": "---",
            "serial": "---",
            "version": "Unknown", 
            "uptime": "Unknown",
            "mode": self.mode,   
            "error": None
        }

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # 1. CONNECT
            client.connect(
                self.ip, 
                port=self.port, 
                username=self.username, 
                password=self.password, 
                timeout=10
            )
            data["status"] = "PASS"

            # Helper for clean command execution
            def run_cmd(cmd):
                stdin, stdout, stderr = client.exec_command(cmd)
                return stdout.read().decode('utf-8', errors='ignore').strip()

            # 2. HOSTNAME
            data["hostname"] = run_cmd("hostname")

            # 3. OS VERSION
            os_out = run_cmd('systeminfo | findstr /B /C:"OS Name" /C:"OS Version"')
            os_name = "Win"
            os_ver = ""
            for line in os_out.splitlines():
                if "OS Name" in line: os_name = line.split(":", 1)[1].strip()
                elif "OS Version" in line: os_ver = line.split(":", 1)[1].strip()
            
            if os_name != "Win":
                data["version"] = f"{os_name} ({os_ver})"

            # 4. SERIAL NUMBER
            ps_serial = 'powershell -Command "(Get-CimInstance -ClassName Win32_BIOS).SerialNumber"'
            serial_out = run_cmd(ps_serial)

            if not serial_out or "not recognized" in serial_out or "command not found" in serial_out:
                serial_out = run_cmd("wmic bios get serialnumber").replace("SerialNumber", "").strip()

            data["serial"] = serial_out if serial_out else "Not Found"

            # 5. UPTIME
            # Calculates uptime via PowerShell and formats it as "Xd Yh Zm"
            ps_uptime = "powershell -Command \"$t = New-TimeSpan -Start (Get-CimInstance Win32_OperatingSystem).LastBootUpTime; '{0}d {1}h {2}m' -f $t.Days, $t.Hours, $t.Minutes\""
            uptime_out = run_cmd(ps_uptime)
            
            if uptime_out and "Days" not in uptime_out:
                 data["uptime"] = uptime_out

            # 6. MAC ADDRESS
            mac_out = run_cmd("getmac /fo csv /nh")
            mac_match = re.search(r"([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})", mac_out, re.IGNORECASE)
            if mac_match:
                data["mac"] = mac_match.group(1).replace("-", ":")

            client.close()

        except Exception as e:
            data["error"] = str(e)
            data["status"] = "FAIL"

        return data