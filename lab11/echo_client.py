import socket

client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
client_socket.connect(("::1", 12345))

while True:
    message = input("> ")
    if message == "":
        continue
    if message == "exit":
        break;
    
    client_socket.sendall(message.encode('utf-8'))
    response = client_socket.recv(2048).decode('utf-8')
    print(response)

client_socket.close()