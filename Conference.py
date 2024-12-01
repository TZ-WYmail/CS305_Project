import socket
import threading


class Conference:
    def __init__(self, conference_id, port, client_socket):
        self.conference_id = conference_id
        self.is_active = True
        self.hoster = client_socket
        self.port = port
        self.clients = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', port))
        self.server_socket.listen(5)
        print(f"[*] Conference {conference_id} listening on port {port}")

    def remove_client(self, client):
        """Remove a client from the conference."""
        if client in self.clients:
            self.clients.remove(client)
            client.close()
            print("[*] Client disconnected from conference")

    def handle_client(self, client_socket):
        """Handle incoming messages from a client."""
        while True:
            if client_socket not in self.clients:
                print("[*] Client disconnected from conference")
                return  # Client has disconnected
            #接收数据
            recv_message = client_socket.recv(1024)
            message = recv_message.decode()
            self.handle_message(client_socket, message)
            #打印对应的信息，from：message
            print(f"[*] Received message from {client_socket}: {message}")

    #业务逻辑处理
    def handle_message(self, client_socket, message):
        # 接收客户端发送的数据
        is_connected = message[0]
        conference_id = message[1]
        is_conference_running = message[2]
        is_command = message[3]
        datatype = message[4]
        data = message[5]

        # 打印收到的全部信息
        print(f"Is Connected: {is_connected}")
        print(f"Is Command: {is_command}")
        print(f"Conference ID: {conference_id}")
        print(f"Is Conference Running: {is_conference_running}")
        print(f"Data Type: {datatype}")

        if data is not None:
            print(f"Data: {data}")
        if is_command:
            if data == 'quit':
                self.quit(client_socket)
            elif data == 'help':
                self.help(client_socket)
            elif data == 'cancel':
                self.cancel(client_socket)
            elif data == 'list':  #列出会议中的client
                self.list(client_socket)
        else:
            print('broadcast')
            self.broadcast(message)

    #quit指令
    def quit(self, client_socket):
        message = ''
        if client_socket == self.hoster:
            #通知所有连接会议取消，再断开连接
            for client in self.clients:
                message = 'quit conference'
                message_with_id = f"{self.conference_id}:quit:{message}"
                client.send(message_with_id.encode())
                print(f"[*] Quitting client {client}")
                self.remove_client(client)
            self.is_active = False
        else:
            message = 'quit conference'
            message_with_id = f"{self.conference_id}:quit:{message}"
            client_socket.send(message_with_id.encode())
            self.remove_client(client_socket)

    #cancel指令
    def cancel(self, client_socket):
        message = ''
        if client_socket == self.hoster:
            # 通知所有连接会议取消，再断开连接
            for client in self.clients:
                message = 'cancel conference'
                message_with_id = f"{self.conference_id}:cancel:{message}"
                client.send(message_with_id.encode())
                self.remove_client(client)
            self.is_active = False
        else:
            message = 'You arent hoster to cancel conference'
            message_with_id = f"{self.conference_id}:uncancel:{message}"
            client_socket.send(message_with_id.encode())

    #list指令
    def list(self, client_socket):
        message = ''
        for client in self.clients:
            message += str(client) + '\n'
        message_with_id = f"{self.conference_id}:list:{message}"
        client_socket.send(message_with_id.encode())

    #broadcast指令
    def broadcast(self, message):
        print(f"[*] Broadcasting message: {message}")
        """Broadcast a message to all clients in the conference."""
        print(self.clients.__len__())
        for client in self.clients:
            try:
                message_with_id = f"{self.conference_id}:broadcast:{message}"
                encoded_message = message_with_id.encode('utf-8')
                client.sendall(encoded_message)
                print(f"[*] Broadcasted message to client {client}: {message}")
            except Exception as e:
                print(f"Failed to send message to client: {e}")

    #help指令
    def help(self, client_socket):
        message = """
        quit           : quit an on-going conference
        cancel         : cancel your on-going conference (only the manager)
        list           : list all clients in the conference
        """
        message_with_id = f"{self.conference_id}:help:{message}"
        client_socket.send(message_with_id.encode())

    def start(self):
        """Start the conference server."""
        print(f"[*] Conference {self.conference_id} started on port {self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"[*] Accepted connection from {addr}")
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            if not self.is_active:
                break
            #检查是否有client断开连接
            for client_socket in self.clients:
                if not client_socket:
                    self.remove_client(client_socket)

        print(f"[*] Conference {self.conference_id} closed")
        self.server_socket.close()
