import socket

server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
server_socket.bind(("::1", 12345))
server_socket.listen(1)

while True:
    print("waiting for client to connect")
    conn, addr = server_socket.accept()
    with conn:
        print(f"connected client: {addr}")
        while True:
            data = conn.recv(2048)
            if not data:
                break
            text = data.decode('utf-8')
            conn.sendall(text.upper().encode('utf-8'))
