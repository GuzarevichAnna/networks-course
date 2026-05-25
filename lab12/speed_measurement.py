import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time
import os

class UDPServer:
    def __init__(self, port):
        self.port = port
        self.running = False
        self.sock = None
        self.total_bytes = 0
        self.total_packets = 0
        self.start_time = None

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.settimeout(1.0)
        self.running = True
        self.total_bytes = 0
        self.total_packets = 0
        self.start_time = None

        while self.running:
            try:
                data, addr = self.sock.recvfrom(65535)
                if len(data) >= 12:
                    self.total_bytes += len(data) - 12
                    self.total_packets += 1
                    if self.start_time is None:
                        self.start_time = time.time()
                    elapsed = time.time() - self.start_time
                    if elapsed > 0:
                        speed = (self.total_bytes * 8) / (elapsed * 1_000_000)
                    else:
                        speed = 0
                    packets_sent = self.total_packets
                    packets_received = self.total_packets
                    lost = max(0, packets_sent - packets_received)
                    update_gui('udp', speed, self.total_bytes, elapsed, self.total_packets, lost)
            except socket.timeout:
                continue

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()


class UDPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = False

    def send(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True
        total_sent = 0
        total_packets = 0
        seq = 0
        start_time = time.time()

        while self.running:
            payload = os.urandom(1400)
            timestamp = time.time()
            packet = struct.pack('!Id', seq, timestamp) + payload
            try:
                sock.sendto(packet, (self.server_ip, self.server_port))
                total_sent += len(packet)
                total_packets += 1
                seq += 1
                elapsed = time.time() - start_time
                if elapsed > 0:
                    speed = (total_sent * 8) / (elapsed * 1_000_000)
                else:
                    speed = 0
                update_gui('udp_client', speed, total_sent, elapsed, total_packets, 0)
            except Exception as e:
                print(f"UDP send error: {e}")
                break
            time.sleep(0.001)
        sock.close()

    def start(self):
        self.thread = threading.Thread(target=self.send, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False


class TCPServer:
    def __init__(self, port):
        self.port = port
        self.running = False
        self.sock = None
        self.total_bytes = 0
        self.start_time = None

    def handle_client(self, client_sock, addr):
        client_sock.settimeout(5.0)
        while self.running:
            try:
                data = client_sock.recv(65535)
                if not data:
                    break
                self.total_bytes += len(data)
                if self.start_time is None:
                    self.start_time = time.time()
                elapsed = time.time() - self.start_time
                if elapsed > 0:
                    speed = (self.total_bytes * 8) / (elapsed * 1_000_000)
                else:
                    speed = 0
                update_gui('tcp', speed, self.total_bytes, elapsed, 0, 0)
            except socket.timeout:
                continue
            except Exception as e:
                break
        client_sock.close()

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen(5)
        self.sock.settimeout(1.0)
        self.running = True
        self.total_bytes = 0
        self.start_time = None

        while self.running:
            try:
                client_sock, addr = self.sock.accept()
                t = threading.Thread(target=self.handle_client, args=(client_sock, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()


class TCPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = False

    def send(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        total_sent = 0
        start_time = time.time()

        try:
            sock.connect((self.server_ip, self.server_port))
            while self.running:
                payload = os.urandom(1400)
                try:
                    sock.sendall(payload)
                    total_sent += len(payload)
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        speed = (total_sent * 8) / (elapsed * 1_000_000)
                    else:
                        speed = 0
                    update_gui('tcp_client', speed, total_sent, elapsed, 0, 0)
                except Exception as e:
                    print(f"TCP send error: {e}")
                    break
                time.sleep(0.001)
        finally:
            sock.close()

    def start(self):
        self.thread = threading.Thread(target=self.send, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False


import struct

gui_tcp_speed = "0.00"
gui_tcp_bytes = "0"
gui_tcp_time = "0.00"
gui_udp_speed = "0.00"
gui_udp_bytes = "0"
gui_udp_time = "0.00"
gui_udp_lost = "0"


def update_gui(protocol, speed, total_bytes, elapsed, packets, lost):
    global gui_tcp_speed, gui_tcp_bytes, gui_tcp_time
    global gui_udp_speed, gui_udp_bytes, gui_udp_time, gui_udp_lost

    if protocol in ('tcp', 'tcp_client'):
        gui_tcp_speed = f"{speed:.2f}"
        gui_tcp_bytes = f"{total_bytes:,}"
        gui_tcp_time = f"{elapsed:.2f}"
    elif protocol in ('udp', 'udp_client'):
        gui_udp_speed = f"{speed:.2f}"
        gui_udp_bytes = f"{total_bytes:,}"
        gui_udp_time = f"{elapsed:.2f}"
        gui_udp_lost = str(lost)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Measurement - TCP/UDP")
        self.root.geometry("800x700")

        self.tcp_server = None
        self.tcp_client = None
        self.udp_server = None
        self.udp_client = None
        self.tcp_running = False
        self.udp_running = False

        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.root, padding="10")
        main.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        cfg = ttk.LabelFrame(main, text="Configuration", padding="10")
        cfg.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(cfg, text="Server IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ip_entry = ttk.Entry(cfg, width=20)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(cfg, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.port_entry = ttk.Entry(cfg, width=10)
        self.port_entry.insert(0, "9999")
        self.port_entry.grid(row=0, column=3, padx=(0, 10))

        tcp_frame = ttk.LabelFrame(main, text="TCP Transfer", padding="10")
        tcp_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        btn_f = ttk.Frame(tcp_frame)
        btn_f.grid(row=0, column=0, pady=(0, 10))

        self.tcp_start_btn = ttk.Button(btn_f, text="Start TCP Server", command=self.start_tcp_server)
        self.tcp_start_btn.grid(row=0, column=0, padx=5)
        self.tcp_stop_btn = ttk.Button(btn_f, text="Stop TCP Server", command=self.stop_tcp_server, state=tk.DISABLED)
        self.tcp_stop_btn.grid(row=0, column=1, padx=5)
        self.tcp_client_btn = ttk.Button(btn_f, text="Start TCP Client", command=self.start_tcp_client)
        self.tcp_client_btn.grid(row=0, column=2, padx=5)
        self.tcp_client_stop_btn = ttk.Button(btn_f, text="Stop TCP Client", command=self.stop_tcp_client, state=tk.DISABLED)
        self.tcp_client_stop_btn.grid(row=0, column=3, padx=5)

        stats_f = ttk.Frame(tcp_frame)
        stats_f.grid(row=1, column=0)

        self.tcp_speed_lbl = ttk.Label(stats_f, text="Speed: 0.00 Mbps", font=("Arial", 12))
        self.tcp_speed_lbl.grid(row=0, column=0, padx=10)
        self.tcp_bytes_lbl = ttk.Label(stats_f, text="Bytes: 0", font=("Arial", 12))
        self.tcp_bytes_lbl.grid(row=0, column=1, padx=10)
        self.tcp_time_lbl = ttk.Label(stats_f, text="Time: 0.00 s", font=("Arial", 12))
        self.tcp_time_lbl.grid(row=0, column=2, padx=10)

        udp_frame = ttk.LabelFrame(main, text="UDP Transfer", padding="10")
        udp_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        btn_f2 = ttk.Frame(udp_frame)
        btn_f2.grid(row=0, column=0, pady=(0, 10))

        self.udp_start_btn = ttk.Button(btn_f2, text="Start UDP Server", command=self.start_udp_server)
        self.udp_start_btn.grid(row=0, column=0, padx=5)
        self.udp_stop_btn = ttk.Button(btn_f2, text="Stop UDP Server", command=self.stop_udp_server, state=tk.DISABLED)
        self.udp_stop_btn.grid(row=0, column=1, padx=5)
        self.udp_client_btn = ttk.Button(btn_f2, text="Start UDP Client", command=self.start_udp_client)
        self.udp_client_btn.grid(row=0, column=2, padx=5)
        self.udp_client_stop_btn = ttk.Button(btn_f2, text="Stop UDP Client", command=self.stop_udp_client, state=tk.DISABLED)
        self.udp_client_stop_btn.grid(row=0, column=3, padx=5)

        stats_f2 = ttk.Frame(udp_frame)
        stats_f2.grid(row=1, column=0)

        self.udp_speed_lbl = ttk.Label(stats_f2, text="Speed: 0.00 Mbps", font=("Arial", 12))
        self.udp_speed_lbl.grid(row=0, column=0, padx=10)
        self.udp_bytes_lbl = ttk.Label(stats_f2, text="Bytes: 0", font=("Arial", 12))
        self.udp_bytes_lbl.grid(row=0, column=1, padx=10)
        self.udp_time_lbl = ttk.Label(stats_f2, text="Time: 0.00 s", font=("Arial", 12))
        self.udp_time_lbl.grid(row=0, column=2, padx=10)
        self.udp_lost_lbl = ttk.Label(stats_f2, text="Lost: 0", font=("Arial", 12))
        self.udp_lost_lbl.grid(row=0, column=3, padx=10)

        log_frame = ttk.LabelFrame(main, text="Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        self.log_text = tk.Text(log_frame, width=80, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(3, weight=1)

        self._update_labels()

    def _update_labels(self):
        global gui_tcp_speed, gui_tcp_bytes, gui_tcp_time
        global gui_udp_speed, gui_udp_bytes, gui_udp_time, gui_udp_lost

        self.tcp_speed_lbl.config(text=f"Speed: {gui_tcp_speed} Mbps")
        self.tcp_bytes_lbl.config(text=f"Bytes: {gui_tcp_bytes}")
        self.tcp_time_lbl.config(text=f"Time: {gui_tcp_time} s")
        self.udp_speed_lbl.config(text=f"Speed: {gui_udp_speed} Mbps")
        self.udp_bytes_lbl.config(text=f"Bytes: {gui_udp_bytes}")
        self.udp_time_lbl.config(text=f"Time: {gui_udp_time} s")
        self.udp_lost_lbl.config(text=f"Lost: {gui_udp_lost}")

        self.root.after(100, self._update_labels)

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)

    def start_tcp_server(self):
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port!")
            return

        self.tcp_server = TCPServer(port)
        self.tcp_server.start()
        self.tcp_running = True
        self.tcp_start_btn.config(state=tk.DISABLED)
        self.tcp_stop_btn.config(state=tk.NORMAL)
        self._log(f"TCP Server started on port {port}")

    def stop_tcp_server(self):
        if self.tcp_server:
            self.tcp_server.stop()
        self.tcp_running = False
        self.tcp_start_btn.config(state=tk.NORMAL)
        self.tcp_stop_btn.config(state=tk.DISABLED)
        self._log("TCP Server stopped")

    def start_tcp_client(self):
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port!")
            return
        ip = self.ip_entry.get()

        self.tcp_client = TCPClient(ip, port)
        self.tcp_client.start()
        self.tcp_client_btn.config(state=tk.DISABLED)
        self.tcp_client_stop_btn.config(state=tk.NORMAL)
        self._log(f"TCP Client started -> {ip}:{port}")

    def stop_tcp_client(self):
        if self.tcp_client:
            self.tcp_client.stop()
        self.tcp_client_btn.config(state=tk.NORMAL)
        self.tcp_client_stop_btn.config(state=tk.DISABLED)
        self._log("TCP Client stopped")

    def start_udp_server(self):
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port!")
            return

        self.udp_server = UDPServer(port)
        self.udp_server.start()
        self.udp_running = True
        self.udp_start_btn.config(state=tk.DISABLED)
        self.udp_stop_btn.config(state=tk.NORMAL)
        self._log(f"UDP Server started on port {port}")

    def stop_udp_server(self):
        if self.udp_server:
            self.udp_server.stop()
        self.udp_running = False
        self.udp_start_btn.config(state=tk.NORMAL)
        self.udp_stop_btn.config(state=tk.DISABLED)
        self._log("UDP Server stopped")

    def start_udp_client(self):
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port!")
            return
        ip = self.ip_entry.get()

        self.udp_client = UDPClient(ip, port)
        self.udp_client.start()
        self.udp_client_btn.config(state=tk.DISABLED)
        self.udp_client_stop_btn.config(state=tk.NORMAL)
        self._log(f"UDP Client started -> {ip}:{port}")

    def stop_udp_client(self):
        if self.udp_client:
            self.udp_client.stop()
        self.udp_client_btn.config(state=tk.NORMAL)
        self.udp_client_stop_btn.config(state=tk.DISABLED)
        self._log("UDP Client stopped")


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
