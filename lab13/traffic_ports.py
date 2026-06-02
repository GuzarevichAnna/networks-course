import signal
from scapy.all import sniff, IP, TCP, UDP

rx_by_port = {}
tx_by_port = {}

MY_IP = None

def get_my_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def packet_callback(packet):
    global rx_by_port, tx_by_port

    if IP not in packet:
        return
    ip = packet[IP]
    size = len(ip)

    if ip.dst == MY_IP:
        if TCP in packet:
            port = packet[TCP].dport
        elif UDP in packet:
            port = packet[UDP].dport
        else:
            return
        rx_by_port[port] = rx_by_port.get(port, 0) + size

    elif ip.src == MY_IP:
        if TCP in packet:
            port = packet[TCP].sport
        elif UDP in packet:
            port = packet[UDP].sport
        else:
            return
        tx_by_port[port] = tx_by_port.get(port, 0) + size

def print_report(signum=None, frame=None):
    print("Report:")

    print("\n--- Incoming traffic ---")
    if rx_by_port:
        for port, bytes_count in sorted(rx_by_port.items()):
            print(f"Port {port}: {bytes_count}B")
    else:
        print("No traffic")

    print("\n--- Outcoming traffic ---")
    if tx_by_port:
        for port, bytes_count in sorted(tx_by_port.items()):
            print(f"Port {port}: {bytes_count}B")
    else:
        print("No traffic")

    exit(0)

if __name__ == "__main__":
    MY_IP = get_my_ip()
    print(f"This host ip: {MY_IP}")
    print("Started sniffing... Press Ctrl+C to stop sniffing and get the report")
    signal.signal(signal.SIGINT, print_report)
    sniff(prn=packet_callback, store=False)