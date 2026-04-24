import socket

HOST = "::"  # Listen on all IPv6 interfaces
PORT = 40000

def main():
    # Set up for IPv6 (AF_INET6)
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    
    # Allow immediate reuse of the port after a restart
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"[CLIENT] Listening on IPv6 Port {PORT}...")

        while True:
            conn, addr = server.accept()
            # addr for IPv6 is a 4-tuple: (ip, port, flowinfo, scope_id)
            print(f"[CLIENT] Connected by: {addr[0]}")

            data = conn.recv(1024)
            if data:
                print(f"[CLIENT] Received: {data.decode('utf-8')}")
            
            conn.close()
            print("[CLIENT] Connection closed, waiting for next...")

    except Exception as e:
        print(f"[CLIENT] Error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    main()