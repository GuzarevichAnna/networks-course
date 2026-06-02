import time

INTERFACE = "wlp0s20f3"

def get_bytes():
    with open("/proc/net/dev", "r") as f:
        lines = f.readlines()[2:]
    for line in lines:
        parts = line.split()
        iface = parts[0].rstrip(':')
        if iface == INTERFACE:
            rx = int(parts[1])
            tx = int(parts[9])
            return rx, tx
    raise Exception(f"Interface {INTERFACE} not found")

prev_rx, prev_tx = get_bytes()
print(f"Monitoring {INTERFACE}")

while True:
    time.sleep(1)
    rx, tx = get_bytes()
    
    delta_rx = rx - prev_rx
    delta_tx = tx - prev_tx
    
    print(f"Read bytes: {delta_rx}B\tTransmissioned bytes: {delta_tx}B")
    
    prev_rx, prev_tx = rx, tx
