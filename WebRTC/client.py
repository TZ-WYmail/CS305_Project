import asyncio
import sys
import cv2
import socketio
import threading
from aiortc import (RTCPeerConnection, RTCSessionDescription, RTCIceCandidate,
                   RTCConfiguration, RTCIceServer)  

enable_p2p = False  

class client:
    def __init__(self):
        #窗口
        self.Ui_Remote_meeting_room = None
        self.UI_ChatRoomWindow = None
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
        #房间列表
        self.refresh_room = False
        self.room_list = []
        self.is_in_room = False
        self.room_id = None

        #房间通信事件
        self.main_sio.on('system_notification', self.on_system_notification)
        self.main_sio.on('chat_message', self.on_chat_message)
        self.main_sio.on('video_message', self.on_video_message)
        self.main_sio.on('audio_message', self.on_audio_message)

        #成员列表
        self.refresh_member = False
        self.member_list = []

        #错误处理
        self.is_error = False
        self.error_message=''

        # WebRTC 相关,只保留必要的
        self.pc = None
        self.data_channel = None
        
        # P2P信令事件 - 修改处理方式
        self.main_sio.on('offer', lambda data: asyncio.run_coroutine_threadsafe(self.on_offer(data), self.loop))
        self.main_sio.on('answer', lambda data: asyncio.run_coroutine_threadsafe(self.on_answer(data), self.loop))
        self.main_sio.on('ice_candidate', lambda data: asyncio.run_coroutine_threadsafe(self.on_ice_candidate(data), self.loop))

        self.loop = None  # 添加事件循环属性
        self.message_separator = b'\x00\x01\x02\x03'  # 使用特殊的字节序列作为分隔符
        global enable_p2p  # 使用全局变量
        self.enable_p2p = enable_p2p  # 添加 P2P 控制开关

    #处理连接消息,包括和服务器的文本传输测试
    def on_connect_message(self, data):
        print(f"连接成功: {data['message']}")

    #处理错误消息
    def on_error_message(self, data):
        print(f"错误:{data['timestamp']}: {data['message']}")
        self.is_error = True
        self.error_message = data['message']

    #处理command信息
    def on_command(self, data):
        command = data['command']
        timestamp = data.get('timestamp', '')  # 使用 get 方法提供默认值
        
        if command == 'help':
            print(f"{timestamp}:帮助信息: {data['message']}")
        elif command == 'create':
            print(f"{timestamp}:创建成功: {data['room_id']}")
            self.is_in_room = True
            self.room_id = data['room_id']
        elif command == 'join':
            print(f"{timestamp}:加入成功:{data['room_id']}")
            self.is_in_room = True
            self.room_id = data['room_id']
        elif command == 'quit':
            room_id = data.get('room_id', '')  # 也为 room_id 提供默认值
            print(f"{timestamp}:退出成功 {room_id}")
            self.UI_ChatRoomWindow.MainWindow.showMainWindow()
            self.is_in_room = False
            self.room_id = None
        elif command == 'list':
            print(f"{timestamp}:房间列表: {data['message']}")
            self.room_list = data['message']
            self.refresh_room = True
        else:
            print(f"{timestamp}:未知命令:{command}")

    #处理聊天信息
    #处理系统通知
     

    def on_system_notification(self, data):  #聊天室中的系统通知，包括用户加入和退出，更新用户列表
        print(f"{data['timestamp']}:系统通知: {data['message']}")
        self.UI_ChatRoomWindow.show_chat_message(f"{data['timestamp']}:系统通知: {data['message']}")
        #处理用户列表的跟新（join，create，quit，disconnect），这里直接用command作为key
        if 'command' in data and data['command'] == 'list':
            self.member_list = data['members']

            print(f"{data['timestamp']}:用户列表: {data['members']}")

    def on_chat_message(self, data):
        print(f"{data['timestamp']}:{data['user']}: {data['chat_message']}")
        self.UI_ChatRoomWindow.show_chat_message('<<' + data['timestamp'] + '>>' + data['user'] + ':' + data['chat_message'])

    # def send_chat_message(self, message):
    #     self.main_sio.emit('chat_message', {'room_id': self.room_id, 'chat_message': message})

    def on_video_message(self, data):
        sid=data['user']
        index=0
        count=-1
        for member in self.member_list:
            count+=1
            if member == sid:
                index = count
        self.UI_ChatRoomWindow.show_video_message(index, data['video_message'])

    def send_video_message(self,video_message):
        self.main_sio.emit('video_message', {'room_id': self.room_id, 'video_message': video_message})


    #处理音频信息
    def on_audio_message(self, data):
        self.UI_ChatRoomWindow.show_audio_message(data['audio_message'])

    def send_audio_message(self,audio_message):
        self.main_sio.emit('audio_message', {'room_id': self.room_id, 'audio_message': audio_message})

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
            # else:
            #     self.main_sio.emit('chat_message', {'room_id': self.room_id, 'message': message})
            #其他的音频视频传输

    async def create_peer_connection(self):
        config = RTCConfiguration([
            RTCIceServer(urls=['stun:49.235.44.81:3478'])
        ])

        pc = RTCPeerConnection(configuration=config)
        print(f"Created peer connection: {pc}")
        self.data_channel = pc.createDataChannel('mediaChannel')
        self.data_channel.on('message', self.on_data_channel_message)
        @pc.on('connectionstatechange')
        def on_connectionstatechange():
            print(f"Connection state changed to: {pc.connectionState}")

        @pc.on('signalingstatechange')
        def on_signalingstatechange():
            print(f"Signaling state changed to: {pc.signalingState}")

        @pc.on('iceconnectionstatechange')
        def on_iceconnectionstatechange():
            print(f"ICE connection state changed to: {pc.iceConnectionState}")

        @pc.on('icegatheringstatechange')
        def on_icegatheringstatechange():
            print(f"ICE gathering state changed to: {pc.iceGatheringState}")

        @pc.on('datachannel')
        def on_datachannel(channel):
            print(f"Received data channel: {channel}")
            channel.on('message', self.on_data_channel_message)  
            self.data_channel = channel
            
        @pc.on('icecandidate')
        def on_ice_candidate(candidate):
            print(f"Received ICE candidate: {candidate}")
            if candidate:
                self.main_sio.emit('ice_candidate', {
                    'room_id': self.room_id,
                    'candidate': candidate.toJSON()
                })
                
        self.pc = pc
        return pc

    def on_data_channel_message(self, message):
        try:
            if isinstance(message, bytes):
                # 解析消息
                sid_len = int.from_bytes(message[:4], byteorder='big')
                parts = message[4:].split(self.message_separator, 2)
                if len(parts) == 3:
                    sid = parts[0].decode()
                    msg_type = parts[1].decode()
                    data = parts[2]
                    
                    try:
                        index = self.member_list.index(sid)
                    except ValueError:
                        index = 0  
                    print(index,sid,msg_type)
                    if msg_type == 'VID:':
                        self.UI_ChatRoomWindow.show_video_message(index, data)
                    elif msg_type == 'AUD:':
                        self.UI_ChatRoomWindow.show_audio_message(data)
        except Exception as e:
            print(f"Error handling data channel message: {e}")

    def send_p2p_message(self, msg_type, data):
        if not self.enable_p2p or not self.data_channel or self.data_channel.readyState != 'open':
            return False
            
        try:
            sid = self.main_sio.sid.encode()
            sid_len = len(sid).to_bytes(4, byteorder='big')
            message = sid_len + sid + self.message_separator + msg_type.encode() + self.message_separator + data
            
            future = asyncio.run_coroutine_threadsafe(
                self._send_p2p_message_async(message),
                self.loop
            )
            self.on_data_channel_message(message)
            return future.result()
        except Exception as e:
            print(f"Error sending P2P message: {e}")
            return False

    async def _send_p2p_message_async(self, message):
        try:
            self.data_channel.send(message)
            return True
        except Exception as e:
            print(f"Error in async send: {e}")
            return False

    async def on_offer(self, data):
        try:
            if not self.pc:
                self.pc = await self.create_peer_connection()
            
            offer = RTCSessionDescription(
                sdp=data['sdp'],
                type=data['type']
            )
            await self.pc.setRemoteDescription(offer)
            
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            
            self.main_sio.emit('answer', {
                'room_id': self.room_id,
                'sdp': self.pc.localDescription.sdp,
                'type': self.pc.localDescription.type
            })
            
        except Exception as e:
            print(f"Error handling offer: {e}")

    async def on_answer(self, data):
        try:
            answer = RTCSessionDescription(
                sdp=data['sdp'],
                type=data['type']
            )
            await self.pc.setRemoteDescription(answer)
        except Exception as e:
            print(f"Error handling answer: {e}")

    async def on_ice_candidate(self, data):
        try:
            candidate = RTCIceCandidate(
                component=data['candidate'].get('component'),
                foundation=data['candidate'].get('foundation'),
                ip=data['candidate'].get('ip'),
                port=data['candidate'].get('port'),
                priority=data['candidate'].get('priority'),
                protocol=data['candidate'].get('protocol'),
                type=data['candidate'].get('type')
            )
            await self.pc.addIceCandidate(candidate)
        except Exception as e:
            print(f"Error handling ICE candidate: {e}")

    # 建立P2P连接
    async def setup_peer_connection(self, is_initiator=False):
        try:
            if not self.pc:
                print(f"Creating peer connection")
                self.pc = await self.create_peer_connection()
            if is_initiator:
                offer = await self.pc.createOffer()
                await self.pc.setLocalDescription(offer)
                self.main_sio.emit('offer', {
                    'room_id': self.room_id,
                    'sdp': self.pc.localDescription.sdp,
                    'type': self.pc.localDescription.type
                })
        except Exception as e:
            print(f"Error setting up peer connection: {e}")

    async def send_offer(self, room_id, offer):
        try:
            print("Sending offer")
            self.main_sio.emit('offer', {
                'room_id': room_id,
                'sdp': offer.sdp,
                'type': offer.type
            })
        except Exception as e:
            print(f"Error sending offer: {e}")

    async def send_answer(self, room_id, answer):
        try:
            print("Sending answer")
            self.main_sio.emit('answer', {
                'room_id': room_id,
                'sdp': answer.sdp,
                'type': answer.type
            })
        except Exception as e:
            print(f"Error sending answer: {e}")

    async def send_ice_candidate(self, room_id, candidate):
        try:
            print("Sending ICE candidate")
            self.main_sio.emit('ice_candidate', {
                'room_id': room_id,
                'candidate': candidate.toJSON() if hasattr(candidate, 'toJSON') else candidate
            })
        except Exception as e:
            print(f"Error sending ICE candidate: {e}")

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        def run_event_loop():
            self.loop.run_forever()
            
        threading.Thread(target=run_event_loop, daemon=True).start()
        
        self.main_sio.connect('http://localhost:5000')
        threading.Thread(target=self.main_sio.wait, daemon=True).start()
        # try:
        #     while True:
        #         message = input("请输入消息: ")
        #         self.handle_input(message)
        # finally:
        #     self.main_sio.disconnect()
    # 界面绑定.



if __name__ == '__main__':
    client = client()
    client.run()
