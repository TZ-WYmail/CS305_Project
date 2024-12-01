import sys
import socket
import threading


class ConferenceClient:
    def __init__(self, server_addr, server_port):
        self.server_addr = server_addr
        self.server_port = server_port

        self.conns = None
        self.is_connected = False
        self.is_command = False

        self.conference_id = None
        self.conference_port = None
        self.is_conference_running = False
        self.con_conns = None
        self.is_video = False
        self.is_audio = False

        self.datatype = None  # 数据类型，如 text, audio, video, etc.
        self.data = None

    #将用户属性形成报文头部
    def make_Main_message(self):
        message = f"{self.is_connected}:{self.is_command}:{self.conference_id}:{self.is_conference_running}:{self.is_video}:{self.is_audio}:{self.datatype}:{self.data}"
        return message

    #传递给会议服务器的报文（以data为主）：iscommand+datatype+data
    def make_Conference_message(self):
        message = f"{self.is_command}:{self.datatype}:{self.data}"
        return message

    def connect_to_server(self):
        print('Connecting to server')
        ip_port = f"{self.server_addr}:{self.server_port}"
        try:
            ip, port = ip_port.split(':')
            port = int(port)
            self.conns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conns.connect((ip, port))
            print(f"Connected to server {ip_port}")
            self.is_connected = True
        except Exception as e:
            print(f"Failed to connect to server {ip_port}: {e}")

    def receive_from_conference(self):
        while True:
            try:
                # 接收服务器发送的数据
                data = self.con_conns.recv(1024)
                print("\n")
                message = data.decode()
                conference_id, command, data = message.split(':')[0], message.split(':')[1], message.split(':')[2:]
                if command == 'quit' or command == 'cancel':
                    self.is_conference_running = False
                    self.send_command_to_Mainserver('quit')
                    self.con_conns.close()
                    self.con_conns = None
                    self.conference_id = None
                    self.conference_port = None
                    print(data)

                elif command == 'list':
                    print(data)

                elif command == 'help':
                    print(data)
                else:
                    print(message)
                if not data:
                    break

            except Exception as e:
                print(f"Failed to receive data: {e}")
                break

    def send_command_to_Mainserver(self, command):
        if command == 'exit':
            self.data = command
            self.is_command = True
        if command.lower() == 'check':
            self.print_attributes()
            self.data = command
            self.is_command = False
            return
        elif command == 'help':
            print("Available commands: check, create, join, quit, start, stop, share, receive, help")
            self.data = command
            self.is_command = True

        elif command == 'create':
            self.datatype = 'text'
            self.data = command
            self.is_command = True

        elif command.startswith('join'):
            cmd, conference_id = command.split(' ')
            self.datatype = 'text'
            self.conference_id = conference_id
            self.data = cmd
            self.is_command = True

        elif command == 'quit':
            self.datatype = 'text'
            self.data = command
            self.is_command = True

        elif command == 'list':
            self.datatype = 'text'
            self.data = command
            self.is_command = True

        else:
            self.datatype = 'text'
            self.data = command
            self.is_command = False

        self.datatype = 'text'
        message = self.make_Main_message()
        print(message)
        if self.is_connected and self.conns:
            try:
                self.conns.sendall(message.encode())
            except Exception as e:
                print(f"Failed to send command: {e}")

    def receive_from_Mainserver(self):
        while True:
            data = self.conns.recv(1024)
            print(data.decode() + "\n")
            # 处理服务器返回的会议信息
            if data.decode().startswith('create'):
                conference_id, conference_port = data.decode().split(':')[1:]
                print(f"Conference created with ID: {conference_id} and Port: {conference_port}")
                # 这里可以添加连接到会议的逻辑
                self.conference_id = conference_id
                self.conference_port = int(conference_port)
                self.con_conns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.con_conns.connect((self.server_addr, self.conference_port))
                if self.con_conns:
                    self.is_conference_running = True
                    # 连接到会议后，你可以在新的线程中接收会议数据
                    threading.Thread(target=self.receive_from_conference, daemon=True).start()
                else:
                    print("Failed to connect to conference.")
                    #取消会议
                    self.send_command_to_Mainserver('cancel')


            elif data.decode().startswith('join'):
                conference_id, conference_port = data.decode().split(':')[1], data.decode().split(':')[2]
                self.conference_id = conference_id
                self.conference_port = int(conference_port)
                # 这里可以添加连接到会议的逻辑
                self.conference_id = conference_id
                self.conference_port = int(conference_port)
                self.con_conns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.con_conns.connect((self.server_addr, self.conference_port))
                if self.con_conns:
                    self.is_conference_running = True
                    print(f"Joined conference with ID: {conference_id} and Port: {conference_port}")
                    threading.Thread(target=self.receive_from_conference, daemon=True).start()
                else:
                    print("Failed to connect to conference.")
                    # 连接到会议后，你可以在新的线程中接收会议数据
            elif data.decode().startswith('quit'):
                quit_msg = data.decode().split(':')[1]
                print(quit_msg)
            elif data.decode().startswith('help'):
                help_msg = data.decode().split(':')[1]
                print(help_msg)
            elif data.decode().startswith('list'):
                conference_list = data.decode().split(':')[2:]
                print(conference_list)


    def send_command_to_conference(self, command):
        if command.lower() == 'check':
            self.print_attributes()
            self.data = command
            self.is_command = False
            return
        elif command.lower() == 'help':
            self.data = command
            self.is_command = True
        elif command.lower() == 'quit':
            self.data = command
            self.is_command = True
        elif command.lower() == 'list':
            self.data = command
            self.is_command = True
        else:
            self.data = command
            self.is_command = False
        message = self.make_Conference_message()
        if self.is_conference_running and self.con_conns:
            try:
                self.con_conns.sendall(message.encode())
            except Exception as e:
                print(f"Failed to send command: {e}")

    def start_communication(self):
        # Start receiving data from server in a separate thread
        threading.Thread(target=self.receive_from_Mainserver, daemon=True).start()

        # Main loop to send commands to server
        try:
            while self.is_connected:
                if self.is_conference_running:
                    title = f"conference:{self.conference_id}:{self.conference_port}"
                else:
                    title = f"Main server:{self.server_addr}:{self.server_port}"
                command = input(title + ">")
                if not self.is_conference_running:
                    self.send_command_to_Mainserver(command)
                else:
                    self.send_command_to_conference(command)
        except KeyboardInterrupt:
            print("\nExiting due to keyboard interrupt.")

    def close_connection(self):
        if self.conns:
            self.conns.close()
            print("Connection closed.")

    #查询自身状态
    def print_attributes(self):
        attributes = [
            ('Server Address', self.server_addr),
            ('Server Port', self.server_port),
            ('Connection Status', self.is_connected),
            ('Conference ID', self.conference_id),
            ('Conference Port', self.conference_port),
            ('Conference Running', self.is_conference_running),
            ('Data Type', self.datatype)
        ]
        for name, value in attributes:
            print(f"{name}: {value}")


if __name__ == "__main__":
    client = ConferenceClient("127.0.0.1", "5555")
    client.connect_to_server()
    if client.is_connected:
        client.start_communication()
