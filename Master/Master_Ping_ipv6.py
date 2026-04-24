import socket
import time

# Use the Client's IPv6 Link-Local address (found via 'ip a' on the client)
SECC2_IP = "fe80::8f2d:7470:bb0c:7462" 
INTERFACE = "eth0" # The physical interface for PLC
PORT = 40000 
DATA = "I am the Master Calling" 

def compute_connect_tuple(ip: str, port: int, iface: str):
    """
    Computes the 4-tuple required for IPv6 Link-Local connections.
    Format: (address, port, flowinfo, scope_id)
    """
    try:
        # Get the integer index of the interface (e.g., eth0 -> 2)
        scope_id = socket.if_nametoindex(iface)
        return (ip, port, 0, scope_id)
    except Exception as e:
        print(f"[ERROR] Could not find index for interface {iface}: {e}")
        return (ip, port)

def main():
    print(f"[SEND] Destino: [{SECC2_IP}%{INTERFACE}]:{PORT}")
    
    # AF_INET6 is required for IPv6 [cite: 65, 69]
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    
    connect_tuple = compute_connect_tuple(SECC2_IP, PORT, INTERFACE)
    start = time.monotonic()
    
    try:
        sock.connect(connect_tuple)
        elapsed = time.monotonic() - start
        print(f"[SEND] Conectado em {elapsed:.3f}s")
        
        sent = sock.send(DATA.encode("utf-8"))
        print(f"[SEND] Enviado {sent} bytes: {DATA!r}")
        
    except socket.timeout:
        print("[ERROR] Timeout na conexão (check if server is running)")
    except Exception as e:
        print(f"[ERROR] Falha na conexão/envio: {e}")
    finally:
        sock.close()
        print("[SEND] Socket fechado")

if __name__ == "__main__":
    main()