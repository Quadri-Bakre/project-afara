import socket
import threading

# Server Configuration
# '127.0.0.1' is the "Localhost" address (the computer talking to itself)
HOST = '127.0.0.1'
# Port 5001 is used to avoid conflicts with common macOS services like AirPlay (Port 5000)
PORT = 5001

def handle_client(conn, addr):
    """
    Handles the communication logic for a single connected client.
    Args:
        conn: The socket object for the connection.
        addr: The IP address and port of the client.
    """
    print(f"New connection established from {addr}")
    
    with conn:
        while True:
            # Receive up to 1024 bytes of data from the client
            data = conn.recv(1024)
            
            # If no data is received, the client has disconnected
            if not data:
                break
            
            # Decode bytes to string and strip whitespace
            command = data.decode().strip()
            print(f"Received command: {command}")
            
            # Simulate a device processing the command and sending an acknowledgement
            response = f"ACK: Processed command '{command}'".encode()
            conn.sendall(response)
    
    print(f"Connection closed for {addr}")

def start_server():
    """
    Initializes the TCP server, binds to the port, and listens for incoming connections.
    """
    # Create a new socket using IPv4 (AF_INET) and TCP (SOCK_STREAM)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set option to allow the port to be reused immediately after the server stops
    # This prevents the "Address already in use" error during development
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind the socket to our specific address and port
        server.bind((HOST, PORT))
        
        # Start listening for connections (queue up to 5)
        server.listen()
        print(f"Server online. Listening on {HOST}:{PORT}")
        print("Press Ctrl+C to stop the server.")
        
        while True:
            # Accept a new connection (this blocks the code until someone connects)
            conn, addr = server.accept()
            
            # Pass the connection to the handler function
            # We use threading here so the server can handle multiple connections if needed
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\nUser requested stop. Shutting down server...")
    except Exception as e:
        print(f"Server encountered an error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()