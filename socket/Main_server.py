import threading
import socket
import random
from Conference import Conference
import config


#用户header
# self.is_connected = False
# self.conference_id = None
# self.is_conference_running = False
# self.is_video = False
# self.is_audio = False
# self.datatype = None  # 数据类型，如 text, audio, video, etc.


class MainServer:
    def __init__(self, main_port):
        self.main_port = main_port
        self.conferences = {}  #会议号+端口号查找client的信息
        self.next_conference_port = 12000  # 假设会议端口从12000开始

    def generate_random_conference_id(self):
        """生成一个随机的六位数会议ID"""
        return random.randint(100000, 999999)

    #处理聊天室创建的逻辑
    def create_conference(self, client_socket):
        conference_id = self.generate_random_conference_id()
        while conference_id in self.conferences:
            conference_id = self.generate_random_conference_id()
        conference_port = self.next_conference_port
        print(conference_id)
        print(conference_port)
        self.next_conference_port += 1
        new_conference = Conference(conference_id,conference_port,client_socket)
        # 将新创建的会议信息添加到字典中
        self.conferences[conference_id] = {
            'port': conference_port,
            'conference': new_conference,  # 存储会议对象
            'clients': []  # 存储客户端列表
        }
        print(f"create:{conference_id}:{conference_port}")
        client_socket.send(f"create:{conference_id}:{conference_port}".encode())
        print('send create')
        self.conferences[conference_id]['clients'].append(client_socket)
        # 在新线程中启动会议
        conference_thread = threading.Thread(target=new_conference.start)
        conference_thread.start()


    #处理用户加入会议
    def join_conference(self, client_socket, conference_id):
        """加入一个已有的会议"""
        if int(conference_id) in self.conferences:
            # 发送会议端口给客户端
            client_socket.send(('join:'+conference_id+':'+str(self.conferences[int(conference_id)]['port'])).encode())
            print('join:'+conference_id+':'+str(self.conferences[int(conference_id)]['port']))
            #将请求加入者添加到会议
            self.conferences[int(conference_id)]['clients'].append(client_socket)
        else:
            # 发送错误消息给客户端
            client_socket.send("Conference not found".encode())
            print(f"[*] Conference with ID: {conference_id} not found")

    #处理用户查询可加入会议逻辑
    def list_conferences(self, client_socket):
        """列出所有可用的会议"""
        available_conferences = [f"ID:{conference_id}" for conference_id, _ in self.conferences.items()]
        message = "\n".join(available_conferences)
        client_socket.send(('list:'+message).encode())


    #处理用户退出会议逻辑
    def quit_conference(self, client_socket, conference_id):
        """退出当前会议"""
        conference_id=int(conference_id)
        if conference_id in self.conferences:
            self.conferences[conference_id]['clients'].remove(client_socket)
            if not self.conferences[conference_id]['clients']:
                #关闭会议服务器
                self.conferences[conference_id]['conference'].is_active = False
                self.conferences[conference_id]['conference'].server_socket.close()
                del self.conferences[conference_id]
                print(f"[*] Conference with ID: {conference_id} closed.")
                client_socket.send(f"quit:{conference_id}".encode())
            else:
                print(f"[*] User left conference with ID: {conference_id}")
        else:
            client_socket.send("Conference not found".encode())
            print(f"[*] Conference with ID: {conference_id} not found")
    #处理用户帮助逻辑
    def help_command(self, client_socket):
        """处理帮助命令"""
        client_socket.send(('help:' + config.HELP).encode())

    #移除某个聊天室
    def cancel_conference(self, client_socket, conference_id):
        """取消当前会议"""
        conference_id=int(conference_id)
        if conference_id in self.conferences:
            del self.conferences[conference_id]
            print(f"[*] Conference with ID: {conference_id} cancelled.")
            #告知client成功移除
            client_socket.send("Conference cancelled".encode())
        else:
            client_socket.send("Conference not found".encode())

    def handle_client(self, client_socket, addr):
        """处理客户端请求的函数"""
        try:
            while True:
                # 接收客户端发送的数据
                recv_data = client_socket.recv(1024)
                print(recv_data.decode())
                msg = recv_data.decode().split(':')
                is_connected = msg[0]
                conference_id = msg[1]
                is_conference_running = msg[2]
                is_command = msg[3]
                datatype = msg[4]
                data = msg[5]

                # 打印收到的全部信息
                print(f"Is Connected: {is_connected}")
                print(f"Conference ID: {conference_id}")
                print(f"Is Conference Running: {is_conference_running}")
                print(f"Is Command: {is_command}")
                print(f"Data Type: {datatype}")
                if data is not None:
                    print(f"Data: {data}")

                #处理Help命令逻辑
                if is_command == 'True' and data == 'help':
                   print('help')
                   self.help_command(client_socket)

                #处理建立聊天室逻辑
                if is_command == 'True' and is_conference_running == 'False' and data == 'create':
                    print('create')
                    self.create_conference(client_socket)

                #处理查询聊天室逻辑
                if is_command == 'True' and is_conference_running == 'False' and data == 'list':
                    print('list')
                    self.list_conferences(client_socket)

                #处理加入聊天房逻辑
                if is_command == 'True' and is_conference_running == 'False' and data == 'join':
                    print(conference_id)
                    self.join_conference(client_socket, conference_id)

                #处理退出聊天室逻辑
                if is_command == 'True' and is_conference_running == 'False' and data == 'quit':
                    print(conference_id)
                    self.quit_conference(client_socket, conference_id)

                print(f"[*] Received message from {addr[0]}:{addr[1]}: {data}")
        # except Exception as e:
        #     print(f"[*] Error handling client: {e}")
        #     client_socket.close()
        finally:
            client_socket.close()  # 关闭客户端连接
            print(f"[*] Connection with {addr[0]}:{addr[1]} closed.")

    def start_server(self, host='localhost', port=None):
        """启动服务器并监听指定端口"""
        if port is None:
            port = self.main_port
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(5)  # 最大连接数为5
        print(f"[*] Listening on {host}:{port}")

        try:
            while True:
                # 接受客户端连接请求
                client_socket, addr = server.accept()
                print(f"[*] Accepted connection from: {addr[0]}:{addr[1]}")
                # 创建新线程来处理客户端请求
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_handler.start()
        except KeyboardInterrupt:
            print("[*] Server shutting down.")
        finally:
            server.close()


if __name__ == "__main__":
    main_server = MainServer(5555)
    main_server.start_server()
