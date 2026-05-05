import sys
import socket

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <IP> <start port> <end port>")
        sys.exit(1)

    ip = sys.argv[1]
    try:
        start_port = int(sys.argv[2])
        end_port = int(sys.argv[3])
    except ValueError:
        print("Ports must be integers")
        sys.exit(1)

    print(f"Free TCP ports on {ip} in range {start_port}-{end_port}:")

    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((ip, port))
            print(port)
        except OSError:
            pass  #port is not free
        finally:
            sock.close()

if __name__ == "__main__":
    main()
