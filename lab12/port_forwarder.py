import json
import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class PortForwarder:
    def __init__(self, config_path="port_forwarder_config.json"):
        self.config_path = config_path
        self.rules = []
        self.is_running = False

    def load_config(self):
        with open(self.config_path, "r") as f:
            config = json.load(f)
        self.rules = []
        for r in config["rules"]:
            rule = {
                "name": r["name"],
                "internal_ip": r["internal_ip"],
                "internal_port": int(r["internal_port"]),
                "external_ip": r["external_ip"],
                "external_port": int(r["external_port"]),
                "server_socket": None,
                "is_running": False,
            }
            self.rules.append(rule)

    def forward_data(self, from_sock, to_sock):
        while True:
            try:
                data = from_sock.recv(4096)
                if not data:
                    break
                to_sock.sendall(data)
            except:
                break

    def handle_client(self, rule, client_sock):
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.connect((rule["external_ip"], rule["external_port"]))
            t1 = threading.Thread(target=self.forward_data,
                                  args=(client_sock, server_sock), daemon=True)
            t2 = threading.Thread(target=self.forward_data,
                                  args=(server_sock, client_sock), daemon=True)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            server_sock.close()
        except:
            pass
        finally:
            client_sock.close()

    def accept_clients(self, rule, log_callback):
        while rule["is_running"]:
            try:
                client_sock, addr = rule["server_socket"].accept()
                log_callback("Подключение от " + str(addr[0]))
                t = threading.Thread(target=self.handle_client,
                                     args=(rule, client_sock), daemon=True)
                t.start()
            except:
                pass

    def start_rule(self, rule, log_callback):
        rule["server_socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rule["server_socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        rule["server_socket"].bind((rule["internal_ip"], rule["internal_port"]))
        rule["server_socket"].listen(5)
        rule["server_socket"].settimeout(1.0)
        rule["is_running"] = True
        t = threading.Thread(target=self.accept_clients,
                             args=(rule, log_callback), daemon=True)
        t.start()

    def stop_rule(self, rule):
        rule["is_running"] = False
        if rule["server_socket"]:
            rule["server_socket"].close()

    def start_all(self, log_callback):
        self.is_running = True
        for rule in self.rules:
            self.start_rule(rule, log_callback)

    def stop_all(self):
        self.is_running = False
        for rule in self.rules:
            self.stop_rule(rule)

class App:
    def __init__(self, root, fw):
        self.root = root
        self.root.title("Транслятор портов")
        self.root.geometry("900x700")
        self.fw = fw
        self._create_widgets()
        self._load_config()

    def _create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        ctrl = ttk.LabelFrame(main, text="Управление", padding=10)
        ctrl.grid(row=0, column=0, sticky="we", pady=(0, 10))

        ttk.Label(ctrl, text="IP:").grid(row=0, column=0, sticky="w")
        self.ip_var = tk.StringVar()
        self.ip_entry = ttk.Entry(ctrl, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5)

        ttk.Button(ctrl, text="Запустить транслятор",
                   command=self._toggle).grid(row=1, column=0, columnspan=2, sticky="we", pady=5)

        ttk.Button(ctrl, text="+", command=self._add_rule).grid(row=1, column=2)
        ttk.Button(ctrl, text="-", command=self._remove_rule).grid(row=1, column=3)

        ip_frame = ttk.LabelFrame(ctrl, text="Получение IP", padding=10)
        ip_frame.grid(row=0, column=4, padx=20, sticky="w")

        ttk.Label(ip_frame, text="Имя хоста").grid(row=0, column=0, sticky="w")
        self.hostname_var = tk.StringVar(value="yandex.ru")
        ttk.Entry(ip_frame, textvariable=self.hostname_var, width=20).grid(row=1, column=0)

        ttk.Button(ip_frame, text="Получить",
                   command=self._resolve_ip).grid(row=2, column=0, pady=5)

        ttk.Label(ip_frame, text="IP:").grid(row=3, column=0, sticky="w", pady=5)
        self.resolved_ip_var = tk.StringVar()
        ttk.Entry(ip_frame, textvariable=self.resolved_ip_var, width=20).grid(row=4, column=0)

        tbl = ttk.LabelFrame(main, text="Правила трансляции", padding=10)
        tbl.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        cols = ("name", "internal_ip", "internal_port", "external_ip", "external_port")
        self.tree = ttk.Treeview(tbl, columns=cols, show="headings", height=8)
        self.tree.heading("name", text="Название")
        self.tree.heading("internal_ip", text="Внутренний IP")
        self.tree.heading("internal_port", text="Внутренний порт")
        self.tree.heading("external_ip", text="Внешний IP")
        self.tree.heading("external_port", text="Внешний порт")
        self.tree.column("name", width=120)
        self.tree.column("internal_ip", width=120)
        self.tree.column("internal_port", width=100)
        self.tree.column("external_ip", width=120)
        self.tree.column("external_port", width=100)

        sb = ttk.Scrollbar(tbl, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        log_frame = ttk.LabelFrame(main, text="Журнал", padding=10)
        log_frame.grid(row=2, column=0, sticky="nsew")

        self.log_text = tk.Text(log_frame, height=8, wrap="word", state="disabled")
        log_sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_sb.set)
        log_sb.grid(row=0, column=1, sticky="ns")
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def _add_log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _load_config(self):
        try:
            self.fw.load_config()
            self._refresh_table()
            if self.fw.rules:
                self.ip_var.set(self.fw.rules[0]["internal_ip"])
            self._add_log("Конфигурация загружена")
        except Exception as e:
            self._add_log("Ошибка загрузки: " + str(e))

    def _resolve_ip(self):
        hostname = self.hostname_var.get()
        try:
            ip = socket.gethostbyname(hostname)
            self.resolved_ip_var.set(ip)
            self._add_log(hostname + " -> " + ip)
        except:
            self.resolved_ip_var.set("Ошибка")

    def _add_rule(self):
        try:
            name = "Rule " + str(len(self.fw.rules) + 1)
            internal_ip = self.ip_var.get() or "0.0.0.0"
            external_ip = self.resolved_ip_var.get() or "127.0.0.1"

            with open(self.fw.config_path, "r") as f:
                config = json.load(f)

            config["rules"].append({
                "name": name,
                "internal_ip": internal_ip,
                "internal_port": 8080,
                "external_ip": external_ip,
                "external_port": 80
            })

            with open(self.fw.config_path, "w") as f:
                json.dump(config, f, indent=4)

            self._load_config()
            self._add_log("Добавлено правило: " + name)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _remove_rule(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Подтверждение", "Удалить '" + name + "'?"):
            with open(self.fw.config_path, "r") as f:
                config = json.load(f)
            config["rules"] = [r for r in config["rules"] if r["name"] != name]
            with open(self.fw.config_path, "w") as f:
                json.dump(config, f, indent=4)
            self._load_config()
            self._add_log("Удалено правило: " + name)

    def _toggle(self):
        if self.fw.is_running:
            self.fw.stop_all()
            self.start_btn.config(text="Запустить транслятор")
            self._add_log("Транслятор остановлен")
        else:
            self.fw.start_all(self._add_log)
            self.start_btn.config(text="Остановить транслятор")
            self._add_log("Транслятор запущен")

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for rule in self.fw.rules:
            self.tree.insert("", "end", values=(
                rule["name"], rule["internal_ip"], rule["internal_port"],
                rule["external_ip"], rule["external_port"]
            ))


def main():
    fw = PortForwarder("port_forwarder_config.json")
    root = tk.Tk()
    app = App(root, fw)
    root.mainloop()


if __name__ == "__main__":
    main()
