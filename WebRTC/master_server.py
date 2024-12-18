import socketio
from aiohttp import web
import asyncio

class Master_Server:
    def __init__(self):
        # 创建异步Socket.IO服务器实例
        self.sio = socketio.AsyncServer(cors_allowed_origins='*')
        self.app = web.Application()
        self.sio.attach(self.app)

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

        # WebRTC 信令
        self.sio.on('offer', self.handle_offer)
        self.sio.on('answer', self.handle_answer) 
        self.sio.on('ice_candidate', self.handle_ice_candidate)

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
    async def handle_connect(self, sid, environ):
        print(f"用户 {sid} 已连接")

    async def handle_disconnect(self, sid):
        print(f"用户 {sid} 已断开连接")
        # 创建房间ID的列表，以便在遍历时可以安全地修改self.rooms字典
        for room_id in list(self.rooms.keys()):
            if self.rooms[room_id]['host'] == sid:
                # 如果用户是房间的host，则移除房间中的所有用户，并删除房间
                for user in self.rooms[room_id]['users']:
                    await self.sio.leave_room(user, room_id)
                    await self.sio.emit('system_notification', {'user': user, 'timestamp': self.get_timestamp(),
                                                                'message': user + ' 取消了会议'}, room=user)
                    await self.sio.emit('command_message', {'user': user, 'command': 'quit', 'room_id': room_id},
                                        room=user)
                del self.rooms[room_id]  # 删除房间
            else:
                # 如果用户不是房间的host，仅将用户从房间中移除
                if sid in self.rooms[room_id]['users']:
                    self.rooms[room_id]['users'].remove(sid)
                    await self.sio.leave_room(sid, room_id)
                    for user in self.rooms[room_id]['users']:
                        if user != sid:
                            await self.sio.emit('system_notification',
                                                {'user': user, 'timestamp': self.get_timestamp(), 'command': 'list',
                                                 'message': user + ' 断开了连接',
                                                 'members': self.rooms[room_id]['users']},
                                                room=user)

    #服务器交互事件实现
    #文本消息处理
    async def handle_connect_message(self, sid, data):
        print(f"用户 {sid} 发送消息: {data['message']}")
        await self.sio.emit('connect_message',
                            {'user': sid, 'timestamp': self.get_timestamp(), 'message': data['message']},
                            room=sid)

    #命令消息处理
    async def handle_command_message(self, sid, data):
        print(f"用户 {sid} 发送命令: {data['command']}")
        command = data['command']

        if command == 'create':
            room_id = self.generate_room_id()
            if room_id in self.rooms:
                await self.sio.emit('error_message',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'message': '房间已存在'},
                                    room=room_id)
            else:
                self.rooms[room_id] = {'host': sid, 'users': [sid]}
                await self.sio.enter_room(sid, room_id)
                await self.sio.emit('command_message',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'command': 'create',
                                     'room_id': room_id},
                                    room=sid)
                await self.sio.emit('system_notification',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'command': 'list',
                                     'message': sid + '创建了房间', 'members': self.rooms[room_id]['users']},
                                    room=sid)

        elif command == 'join':
            room_id = data['room_id']
            if room_id in self.rooms:
                self.rooms[room_id]['users'].append(sid)
                await self.sio.enter_room(sid, room_id)
                #告知该用户加入成功
                await self.sio.emit('command_message',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'command': 'join',
                                     'room_id': room_id},
                                    room=sid)
                #告知该房间的其他用户，这个用户加入了房间
                for user in self.rooms[room_id]['users']:
                    await self.sio.emit('system_notification',
                                        {'user': user, 'timestamp': self.get_timestamp(), 'command': 'list',
                                         'message': sid + '加入了房间', 'members': self.rooms[room_id]['users']},
                                        room=user)
            else:
                await self.sio.emit('error_message',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'message': '房间不存在'}, room=sid)

        elif command == 'quit':
            room_id = data['room_id']
            #如果用户时host，将全部用户移除房间并删除房间
            if room_id in self.rooms:
                if self.rooms[room_id]['host'] == sid:
                    for user in self.rooms[room_id]['users']:
                        await self.sio.leave_room(user, room_id)
                        # 告诉房间内的人退出消息
                        await self.sio.emit('system_notification', {'user': user, 'timestamp': self.get_timestamp(),
                                                                    'message': sid + ' 取消了会议'}, room=user)
                        await self.sio.emit('command_message',
                                            {'user': user, 'timestamp': self.get_timestamp(), 'command': 'quit',
                                             'room_id': room_id},
                                            room=user)
                    del self.rooms[room_id]
                else:
                    self.rooms[room_id]['users'].remove(sid)
                    await self.sio.leave_room(sid, room_id)
                    await self.sio.emit('command_message',
                                        {'user': sid, 'timestamp': self.get_timestamp(), 'command': 'quit',
                                         'room_id': room_id},
                                        room=sid)
                    #告诉房间内的其他人退出消息
                    for user in self.rooms[room_id]['users']:
                        if user != sid:
                            await self.sio.emit('system_notification',
                                                {'user': user, 'timestamp': self.get_timestamp(), 'command': 'list',
                                                 'message': sid + ' 离开了房间',
                                                 'members': self.rooms[room_id]['users']},
                                                room=user)
            else:
                await self.sio.emit('error_message',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'message': '房间不存在'}, room=sid)

        elif command == 'list':  #返回给查询的那个用户
            room_list = list(self.rooms.keys())
            await self.sio.emit('command_message',
                                {'user': sid, 'command': 'list', 'timestamp': self.get_timestamp(),
                                 'message': room_list},
                                room=sid)

        elif command == 'help':
            help_message = '可用命令:\n'
            for cmd, desc in self.commands.items():
                help_message += f'{cmd}: {desc}\n'
            await self.sio.emit('command_message',
                                {'user': sid, 'command': 'help', 'timestamp': self.get_timestamp(),
                                 'message': help_message},
                                room=sid)

    #聊天事件实现
    async def handle_chat_message(self, sid, data):
        print(f"用户 {sid} 发送消息: {data['chat_message']}")
        # 广播消息给所在房间的全体用户
        for user in self.rooms[data['room_id']]['users']:
            if self.rooms[data['room_id']]['users'] is not None:
                await self.sio.emit('chat_message',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'chat_message': data['chat_message']},
                                    room=user)

    async def handle_video_message(self, sid, data):
        print(f"[VIDEO] {sid} 发送视频消息")
        # 广播消息给所有用户
        for user in self.rooms[data['room_id']]['users']:
            if self.rooms[data['room_id']]['users'] is not None:
                await self.sio.emit('video_message', {'user': sid, 'timestamp': self.get_timestamp(),
                                                      'video_message': data['video_message']},
                                    room=user)

    async def handle_audio_message(self, sid, data):
        # 广播消息给所有用户
        for user in self.rooms[data['room_id']]['users']:
            if self.rooms[data['room_id']]['users'] is not None:
                await self.sio.emit('audio_message',
                                    {'user': sid, 'timestamp': self.get_timestamp(), 'audio_message': data['audio_message']},
                                    room=user)

    # WebRTC 
    async def handle_offer(self, sid, data):
        room_id = data['room_id']
        if room_id in self.rooms:
            for user in self.rooms[room_id]['users']:
                if user != sid:
                    print(f"[OFFER] Sending to {user}") 
                    await self.sio.emit('offer', data, room=user)

    async def handle_answer(self, sid, data):
        room_id = data['room_id']
        if room_id in self.rooms:
            for user in self.rooms[room_id]['users']:
                if user != sid:
                    print(f"[ANSWER] Sending to {user}")
                    await self.sio.emit('answer', data, room=user)

    async def handle_ice_candidate(self, sid, data):
        room_id = data['room_id']
        if room_id in self.rooms:
            for user in self.rooms[room_id]['users']:
                if user != sid:
                    print(f"[ICE] Sending to {user}")
                    await self.sio.emit('ice_candidate', data, room=user)

    def run(self, host='localhost', port=5000):
        web.run_app(self.app, host=host, port=5000)

# 启动服务器
if __name__ == '__main__':
    server = Master_Server()
    server.run()
