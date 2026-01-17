import socket
import os
from dotenv import load_dotenv

# Load local configuration secrets
load_dotenv()

class Control4Manager:
    """
    Controller class for interacting with Control4 via Generic TCP Driver.
    """
    def __init__(self):
        self.ip = os.getenv("CONTROL4_IP")
        # Standard port for Generic TCP driver (usually 5000, 6000, or 8080)
        # We will assume 5000 for now.
        self.port = int(os.getenv("CONTROL4_PORT", 5000))

    def send_command(self, command):
        """
        Opens a socket, sends a command string, and closes the connection.
        """
        if not self.ip:
            print("[!] Error: CONTROL4_IP not set in .env")
            return False

        print(f"[*] Connecting to Control4 Controller ({self.ip}:{self.port})...")
        
        try:
            # Create a TCP/IP socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5) # Don't hang forever
                s.connect((self.ip, self.port))
                
                # Send data (Must be encoded to bytes)
                print(f"[*] Sending Command: {command}")
                s.sendall(command.encode('utf-8'))
                
                # Optional: Wait for acknowledgment from C4
                # response = s.recv(1024)
                # print(f"[+] Received: {response.decode('utf-8')}")
                
            print("[+] Command transmission complete.")
            return True

        except ConnectionRefusedError:
            print(f"[!] Connection Refused. Is the Generic TCP Driver listening on port {self.port}?")
            return False
        except socket.timeout:
            print(f"[!] Timeout. Control4 EA-1 did not respond.")
            return False
        except Exception as e:
            print(f"[!] Error: {e}")
            return False

if __name__ == "__main__":
    # Test Payload
    c4 = Control4Manager()
    c4.send_command("LIGHT_ON")