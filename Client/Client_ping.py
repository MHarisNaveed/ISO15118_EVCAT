import socket

SERVER_IP = "192.168.188.2"
PORT = 40000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.connect((SERVER_IP, PORT))
sock.send(b"TESTE123")

print("Sent OK")

sock.close()