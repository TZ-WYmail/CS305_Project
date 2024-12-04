import socketio


class Master_Server:
    def __init__(self):
        # 创建Socket.IO服务器实例
        self.sio = socketio.Server(cors_allowed_origins='*')
        self.app = socketio.WSGIApp(self.sio)

        # 指令列表
        self.commands = {
            'help': '显示帮助信息',
            'create': '创建一个新的房间',
            'join': '加入一个已有的房间',
            'quit': '退出当前房间或程序',
            'list': '列出所有可用的房间',
        }
        #房间字典
        self.rooms = {}
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)

        #服务器交互事件处理
        self.sio.on('command_message', self.handle_command_message)
        #服务器交互事件处理
        self.sio.on('connect_message', self.handle_connect_message)

        #聊天事件处理
        self.sio.on('chat_message', self.handle_chat_message)
        self.sio.on('video_message', self.handle_video_message)
        self.sio.on('audio_message', self.handle_audio_message)

    #随机的生成一个九位数的room_id
    def generate_room_id(self):
        import random
        #判断是否存在重复的room_id
        room_id = str(random.randint(100000000, 999999999))
        while str(random.randint(100000000, 999999999)) in self.rooms:
            room_id = str(random.randint(100000000, 999999999))
        return room_id

    #获取当前时间作为时间戳
    def get_timestamp(self):
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    #注册
    def handle_connect(self, sid, environ):
        print(f"用户 {sid} 已连接")

    def handle_disconnect(self, sid):
        print(f"用户 {sid} 已断开连接")
        # 创建房间ID的列表，以便在遍历时可以安全地修改self.rooms字典
        for room_id in list(self.rooms.keys()):
            if self.rooms[room_id]['host'] == sid:
                # 如果用户是房间的host，则移除房间中的所有用户，并删除房间
                for user in self.rooms[room_id]['users'][:]:
                    self.sio.leave_room(user, room_id)
                    for user in self.rooms[room_id]['users']:
                        self.sio.emit('chat_message', {'user': user, 'timestamp': self.get_timestamp(),
                                                       'message': user + ' 取消了会议'},
                                      room=user)
                    self.sio.emit('command_message', {'user': user, 'command': 'quit', 'room_id': room_id}, room=user)
                del self.rooms[room_id]  # 删除房间
            else:
                # 如果用户不是房间的host，仅将用户从房间中移除
                if sid in self.rooms[room_id]['users']:
                    self.rooms[room_id]['users'].remove(sid)
                    self.sio.leave_room(sid, room_id)
                    for user in self.rooms[room_id]['users']:
                        if user != sid:
                            self.sio.emit('chat_message', {'user': user, 'timestamp': self.get_timestamp(),
                                                           'message': user + ' 断开了连接'}, room=user)

    #服务器交互事件实现
    #文本消息处理
    def handle_connect_message(self, sid, data):
        print(f"用户 {sid} 发送消息: {data['message']}")
        self.sio.emit('connect_message', {'user': sid, 'timestamp': self.get_timestamp(), 'message': data['message']},
                      room=sid)

    #命令消息处理
    def handle_command_message(self, sid, data):
        print(f"用户 {sid} 发送命令: {data['command']}")
        command = data['command']

        if command == 'create':
            room_id = self.generate_room_id()
            if room_id in self.rooms:
                self.sio.emit('error_message',
                              {'user': sid, 'timestamp': self.get_timestamp(), 'message': '房间已存在'}, room=room_id)
            else:
                self.rooms[room_id] = {'host': sid, 'users': [sid]}
                #将用户的id作为添加到房间中
                self.sio.enter_room(sid, room_id)
                self.sio.emit('command_message',
                              {'user': sid, 'timestamp': self.get_timestamp(), 'command': 'create', 'room_id': room_id},
                              room=room_id)

        elif command == 'join':
            room_id = data['room_id']
            if room_id in self.rooms:
                self.rooms[room_id]['users'].append(sid)
                self.sio.enter_room(sid, room_id)
                self.sio.emit('command_message',
                              {'user': sid, 'timestamp': self.get_timestamp(), 'command': 'join', 'room_id': room_id})
                #告知该房间的其他用户，这个用户加入了房间
                for user in self.rooms[room_id]['users']:
                    if user != sid:
                        self.sio.emit('chat_message',
                                      {'user': user, 'timestamp': self.get_timestamp(), 'message': user + '加入了房间'},
                                      room=user)
            else:
                self.sio.emit('error_message',
                              {'user': sid, 'timestamp': self.get_timestamp(), 'message': '房间不存在'}, room=sid)

        elif command == 'quit':
            room_id = data['room_id']
            #如果用户时host，将全部用户移除房间并删除房间
            if room_id in self.rooms:
                if self.rooms[room_id]['host'] == sid:
                    for user in self.rooms[room_id]['users']:
                        self.sio.leave_room(user, room_id)
                        # 告诉房间内的其他人退出消息
                        for user in self.rooms[room_id]['users']:
                            self.sio.emit('chat_message', {'user': user, 'timestamp': self.get_timestamp(),
                                                           'message': user + ' 取消了会议'},
                                          room=user)
                        self.sio.emit('command_message',
                                      {'user': user, 'timestamp': self.get_timestamp(), 'command': 'quit',
                                       'room_id': room_id},
                                      room=user)
                    del self.rooms[room_id]
                else:
                    self.rooms[room_id]['users'].remove(sid)
                    self.sio.leave_room(sid, room_id)
                self.sio.emit('command_message',
                              {'user': sid, 'timestamp': self.get_timestamp(), 'command': 'quit', 'room_id': room_id},
                              room=sid)
                #告诉房间内的其他人退出消息
                for user in self.rooms[room_id]['users']:
                    if user != sid:
                        self.sio.emit('chat_message', {'user': user, 'timestamp': self.get_timestamp(),
                                                       'message': user + ' 离开了房间'}, room=user)
            else:
                self.sio.emit('error_message',
                              {'user': sid, 'timestamp': self.get_timestamp(), 'message': '房间不存在'}, room=sid)

        elif command == 'list':  #返回给查询的那个用户
            room_list = list(self.rooms.keys())
            self.sio.emit('command_message',
                          {'user': sid, 'command': 'list', 'timestamp': self.get_timestamp(), 'message': room_list},
                          room=sid)

        elif command == 'help':
            help_message = '可用命令:\n'
            for cmd, desc in self.commands.items():
                help_message += f'{cmd}: {desc}\n'
            self.sio.emit('command_message',
                          {'user': sid, 'command': 'help', 'timestamp': self.get_timestamp(), 'message': help_message},
                          room=sid)

    #聊天事件实现
    def handle_chat_message(self, sid, data):
        print(f"用户 {sid} 发送消息: {data['message']}")
        # 广播消息给所在房间的全体用户
        self.sio.emit('chat_message', {'user': sid, 'timestamp': self.get_timestamp(), 'message': data['message']},
                      room=data['room_id'])

    def handle_video_message(self, sid, data):
        print(f"用户 {sid} 发送视频: {data['message']}")
        # 广播消息给所有用户
        self.sio.emit('video_message', {'user': sid, 'timestamp': self.get_timestamp(), 'message': data['message']},
                      room=data['room_id'])

    def handle_audio_message(self, sid, data):
        print(f"用户 {sid} 发送音频: {data['message']}")
        # 广播消息给所有用户
        self.sio.emit('audio_message', {'user': sid, 'timestamp': self.get_timestamp(), 'message': data['message']},
                      room=data['room_id'])

    def run(self, host='0.0.0.0', port=5000):
        import eventlet
        eventlet.wsgi.server(eventlet.listen((host, port)), self.app)


# 启动服务器
if __name__ == '__main__':
    server = Master_Server()
    server.run()
