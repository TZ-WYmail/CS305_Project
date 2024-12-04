import sys
import socketio
import threading


class client:
    def __init__(self):
        self.main_sio = socketio.Client()
        #指令列表
        self.commands = {
            'help': '显示帮助信息',
            'create': '创建一个新的房间',
            'join': '加入一个已有的房间',
            'quit': '退出当前房间或程序',
            'list': '列出所有可用的房间',
        }

        # 主服务器事件
        # 主服务器通信测试
        self.main_sio.on('connect_message', self.on_connect_message)
        #处理返回的错误消息
        self.main_sio.on('error_message', self.on_error_message)
        # 命令返回处理
        self.main_sio.on('command_message', self.on_command)

        #房间信息
        self.is_in_room = False
        self.room_id = None

        self.main_sio.on('chat_message', self.on_chat_message)
        self.main_sio.on('video_message', self.on_video_message)
        self.main_sio.on('audio_message', self.on_audio_message)

    #处理连接消息,包括和服务器的文本传输测试
    def on_connect_message(self, data):
        print(f"连接成功: {data['message']}")

    #处理错误消息
    def on_error_message(self, data):
        print(f"错误:{data['timestamp']}: {data['message']}")

    #处理command信息
    def on_command(self, data):
        command = data['command']
        if command == 'help':
            print(f"{data['timestamp']}:帮助信息: {data['message']}")
        elif command == 'create':
            print(f"{data['timestamp']}:创建成功: {data['room_id']}")
            self.is_in_room = True
            self.room_id = data['room_id']
        elif command == 'join':
            print(f"{data['timestamp']}:加入成功:{data['room_id']}")
            self.is_in_room = True
            self.room_id = data['room_id']
        elif command == 'quit':
            print(f"{data['timestamp']}:退出成功 {data['room_id']}")
            self.is_in_room = False
            self.room_id = None
        elif command == 'list':
            print(f"{data['timestamp']}:房间列表: {data['message']}")
        else:
            print(f"{data['timestamp']}:未知命令:{command}")

    #处理聊天信息
    def on_chat_message(self, data):
        print(f"{data['timestamp']}:{data['user']}: {data['message']}")

    #处理视频信息
    def on_video_message(self, data):
        print(f"{data['user']}: {data['message']}")

    #处理音频信息
    def on_audio_message(self, data):
        print(f"{data['user']}: {data['message']}")

    #处理输入的消息
    def handle_input(self, message):
        #判断是否为指令
        if not self.is_in_room:
            print(f"{message}")
            if message in self.commands:
                self.main_sio.emit('command_message', {'command': message})
            elif message.startswith('join'):
                room_id = message.split(' ')[1]
                self.main_sio.emit('command_message', {'command': 'join', 'room_id': room_id})
            else:
                self.main_sio.emit('connect_message', {'message': message})
        else:
            #判断是否为‘quit’
            if message == 'quit':
                self.main_sio.emit('command_message', {'command': 'quit', 'room_id': self.room_id})
            else:
                self.main_sio.emit('chat_message', {'room_id': self.room_id, 'message': message})
            #其他的音频视频传输

    def run(self):
        self.main_sio.connect('http://localhost:5000')
        threading.Thread(target=self.main_sio.wait, daemon=True).start()

        # try:
        #     while True:
        #         message = input("请输入消息: ")
        #         self.handle_input(message)
        # finally:
        #     self.main_sio.disconnect()


if __name__ == '__main__':
    client = client()
    client.run()
