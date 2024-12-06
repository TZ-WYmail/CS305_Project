import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLineEdit, QTextEdit,
                            QLabel)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QMetaObject, Q_ARG
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from aiortc import (RTCPeerConnection, RTCSessionDescription, 
                   MediaStreamTrack, VideoStreamTrack, RTCIceCandidate,
                   RTCConfiguration, RTCIceServer, AudioStreamTrack) 
from aiortc.contrib.media import MediaPlayer, MediaRecorder
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.contrib.media import MediaRelay
from aiortc.mediastreams import MediaStreamTrack, MediaStreamError
import socketio
import asyncio
import sys
import os
import av
import cv2
import numpy as np
import cv2
import numpy as np
import asyncio
import fractions
import time
from av import VideoFrame

class SocketThread(QThread):
    message_received = pyqtSignal(dict)
    connected = pyqtSignal()
    ready_signal = pyqtSignal()
    offer_received = pyqtSignal(dict)
    answer_received = pyqtSignal(dict)
    candidate_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.sio = socketio.Client()
        self.setup_events()
    #处理接受的消息
    def setup_events(self):
        self.sio.on('message', self._on_message)
        self.sio.on('ready', self._on_ready)
        self.sio.on('offer', self._on_offer)
        self.sio.on('answer', self._on_answer)
        self.sio.on('ice_candidate', self._on_ice_candidate)
    #接受消息后将其emit给前端槽函数
    def _on_message(self, data):
        self.message_received.emit(data)

    def _on_ready(self):
        self.ready_signal.emit()

    def _on_offer(self, data):
        self.offer_received.emit(data)

    def _on_answer(self, data):
        self.answer_received.emit(data)

    def _on_ice_candidate(self, data):
        self.candidate_received.emit(data)

    def connect_to_server(self, url):
        try:
            self.sio.connect(url)
            self.connected.emit()
        except Exception as e:
            print(f"Connection error: {e}")

    def join_room(self, room):
        self.sio.emit('join', {'room': room})

    def send_message(self, data):
        self.sio.emit('message', data)

class VideoWidget(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.image_label = QLabel()
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        # 设置最小尺寸以保证视频显示区域合适
        self.setMinimumSize(320, 240)

    def update_frame(self, frame):
        height, width = frame.shape[:2]
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaled(320, 240, Qt.KeepAspectRatio))

class DummyVideoTrack(MediaStreamTrack):
    kind = "video"
    
    def __init__(self):
        super().__init__()
        self.running = True
        # 创建黑色帧
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
    async def recv(self):
        if not self.running:
            raise MediaStreamError
            
        # 创建VideoFrame
        video_frame = VideoFrame.from_ndarray(self.frame, format="rgb24") 
        video_frame.pts = int(time.time() * 1000)
        video_frame.time_base = fractions.Fraction(1, 1000)
        
        return video_frame
        
    def stop(self):
        self.running = False
class CameraStreamTrack(MediaStreamTrack):
    kind = "video"
    
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        print(self.cap)
        if not self.cap.isOpened():
            print("无法打开摄像头，使用DummyVideoTrack")
            self.use_dummy = True
            self.dummy_track = DummyVideoTrack()
        else:
            self.use_dummy = False

    async def recv(self):
        if self.use_dummy:
            return await self.dummy_track.recv()
        else:
            ret, frame = self.cap.read()
            if not ret:
                raise MediaStreamError
            video_frame = VideoFrame.from_ndarray(frame, format="bgr24") 
            video_frame.pts = int(time.time() * 1000)
            video_frame.time_base = fractions.Fraction(1, 1000)
            return video_frame

    def stop(self):
        if self.use_dummy:
            self.dummy_track.stop()
        else:
            if self.cap and self.cap.isOpened():
                self.cap.release()
        super().stop()
class VideoUpdateThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, video_track):
        super().__init__()
        self.video_track = video_track
        self.running = True

    async def receive_frames(self):
        while self.running:
            try:
                frame = await self.video_track.recv()
                if frame:
                    img = frame.to_ndarray(format="rgb24")
                    self.frame_ready.emit(img)
                await asyncio.sleep(1/30)  # 30fps
            except Exception as e:
                print(f"接收视频帧错误: {e}")
                if not self.running:
                    break
                await asyncio.sleep(0.1)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.receive_frames())
        finally:
            loop.close()

    def stop(self):
        self.running = False

class WebRTCManager:
    def __init__(self, loop):
        self.pc = None
        self.loop = loop
        self.video_track = None
        self.audio_track = None
        self._setup_ice_servers()
        
    def _setup_ice_servers(self):
        self.config = RTCConfiguration([
            RTCIceServer(urls=['stun:49.235.44.81:3478'])
        ])
        
    async def create_peer_connection(self):
        """创建新的 PeerConnection 实例"""
        if self.pc:
            await self.close_connection()
            
        self.pc = RTCPeerConnection(configuration=self.config)
        return self.pc
        
    async def close_connection(self):
        """关闭当前连接"""
        if self.pc:
            await self.pc.close()
            self.pc = None
            await asyncio.sleep(0.5)
            
    def add_track(self, track):
        """添加媒体轨道"""
        if self.pc and track:
            self.pc.addTrack(track)
            
    async def create_and_send_offer(self):
        """创建并返回 offer"""
        if not self.pc:
            raise Exception("No PeerConnection available")
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        return offer
        
    async def handle_remote_description(self, sdp, type_):
        """处理远程 SDP"""
        if not self.pc:
            raise Exception("No PeerConnection available")
        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=sdp, type=type_)
        )
        
    async def create_and_send_answer(self):
        """创建并返回 answer"""
        if not self.pc:
            raise Exception("No PeerConnection available")
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        return answer

class MediaTrackManager:
    def __init__(self):
        self.video_track = None
        self.audio_track = None
        self.dummy_video = DummyVideoTrack()
        self.dummy_audio = AudioStreamTrack()
        self.dummy_audio.enabled = False
        
    def get_video_track(self, enabled=False):
        """获取视频轨道，enabled=True 返回摄像头流，False 返回黑屏流"""
        if enabled:
            if not self.video_track:
                self.video_track = CameraStreamTrack()
            return self.video_track
        return self.dummy_video
        
    def get_audio_track(self, enabled=False):
        """获取音频轨道，enabled=True 返回麦克风流，False 返回静音流"""
        if enabled:
            if not self.audio_track:
                self.audio_track = AudioStreamTrack()
            return self.audio_track
        return self.dummy_audio

    def stop_all(self):
        """停止所有轨道"""
        if self.video_track:
            self.video_track.stop()
        if self.audio_track:
            self.audio_track.stop()
        self.dummy_video.stop()
        self.dummy_audio.stop()

class WebRTCClient(QMainWindow):

    start_remote_video_signal = pyqtSignal()
    start_remote_audio_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('P2P Video Chat')
        self.socket_thread = SocketThread()
        self.pc = None
        self.local_video = None
        self.remote_video = None
        self.video_track = None 
        self.audio_track = None
        self.video_thread = None
        self.remote_video_thread = None
        self.media_relay = MediaRelay()
        self.is_room_joined = False
        self.is_video_enabled = False
        self.is_audio_enabled = False
        self.server_connected = False
        self.remote_audio_player = QMediaPlayer()
        
        # 创建事件循环
        self.loop = asyncio.new_event_loop()
        
        #连接槽函数
        self.start_remote_video_signal.connect(self.start_remote_video)
        self.start_remote_audio_signal.connect(self.start_remote_audio)

        # 创建并启动事件循环线程
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()
        
        self.setup_ui()
        self.setup_socket_signals()
        self.webrtc = WebRTCManager(self.loop)
        self.media_manager = MediaTrackManager()
        self.setup_default_tracks()

    def setup_default_tracks(self):
        """初始化默认的媒体轨道（黑屏和静音）"""
        # 确保一开始就有默认轨道
        self.video_track = self.media_manager.get_video_track(False)  # 默认黑屏
        self.audio_track = self.media_manager.get_audio_track(False)  # 默认静音

    def start_remote_video(self):
        if self.remote_video and not self.remote_video_thread:
            self.remote_video_thread = VideoUpdateThread(self.remote_video)
            self.remote_video_thread.frame_ready.connect(self.update_remote_frame)
            self.remote_video_thread.start()

    def start_remote_audio(self):
        if self.remote_audio and not self.remote_audio_player:
            # 初始化音频播放器等逻辑
            pass


    def _run_event_loop(self):
        """在独立线程中运行事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 视频区域
        video_layout = QHBoxLayout()
        self.local_video_widget = VideoWidget("本地视频")
        self.remote_video_widget = VideoWidget("远程视频")
        video_layout.addWidget(self.local_video_widget)
        video_layout.addWidget(self.remote_video_widget)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.video_button = QPushButton('开启视频')
        self.audio_button = QPushButton('开启音频')
        self.video_button.clicked.connect(self.toggle_video)
        self.audio_button.clicked.connect(self.toggle_audio)
        control_layout.addWidget(self.video_button)
        control_layout.addWidget(self.audio_button)
        
        # 房间控制
        room_layout = QHBoxLayout()
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText('输入房间号')
        self.join_button = QPushButton('加入房间')
        self.join_button.clicked.connect(self.join_room)
        room_layout.addWidget(self.room_input)
        room_layout.addWidget(self.join_button)
        
        # 消息区域
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        
        # 消息输入
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText('输入消息')
        self.send_button = QPushButton('发送')
        self.send_button.clicked.connect(self.send_message)
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)
        
        layout.addLayout(video_layout)
        layout.addLayout(control_layout)
        layout.addLayout(room_layout)
        layout.addWidget(self.message_display)
        layout.addLayout(message_layout)

        # 更新按钮状态
        self.video_button.setEnabled(False)  
        self.audio_button.setEnabled(False)
        self.video_button.setText('开启视频')
        self.audio_button.setText('开启音频')

        # 添加远程音频播放
        self.remote_audio_player.setMedia(QMediaContent())
        self.remote_audio_player.setVolume(100)

    def setup_socket_signals(self):
        self.socket_thread.message_received.connect(self.on_message)
        self.socket_thread.ready_signal.connect(self.on_ready)
        self.socket_thread.offer_received.connect(self.handle_offer)
        self.socket_thread.answer_received.connect(self.on_answer)
        self.socket_thread.candidate_received.connect(self.on_ice_candidate)
        
    def join_room(self):
        if not self.is_room_joined:
            try:
                room = self.room_input.text()
                if not room:
                    print("请输入房间号")
                    return
                
                if not self.server_connected:
                    self.socket_thread.connect_to_server('http://localhost:5000')
                    self.server_connected = True
                
                # 确保先创建新的 PeerConnection
                self.create_new_peer_connection()
                self.socket_thread.join_room(room)
                self.is_room_joined = True
                self.join_button.setText('已加入房间')
                self.join_button.setEnabled(False)
                self.room_input.setEnabled(False)
                self.video_button.setEnabled(True)
                self.audio_button.setEnabled(True)
                
            except Exception as e:
                print(f"加入房间失败: {e}")

    def create_new_peer_connection(self):
        """创建新的 PeerConnection 实例"""
        async def setup_pc():
            try:
                pc = await self.webrtc.create_peer_connection()
                
                @pc.on('connectionstatechange')
                def on_connectionstatechange():
                    print(f"连接状态变更: {pc.connectionState}")
                    
                @pc.on('signalingstatechange')    
                def on_signalingstatechange():
                    print(f"信令状态变更: {pc.signalingState}")
                
                @pc.on('icecandidate')
                def on_ice_candidate(candidate):
                    if candidate:
                        self.socket_thread.sio.emit('ice_candidate', {
                            'room': self.room_input.text(),
                            'candidate': candidate.to_dict()
                        })

                @pc.on('track')
                def on_track(track):
                    print(f"收到媒体轨道: {track.kind}")
                    if track.kind == "video":
                        self.remote_video = track
                        self.start_remote_video_signal.emit()
                    elif track.kind == "audio":
                        self.remote_audio = track
                        self.start_remote_audio_signal.emit()
                
                # 立即添加媒体轨道
                pc.addTrack(self.video_track)
                pc.addTrack(self.audio_track)

                print("新连接创建成功")
                return True
                
            except Exception as e:
                print(f"创建连接失败: {e}")
                return False
                
        return asyncio.run_coroutine_threadsafe(setup_pc(), self.loop)

    async def create_offer(self):
        try:
            if not self.webrtc.pc:
                print("等待 PeerConnection 创建完成...")
                return
                
            await self.setup_media_tracks()
            offer = await self.webrtc.create_and_send_offer()
            self.socket_thread.sio.emit('offer', {
                'room': self.room_input.text(),
                'sdp': offer.sdp
            })
        except Exception as e:
            print(f"Create offer failed: {e}")

    async def _handle_offer(self, data):
        print("收到offer,开始处理...")
        try:
            # 1. 创建新的 PeerConnection
            await self.create_new_peer_connection()
            
            # 2. 设置媒体轨道
            await self.setup_media_tracks()
            
            # 3. 设置远程描述并创建应答
            await self.webrtc.handle_remote_description(data['sdp'], 'offer')
            answer = await self.webrtc.create_and_send_answer()
            
            # 4. 发送应答
            self.socket_thread.sio.emit('answer', {
                'room': self.room_input.text(),
                'sdp': answer.sdp
            })
            
        except Exception as e:
            print(f"处理offer失败: {e}")
            raise e

    def on_answer(self, data):
        try:
            asyncio.run_coroutine_threadsafe(
                self.webrtc.handle_remote_description(data['sdp'], 'answer'),
                self.loop
            )
            print("Answer processed successfully")
        except Exception as e:
            print(f"处理 answer 失败: {e}")

    #点击开启视频绑定的事件
    def toggle_video(self):
        try:
            if not self.is_video_enabled:
                # 切换到摄像头视频流
                new_track = self.media_manager.get_video_track(True)
            else:
                # 切换到黑屏流
                new_track = self.media_manager.get_video_track(False)
                
            self.video_track = new_track  # 更新当前轨道引用
            self.is_video_enabled = not self.is_video_enabled
            self.video_button.setText('关闭视频' if self.is_video_enabled else '开启视频')
            
            # 更新PC的视频轨道
            if self.webrtc.pc:
                senders = self.webrtc.pc.getSenders()
                video_sender = next((s for s in senders if s.track and s.track.kind == "video"), None)
                if video_sender:
                    asyncio.run_coroutine_threadsafe(
                        video_sender.replaceTrack(new_track),
                        self.loop
                    )
            
            # 更新本地预览
            if self.video_thread:
                self.video_thread.stop()
                self.video_thread.wait()
            self.video_thread = VideoUpdateThread(new_track)
            self.video_thread.frame_ready.connect(self.update_video_frame)
            self.video_thread.start()
            
            print(f"视频已{'开启' if self.is_video_enabled else '关闭'}")
            
        except Exception as e:
            print(f"视频切换失败: {e}")

    def toggle_audio(self):
        try:
            if not self.is_audio_enabled:
                new_track = self.media_manager.get_audio_track(True)
            else:
                new_track = self.media_manager.get_audio_track(False)
                
            self.audio_track = new_track  # 更新当前轨道引用
            self.is_audio_enabled = not self.is_audio_enabled
            self.audio_button.setText('关闭音频' if self.is_audio_enabled else '开启音频')
            
            # 更新PC的音频轨道
            if self.webrtc.pc:
                senders = self.webrtc.pc.getSenders()
                audio_sender = next((s for s in senders if s.track and s.track.kind == "audio"), None)
                if audio_sender:
                    asyncio.run_coroutine_threadsafe(
                        audio_sender.replaceTrack(new_track),
                        self.loop
                    )
            
            print(f"音频已{'开启' if self.is_audio_enabled else '关闭'}")
            
        except Exception as e:
            print(f"音频切换失败: {e}")

    async def add_video_track(self):
        if self.video_track and self.pc:
            print("添加视频轨道")
            self.pc.addTrack(self.video_track)

    async def add_audio_track(self):
        if self.audio_track and self.pc:
            self.pc.addTrack(self.audio_track)

    def start_local_video(self):
        try:
            class AsyncHelper(QThread):
                def __init__(self, coro):
                    super().__init__()
                    self.coro = coro
                
                def run(self):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.coro)
                    loop.close()

            async def setup_video():
                if not self.video_track:
                    self.video_track = VideoStreamTrack()
                if self.pc:
                    await self.add_tracks()
                
            helper = AsyncHelper(setup_video())
            helper.start()
            helper.wait()
            
            self.start_video_stream()
        except Exception as e:
            print(f"Error starting local video: {e}")
            raise e
    def start_remote_video(self):
        if self.remote_video and not self.remote_video_thread:
            self.remote_video_thread = VideoUpdateThread(self.remote_video)
            self.remote_video_thread.frame_ready.connect(
                self.update_remote_frame,
                type=Qt.QueuedConnection
            )
            self.remote_video_thread.start()
            print("远程视频流已启动")

    def start_remote_audio(self):
        if self.remote_audio:
            try:
                # 创建新的音频播放实例
                self.remote_audio_player = QMediaPlayer()
                self.remote_audio_player.setVolume(100)
                self.remote_audio_player.play()
                print("远程音频流已启动")
            except Exception as e:
                print(f"启动远程音频失败: {e}")

    def start_video_stream(self):
        if not self.video_thread and self.video_track:
            self.video_thread = VideoUpdateThread(self.video_track)
            self.video_thread.frame_ready.connect(self.update_video_frame)
            self.video_thread.start()

    def stop_video_stream(self):
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread.wait()
            self.video_thread = None
            self.local_video_widget.image_label.clear()

    def send_message(self):
        message = self.message_input.text()
        room = self.room_input.text()
        self.socket_thread.send_message({'room': room, 'message': message})
        self.display_message(f'你: {message}')
        self.message_input.clear()

    def display_message(self, message):
        self.message_display.append(message)

    def on_message(self, data):
        self.display_message(f"对方: {data['message']}")

    def on_ready(self):
        print("Room is ready for WebRTC connection")
        # 先确保创建 PeerConnection，再创建 offer
        self.create_new_peer_connection().add_done_callback(
            lambda _: asyncio.run_coroutine_threadsafe(self.create_offer(), self.loop)
        )


    async def create_offer(self):
        try:
            if not self.webrtc.pc:
                print("等待 PeerConnection 创建完成...")
                return
                
            await self.setup_media_tracks()
            offer = await self.webrtc.create_and_send_offer()
            self.socket_thread.sio.emit('offer', {
                'room': self.room_input.text(),
                'sdp': offer.sdp
            })
        except Exception as e:
            print(f"Create offer failed: {e}")
            
    def handle_offer(self, data):
        try:
            # 创建任务并等待结果
            future = asyncio.run_coroutine_threadsafe(self._handle_offer(data), self.loop)
            future.result(timeout=10)  # 设置合理的超时时间
        except Exception as e:
            print(f"处理 offer 错误: {e}")
    
    async def _handle_offer(self, data):
        print("收到offer,开始处理...")
        try:
            # 1. 保存当前媒体状态
            had_video = self.video_track is not None
            had_audio = self.audio_track is not None
            
            # 2. 等待旧连接关闭
            if self.pc:
                await self.pc.close()
                self.pc = None
                await asyncio.sleep(0.5)
    
            # 3. 创建新连接
            ice_configuration = RTCConfiguration([
                RTCIceServer(urls=['stun:49.235.44.81:3478'])
            ])
            self.pc = RTCPeerConnection(configuration=ice_configuration)
            
            # 4. 设置事件处理器
            @self.pc.on('connectionstatechange')
            def on_connectionstatechange():
                print(f"连接状态变更: {self.pc.connectionState}")
                
            @self.pc.on('signalingstatechange')    
            def on_signalingstatechange():
                print(f"信令状态变更: {self.pc.signalingState}")
            
            # 5. 等待连接就绪
            await asyncio.sleep(0.5)
            
            # 6. 恢复媒体轨道
            if had_video:
                await self.add_video_track()
            if had_audio:
                await self.add_audio_track()
                
            # 7. 设置远程描述
            await self.pc.setRemoteDescription(
                RTCSessionDescription(sdp=data['sdp'], type='offer')
            )
            
            # 8. 创建应答
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            
            # 9. 发送应答
            self.socket_thread.sio.emit('answer', {
                'room': self.room_input.text(),
                'sdp': self.pc.localDescription.sdp
            })
            
        except Exception as e:
            print(f"处理offer失败: {e}")
            print(f"当前信令状态: {self.pc.signalingState if self.pc else 'None'}")
            raise e
            
    async def setup_media_tracks(self):
        """初始化媒体轨道"""
        try:
            if not self.webrtc.pc:
                print("PeerConnection not ready")
                return
                
            # 添加当前状态的轨道
            self.webrtc.pc.addTrack(self.video_track)
            self.webrtc.pc.addTrack(self.audio_track)
            
            # 启动本地预览
            if not self.video_thread:
                self.video_thread = VideoUpdateThread(self.video_track)
                self.video_thread.frame_ready.connect(self.update_video_frame)
                self.video_thread.start()
                
        except Exception as e:
            print(f"Setup media tracks failed: {e}")

    def on_answer(self, data):
        try:
            # 在主事件循环中处理 answer
            asyncio.run_coroutine_threadsafe(
                self.pc.setRemoteDescription(
                    RTCSessionDescription(sdp=data['sdp'], type='answer')
                ),
                self.loop
            )
            print("Answer processed successfully")
        except Exception as e:
            print(f"处理 answer 失败: {e}")

    def on_ice_candidate(self, data):
        try:
            candidate = RTCIceCandidate(
                sdpMid=data['candidate']['sdpMid'],
                sdpMLineIndex=data['candidate']['sdpMLineIndex'],
                candidate=data['candidate']['candidate']
            )
            # 在主事件循环中添加 ICE candidate
            asyncio.run_coroutine_threadsafe(
                self.pc.addIceCandidate(candidate),
                self.loop
            )
        except Exception as e:
            print(f"处理 ICE candidate 失败: {e}")

    def handle_ice_candidate(self, candidate_dict):
        self.socket_thread.sio.emit('ice_candidate', {
            'room': self.room_input.text(),
            'candidate': candidate_dict
        })

    def update_video_frame(self, frame):
        try:
            self.local_video_widget.update_frame(frame)
        except Exception as e:
            print(f"更新本地视频帧失败: {e}")

    def update_remote_frame(self, frame):
        try:
            self.remote_video_widget.update_frame(frame)
        except Exception as e:
            print(f"更新远程视频帧失败: {e}")

    def closeEvent(self, event):
        self.media_manager.stop_all()
        if self.video_track:
            self.video_track.stop()
        if self.video_thread:
            self.stop_video_stream()
        if self.remote_video_thread:
            self.remote_video_thread.stop()
            self.remote_video_thread.wait()
        if self.pc:
            self.loop.run_until_complete(self.pc.close())
        if self.remote_audio_player:
            self.remote_audio_player.stop()
        self.loop.close()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    if sys.platform.startswith('linux'):
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
        os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'
    
    try:
        client = WebRTCClient()
        client.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)