import os
import socket

RECV_PORT = int(os.environ.get("RECV_PORT", "40000"))
BIND_IP = "::" # '::' allows listening on ALL IPv6 interfaces [cite: 66, 68]

def main():
    try:
        ifaces = [name for _, name in socket.if_nameindex()]
        print(f"[RECV] Interfaces disponíveis: {ifaces}")
    except Exception:
        pass

    # Create IPv6 TCP Socket
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    # SO_REUSEADDR prevents "Address already in use" errors [cite: 24, 63, 69]
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Binding to ("::", port) works for all interfaces 
        sock.bind((BIND_IP, RECV_PORT))
        sock.listen(5)
        print(f"[RECV] Servidor ouvindo em IPv6 [{BIND_IP}] porta {RECV_PORT}")
    except Exception as e:
        print(f"[ERROR] Falha ao bind/listen: {e}")
        sock.close()
        return

    try:
        while True:
            conn, addr = sock.accept()
            # addr is (ip, port, flowinfo, scope_id) [cite: 70]
            print(f"[RECV] Conexão de: {addr}")

            try:
                data = conn.recv(4096)
                if not data:
                    print("[RECV] Conexão encerrada pelo cliente")
                else:
                    print(f"[RECV] Recebido {len(data)} bytes: {data.decode('utf-8')}")
            except Exception as e:
                print(f"[ERROR] Falha ao receber: {e}")
            finally:
                conn.close()
    except KeyboardInterrupt:
        print("[RECV] Encerrando servidor...")
    finally:
        sock.close()
        print("[RECV] Socket fechado")

if __name__ == "__main__":
    main()