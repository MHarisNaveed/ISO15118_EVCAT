import socket
import time

SERVER_IP = "192.168.188.2"
PORT = 40000
DATA = "TESTE123 HEloooooooooooooooooo "

def main():
    print(f"[SEND] Destino: {SERVER_IP}:{PORT}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)

    start = time.monotonic()

    try:
        sock.connect((SERVER_IP, PORT))

        elapsed = time.monotonic() - start
        print(f"[SEND] Conectado em {elapsed:.3f}s")

        sent = sock.send(DATA.encode("utf-8"))
        print(f"[SEND] Enviado {sent} bytes: {DATA!r}")

    except socket.timeout:
        print("[ERROR] Timeout na conexão")

    except Exception as e:
        print(f"[ERROR] Falha: {e}")

    finally:
        sock.close()
        print("[SEND] Socket fechado")

if __name__ == "__main__":
    main()