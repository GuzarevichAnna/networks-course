import subprocess
import socket
import ipaddress
import re
import sys

def get_my_info():
    result = subprocess.run(['ip', '-4', 'addr', 'show'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if 'inet ' in line and 'global' in line:
            parts = line.strip().split()
            ip_with_mask = parts[1]
            network = ipaddress.IPv4Network(ip_with_mask, strict=False)
            my_ip = ip_with_mask.split('/')[0]
            break

    result = subprocess.run(['ip', 'link'], capture_output=True, text=True)
    my_mac = "unknown"
    for line in result.stdout.split('\n'):
        if 'link/ether' in line:
            my_mac = line.split()[1]
            break

    my_name = socket.gethostname()
    return my_ip, my_mac, my_name, network

def arping(ip, interface):
    try:
        cmd = ['sudo', 'arping', '-c', '1', '-w', '1', '-I', interface, ip]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        output = result.stdout
        match = re.search(r'([0-9a-f:]{17})', output, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    except:
        pass
    return None

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "unknown"

def get_default_interface():
    result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
    parts = result.stdout.split()
    if len(parts) >= 5:
        return parts[4]
    result = subprocess.run(['ip', 'link'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if 'link/ether' in line:
            return line.split(':')[1].strip()

def main():
    interface = get_default_interface()
    my_ip, my_mac, my_name, network = get_my_info()

    print(f"This host: {my_ip}, {my_mac}, {my_name}")
    print(f"Nework: {network}, interface: {interface}\n")
    print("Scanning the network...\n")

    computers = [(my_ip, my_mac, my_name)]

    for ip in network.hosts():
        ip_str = str(ip)
        if ip_str == my_ip:
            continue
        print(f"Checking {ip_str}...", end='\r')
        mac = arping(ip_str, interface)
        if mac:
            name = get_hostname(ip_str)
            computers.append((ip_str, mac, name))

    print("\nReport:")
    print("=" * 70)
    print(f"{'IP':<18} {'MAC':<18} {'hostname'}")
    print("-" * 70)
    for ip, mac, name in computers:
        print(f"{ip:<18} {mac:<18} {name}")

if __name__ == "__main__":
    main()