import socket
import time
import sys
import os

def checksum(data):
    s = 0
    for i in range(0, len(data), 2):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        s += (b1 << 8) + b2
    while (s >> 16 != 0):
        s &= 0xFFFF
        s += (s >> 16)
    return (~s) & 0xFFFF


def build_icmp_request(seq, icmp_id):
    header = bytearray(8)
    header[0] = 8 # echo request type
    header[1] = 0 # echo request code
    header[4] = (icmp_id >> 8) & 0xFF
    header[5] = icmp_id & 0xFF
    header[6] = (seq >> 8) & 0xFF
    header[7] = seq & 0xFF

    payload = bytearray(8) # some random payload

    full_packet = header + payload
    chk = checksum(full_packet)
    full_packet[2] = (chk >> 8) & 0xFF
    full_packet[3] = chk & 0xFF

    return full_packet


def traceroute(dest, probes=3, max_hops=30):
    dest_ip = socket.gethostbyname(dest)
    icmp_id = os.getpid()

    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    sock.settimeout(2.0)

    seq = 1

    for ttl in range(1, max_hops + 1):
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        hop_results = []
        reached = False

        for _ in range(probes):
            packet = build_icmp_request(seq, icmp_id)
            send_time = time.time()
            sock.sendto(packet, (dest_ip, 0))

            while True:
                try:
                    reply, addr = sock.recvfrom(2048)
                    recv_time = time.time()
                except socket.timeout:
                    hop_results.append("*")
                    break

                icmp_type = reply[20] # skip first 20 bytes (ip header)

                recv_seq = None
                if icmp_type == 0: # echo reply type (reached dest)
                    recv_seq = (reply[26] << 8) + reply[27]
                elif icmp_type == 11: # ttl exceeded
                    # skip 20 (ip header) + 8 (icmp header) + 20 (ip header of initial package) + 6(part of icmp header of intial package)
                    recv_seq = (reply[54] << 8) + reply[55] 

                if recv_seq is not None and recv_seq == seq:
                    rtt = (recv_time - send_time) * 1000 #convert to ms
                    router_address = addr[0]
                    try:
                        hostname = socket.gethostbyaddr(router_address)[0]
                    except socket.herror:
                        hostname = ""
            
                    hop_results.append(f"{router_address} {hostname} ({rtt:.2f} ms)")

                    if icmp_type == 0:
                        reached = True
                    break

            seq += 1

        print(f"{ttl:2d}  " + "\t\t".join(hop_results))
        if reached:
            break

    sock.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: sudo python3 my_traceroute.py <host> [probes num]")
        sys.exit(1)

    host = sys.argv[1]
    probes = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    traceroute(host, probes)
