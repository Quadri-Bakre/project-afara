import socket

# Configuration (Must match the mock_device_server.py settings)
TARGET_HOST = '127.0.0.1'
TARGET_PORT = 5001

def send_command(command):
    """
    Connects to the mock device, sends a command, and waits for a response.
    """
    try:
        # Create a socket object (IPv4, TCP)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            # Set a timeout (5 seconds) so we don't hang if the server is offline
            client.settimeout(5)
            
            # Connect to the server
            client.connect((TARGET_HOST, TARGET_PORT))
            
            # Send the command
            print(f"[>] Sending: {command}")
            client.sendall(command.encode())
            
            # Wait for the response (buffer size 1024 bytes)
            response = client.recv(1024)
            print(f"[<] Received: {response.decode()}")
            
    except ConnectionRefusedError:
        print(f"[!] Error: Could not connect to {TARGET_HOST}:{TARGET_PORT}. Is the server running?")
    except socket.timeout:
        print("[!] Error: Connection timed out.")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    print(f"--- Client Controller Online (Target: {TARGET_PORT}) ---")
    print("Type 'exit' to quit.\n")
    
    while True:
        # Get command from user
        user_input = input("Enter command to send: ")
        
        if user_input.lower() == 'exit':
            print("Exiting controller.")
            break
            
        if user_input.strip():
            send_command(user_input)