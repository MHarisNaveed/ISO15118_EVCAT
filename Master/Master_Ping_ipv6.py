import socket
import time

# Use the Client Pi's IPv6 Link-Local address and interface suffix
SERVER_IP = "fe80::8f2d:7470:bb0c:7462%eth0" 
PORT = 40000
DATA = "TESTE123 HANDSHAKE"

def main():
    print(f"[MASTER] Destination: [{SERVER_IP}]:{PORT}")

    # Set up for IPv6 (AF_INET6)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.settimeout(5.0)

    try:
        # Connect to the Client
        sock.connect((SERVER_IP, PORT))
        print(f"[MASTER] Connected to Client over PLC")

        # Send data
        sock.send(DATA.encode("utf-8"))
        print(f"[MASTER] Sent: {DATA}")

    except Exception as e:
        print(f"[MASTER] Error: {e}")

    finally:
        sock.close()
        print("[MASTER] Socket closed")

if __name__ == "__main__":
    main()