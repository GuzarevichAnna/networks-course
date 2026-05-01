import socket
import os
import re
from getpass import getpass

class FTPClient:
    def __init__(self):
        self.control_socket = None
        self.data_socket = None
        self.host = ''
        self.username = ''
        self.port = 21
        
    def connect(self):
        print("\nftp server connection")
        self.host = input("enter ftp server address: ").strip()
        self.username = input("enter username: ").strip()
        password = getpass("enter password: ")
        
        try:
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.control_socket.settimeout(30)
            self.control_socket.connect((self.host, self.port))
            
            response = self.receive_response()
            if not response.startswith('220'):
                print(f"connection failed: {response}")
                return False
            
            self.send_command(f"USER {self.username}")
            response = self.receive_response()
            
            if response.startswith('331'):
                self.send_command(f"PASS {password}")
                response = self.receive_response()
                
                if response.startswith('230'):
                    print(f"connected to {self.host}")
                    return True
                else:
                    print(f"authentication failed: {response}")
                    return False
            else:
                print(f"username not accepted: {response}")
                return False
                
        except socket.error as e:
            print(f"connection error: {e}")
            return False
    
    def disconnect(self):
        if self.control_socket:
            self.send_command("QUIT")
            self.control_socket.close()
            print("disconnected from server")
    
    def send_command(self, command):
        self.control_socket.send(f"{command}\r\n".encode())
    
    def receive_response(self):
        response = ""
        while True:
            data = self.control_socket.recv(4096).decode()
            response += data
            lines = response.split('\r\n')
            for line in lines:
                if line and len(line) >= 4 and line[3] == ' ':
                    return line
    
    def setup_data_connection(self):
        self.send_command("PASV")
        response = self.receive_response()
        
        match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
        if not match:
            print(f"passive mode failed: {response}")
            return False
        
        h1, h2, h3, h4, p1, p2 = map(int, match.groups())
        data_host = f"{h1}.{h2}.{h3}.{h4}"
        data_port = (p1 * 256) + p2
        
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket.settimeout(30)
        self.data_socket.connect((data_host, data_port))
        return True
    
    def close_data_connection(self):
        if self.data_socket:
            self.data_socket.close()
            self.data_socket = None
    
    def list_files(self):
        self.send_command("PWD")
        print(f"\ncurrent directory: {self.receive_response()}\n")
        
        if not self.setup_data_connection():
            return
        
        self.send_command("LIST")
        response = self.receive_response()
        
        if not response.startswith('150'):
            print(f"list command failed: {response}")
            self.close_data_connection()
            return
        
        data = b""
        while True:
            chunk = self.data_socket.recv(4096)
            if not chunk:
                break
            data += chunk
        
        self.close_data_connection()
        self.receive_response()
        
        lines = data.decode().strip().split('\r\n')
        
        if not lines or (len(lines) == 1 and not lines[0]):
            print("directory is empty")
            return
        
        print(f"{'type':<6} {'size':>12} {'modified':<20} {'name'}")
        print("-" * 70)
        
        for line in lines:
            if not line:
                continue
            parts = line.split()
            if len(parts) < 9:
                continue
            
            permissions = parts[0]
            size = parts[4]
            month = parts[5]
            day = parts[6]
            time_or_year = parts[7]
            name = ' '.join(parts[8:])
            
            item_type = "[DIR]" if permissions.startswith('d') else "[FILE]"
            size_formatted = self.format_size(int(size))
            date_str = f"{month} {day} {time_or_year}"
            
            print(f"{item_type:<6} {size_formatted:>12} {date_str:<20} {name}")
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def navigate_directories(self):
        while True:
            self.list_files()
            
            print("\nnavigation commands:")
            print("cd <directory> - change directory")
            print(".. - go up one level")
            print("back - return to main menu")
            
            choice = input("\nenter command: ").strip()
            
            if choice == 'back':
                break
            elif choice == '..':
                self.send_command("CDUP")
                response = self.receive_response()
                if response.startswith('250'):
                    self.send_command("PWD")
                    print(f"moved up to: {self.receive_response()}")
                else:
                    print("cannot go up from here")
            elif choice.startswith('cd '):
                dir_name = choice[3:].strip()
                self.send_command(f"CWD {dir_name}")
                response = self.receive_response()
                if response.startswith('250'):
                    self.send_command("PWD")
                    print(f"changed to: {self.receive_response()}")
                else:
                    print(f"cannot change to directory '{dir_name}'")
            else:
                print("unknown command")
    
    def upload_file(self):
        print("\nupload file to server")
        
        local_path = input("enter local file path: ").strip()
        
        if not os.path.exists(local_path):
            print(f"file '{local_path}' not found")
            return
        
        if not os.path.isfile(local_path):
            print(f"'{local_path}' is not a file")
            return
        
        remote_filename = input("enter remote filename (enter to keep original): ").strip()
        if not remote_filename:
            remote_filename = os.path.basename(local_path)
        
        if not self.setup_data_connection():
            return
        
        self.send_command(f"STOR {remote_filename}")
        response = self.receive_response()
        
        if not response.startswith('150'):
            print(f"upload command failed: {response}")
            self.close_data_connection()
            return
        
        print(f"uploading '{remote_filename}'...")
        
        with open(local_path, 'rb') as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                self.data_socket.send(chunk)
                print('.', end='', flush=True)
        
        self.data_socket.shutdown(socket.SHUT_WR)
        self.close_data_connection()
        
        response = self.receive_response()
        if response.startswith('226'):
            print(f"\nfile uploaded successfully")
        else:
            print(f"\nupload failed: {response}")
    
    def download_file(self):
        print("\ndownload file from server")
        
        self.list_files()
        
        remote_filename = input("\nenter filename on server to download: ").strip()
        if not remote_filename:
            print("filename cannot be empty")
            return
        
        local_path = input("enter local save path (enter for current directory): ").strip()
        if not local_path:
            local_path = remote_filename
        elif os.path.isdir(local_path):
            local_path = os.path.join(local_path, remote_filename)
        
        if os.path.exists(local_path):
            overwrite = input(f"file '{local_path}' already exists. overwrite? (y/n): ").lower()
            if overwrite != 'y':
                print("download cancelled")
                return
        
        self.send_command("TYPE I")
        self.receive_response()
        
        if not self.setup_data_connection():
            return
        
        self.send_command(f"RETR {remote_filename}")
        response = self.receive_response()
        
        if not response.startswith('150'):
            print(f"download command failed: {response}")
            self.close_data_connection()
            return
        
        print(f"downloading '{remote_filename}'...")
        
        os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
        
        with open(local_path, 'wb') as file:
            while True:
                chunk = self.data_socket.recv(4096)
                if not chunk:
                    break
                file.write(chunk)
                print('.', end='', flush=True)
        
        self.close_data_connection()
        
        response = self.receive_response()
        if response.startswith('226'):
            print(f"\nfile saved as '{local_path}'")
        else:
            print(f"\ndownload failed: {response}")
            os.remove(local_path)
    
    def show_current_directory(self):
        self.send_command("PWD")
        print(f"current directory: {self.receive_response()}")
    
    def run(self):
        print("\n" + "="*50)
        print("ftp client")
        print("="*50)
        
        if not self.connect():
            print("failed to connect. exiting...")
            return
        
        try:
            while True:
                print("\n" + "="*50)
                print("main menu")
                print("="*50)
                print("1. list files on server")
                print("2. navigate directories")
                print("3. upload file to server")
                print("4. download file from server")
                print("5. show current directory")
                print("0. exit")
                
                choice = input("\nselect option (0-5): ").strip()
                
                if choice == '1':
                    self.list_files()
                elif choice == '2':
                    self.navigate_directories()
                elif choice == '3':
                    self.upload_file()
                elif choice == '4':
                    self.download_file()
                elif choice == '5':
                    self.show_current_directory()
                elif choice == '0':
                    print("\ngoodbye")
                    break
                else:
                    print("invalid choice. try again.")
                    
        except KeyboardInterrupt:
            print("\n\ninterrupted by user")
        finally:
            self.disconnect()


def main():
    client = FTPClient()
    client.run()


if __name__ == "__main__":
    main()