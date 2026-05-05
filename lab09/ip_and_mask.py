import subprocess

def main():
    result = subprocess.run(["ip", "-4", "-brief", "addr"], capture_output=True, text=True)
    for line in result.stdout.strip().split("\n"):
        if "lo" in line:
            continue
        parts = line.split()
        iface = parts[0]
        ip_mask = parts[2]
        ip, masklen = ip_mask.split("/")
        print(f"{iface:10s}  IP: {ip}   Mask: /{masklen}")

if __name__ == "__main__":
    main()
