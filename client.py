import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLineEdit, QTextEdit,
                            QLabel)
from PyQt5.QtCore import (QThread, pyqtSignal, Qt, QTimer, QMetaObject, Q_ARG,
                         QUrl)  # 添加 QUrl 导入
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
import asyncio
import fractions
import time
from av import VideoFrame
import traceback  # 添加 traceback 导入

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

    def _on_ready(self, data=None):  # 修改这里，添加可选的data参数
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
        self.image_label.setMinimumSize(320, 240)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: black; }")
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.last_update = time.time()
        self.update_interval = 1.0 / 30  # 30 FPS

    def update_frame(self, frame):
        try:
            current_time = time.time()
            if current_time - self.last_update < self.update_interval:
                return
                
            if frame is None or frame.size == 0:
                return
                
            height, width = frame.shape[:2]
            target_width = min(640, self.image_label.width())
            target_height = int(target_width * height / width)
            
            # 缩放帧以提高性能
            frame = cv2.resize(frame, (target_width, target_height))
            
            # BGR to RGB conversion if needed
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            bytes_per_line = 3 * target_width
            q_img = QImage(frame.data, target_width, target_height, 
                         bytes_per_line, QImage.Format_RGB888)
            
            # 使用缩放后的尺寸创建 pixmap
            pixmap = QPixmap.fromImage(q_img)
            self.image_label.setPixmap(pixmap)
            self.last_update = current_time
            
        except Exception as e:
            print(f"更新视频帧失败: {e}")

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

class SwitchableVideoTrack(MediaStreamTrack):
    kind = "video"
    
    def __init__(self):
        super().__init__()
        self.enabled = False
        self.cap = None
        self.black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self._init_camera()
        
    def _init_camera(self):
        """初始化摄像头，包含重试逻辑"""
        try:
            # 尝试不同的摄像��索引
            for index in range(2):  # 尝试前两个摄像头设备
                self.cap = cv2.VideoCapture(index)
                if self.cap and self.cap.isOpened():
                    print(f"成功打开摄像头 {index}")
                    # 设置摄像头分辨率
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    return
                else:
                    print(f"无法打开摄像头 {index}")
                    
            # 如果都失败了，检查设备权限
            if os.path.exists('/dev/video0'):
                print("摄像头设备存在但无法访问，可能是权限问题")
            else:
                print("未找到摄像头设备")
                
        except Exception as e:
            print(f"初始化摄像头时出错: {e}")
            self.cap = None
        
    async def recv(self):
        try:
            if self.enabled and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # BGR to RGB conversion
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    frame = self.black_frame
                    print("读取摄像头帧失败")
            else:
                frame = self.black_frame
                
            # 创建VideoFrame
            video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            video_frame.pts = int(time.time() * 1000)
            video_frame.time_base = fractions.Fraction(1, 1000)
            return video_frame
            
        except Exception as e:
            print(f"处理视频帧时出错: {e}")
            return VideoFrame.from_ndarray(self.black_frame, format="rgb24")
        
    def switch(self, enabled):
        """切换视频状态"""
        self.enabled = enabled
        if enabled and (self.cap is None or not self.cap.isOpened()):
            self._init_camera()  # 尝试重新初始化摄像头
        
    def stop(self):
        """停止视频轨道"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        super().stop()

class SwitchableAudioTrack(AudioStreamTrack):
    def __init__(self):
        super().__init__()
        self.enabled = False
        
    async def recv(self):
        # 使用父类的 recv，但根据 enabled 状态返回静音或原始音频
        frame = await super().recv()
        if not self.enabled:
            # 将音频数据设置为0（静音）
            frame.planes[0].update(bytes(len(frame.planes[0])))
        return frame
        
    def switch(self, enabled):
        self.enabled = enabled

class VideoUpdateThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, video_track):
        super().__init__()
        self.video_track = video_track
        self.running = True
        self.frame_count = 0
        self.frame_buffer = []  # 添加帧缓冲
        self.buffer_size = 5    # 限制缓冲大小
        print(f"VideoUpdateThread initialized for track: {video_track.kind}")

    async def receive_frames(self):
        while self.running:
            try:
                frame = await self.video_track.recv()
                if frame and self.running:
                    # 限制缓冲大小
                    if len(self.frame_buffer) >= self.buffer_size:
                        self.frame_buffer.pop(0)
                    
                    img = frame.to_ndarray(format="bgr24")
                    if img is not None and img.size > 0:
                        self.frame_buffer.append(img)
                        self.frame_ready.emit(img)
                        
                await asyncio.sleep(1/30)  # 30fps
                
            except MediaStreamError as e:
                print(f"Media stream error: {e}")
                break
            except Exception as e:
                print(f"Frame receiving error: {e}")
                traceback.print_exc()
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
        self.frame_buffer.clear()  # 清空缓冲
        self.wait(1000)  # 添加超时等待
        
    def __del__(self):
        """确保线程正确清理"""
        self.stop()
        try:
            if self.isRunning():
                self.terminate()
                self.wait(1000)
        except:
            pass

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
        self.video_thread = None
        self._init_tracks()
        
    def _init_tracks(self):
        """初始化媒体轨道"""
        try:
            self.video_track = SwitchableVideoTrack()
            self.audio_track = SwitchableAudioTrack()
        except Exception as e:
            print(f"初始化媒体轨道失败: {e}")
            # 使用虚拟轨道作为后备
            self.video_track = DummyVideoTrack()
            self.audio_track = SwitchableAudioTrack()
        
    def get_video_track(self, enabled=False):
        """获取视频轨道并设置其状态"""
        self.video_track.switch(enabled)
        return self.video_track
        
    def get_audio_track(self, enabled=False):
        """获取音频轨道并设置其状态"""
        self.audio_track.switch(enabled)
        return self.audio_track

    def start_local_preview(self, frame_callback):
        """启动本地视频预览"""
        if not self.video_thread:
            self.video_thread = VideoUpdateThread(self.video_track)
            self.video_thread.frame_ready.connect(frame_callback, Qt.QueuedConnection)
            self.video_thread.start()

    def stop_local_preview(self):
        """停止本地视频预览"""
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread.wait()
            self.video_thread = None

    def stop_all(self):
        """改进资源清理"""
        try:
            if self.video_thread:
                self.video_thread.stop()
                self.video_thread.wait(1000)
                self.video_thread = None
                
            if self.video_track:
                self.video_track.stop()
                self.video_track = None
                
            if self.audio_track:
                self.audio_track.stop()
                self.audio_track = None
        except Exception as e:
            print(f"停止媒体轨道时发生错误: {e}")

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
        self.audio_recorder = None
        
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
        self.start_local_preview()
        self.setup_video_connections()

        self.frame_count = 0
        self.last_time = time.time()
        self.fps = 0
        
        # 启动性能监控
        self._setup_performance_monitor()

        # 添加资源监控
        self.resource_monitor = QTimer()
        self.resource_monitor.timeout.connect(self.check_resources)
        self.resource_monitor.start(5000)  # 每5秒检查一次
        
        # 添加心跳检测
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        self.heartbeat_timer.start(10000)  # 每10秒发送一次心跳

    def _setup_performance_monitor(self):
        """设置性能监控"""
        self.fps_timer = QTimer(self)
        self.fps_timer.timeout.connect(self._update_fps)
        self.fps_timer.start(1000)  # 每秒更新一次

    def _update_fps(self):
        """更新FPS计数"""
        current_time = time.time()
        elapsed = current_time - self.last_time
        if elapsed > 0:
            self.fps = self.frame_count / elapsed
            print(f"FPS: {self.fps:.2f}")
            self.frame_count = 0
            self.last_time = current_time

    def setup_default_tracks(self):
        """初始化默认的媒体轨道（黑屏和静音）"""
        self.video_track = self.media_manager.get_video_track(False)
        self.audio_track = self.media_manager.get_audio_track(False)

    def start_local_preview(self):
        """启动本地视频预览"""
        self.media_manager.start_local_preview(self.update_video_frame)

    def start_remote_video(self):
        """启动远程视频流"""
        print("启动远程视频流方法被调用")
        if not self.remote_video:
            print("无远程视频轨道")
            return
            
        if self.remote_video_thread and self.remote_video_thread.isRunning():
            print("远程视频线程已在运行")
            return
            
        try:
            print("开始初始化远程视频流")
            self.remote_video_thread = VideoUpdateThread(self.remote_video)
            
            def on_frame_ready(frame):
                try:
                    if frame is not None and frame.size > 0:
                        self.remote_video_widget.update_frame(frame)
                except Exception as e:
                    print(f"处理远程视频帧失败: {e}")
            
            self.remote_video_thread.frame_ready.connect(
                on_frame_ready,
                type=Qt.QueuedConnection
            )
            self.remote_video_thread.start()
            print("远程视频线程已启动")
        except Exception as e:
            print(f"启动远程视频流失败: {e}")
            if self.remote_video_thread:
                self.remote_video_thread.stop()
                self.remote_video_thread = None

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
        
        # 设置固定大小和对齐方式
        for widget in [self.local_video_widget, self.remote_video_widget]:
            widget.setMinimumSize(320, 240)
            widget.setMaximumSize(640, 480)
            
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
        
        # 房间控件
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
        self.remote_audio_player = QMediaPlayer()  # 确保初始化
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
                    print(f"收到新的媒体轨道: {track.kind}")
                    if track.kind == "video":
                        print("设置远程视频轨道")
                        self.remote_video = track
                        print("触发远程视频信号")
                        self.start_remote_video_signal.emit()  # 确保这个信号被正确连接
                    elif track.kind == "audio":
                        print("设置远程音频轨道")
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
        """统一的answer处理方法"""
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
        """切换视频状态"""
        try:
            self.is_video_enabled = not self.is_video_enabled
            self.video_track.switch(self.is_video_enabled)
            self.video_button.setText('关闭视频' if self.is_video_enabled else '开启视频')
            print(f"视频已{'开启' if self.is_video_enabled else '关闭'}")
        except Exception as e:
            print(f"视频切换失败: {e}")
            traceback.print_exc()

    def toggle_audio(self):
        """切换音频状态"""
        try:
            self.is_audio_enabled = not self.is_audio_enabled
            self.audio_track.switch(self.is_audio_enabled)
            self.audio_button.setText('关闭音频' if self.is_audio_enabled else '开启音频')
            print(f"音频已{'开启' if self.is_audio_enabled else '关闭'}")
        except Exception as e:
            print(f"音频切换失败: {e}")
            traceback.print_exc()

    async def add_video_track(self):
        if self.video_track and self.pc:
            print("添加视频轨道")
            self.pc.addTrack(self.video_track)

    async def add_audio_track(self):
        if self.audio_track and self.pc:
            self.pc.addTrack(self.audio_track)

    def start_remote_audio(self):
        """占位用的远程音频处理函数"""
        if self.remote_audio:
            print("收到远程音频轨道")

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
        """优化媒体轨道设置"""
        try:
            if not self.webrtc.pc:
                print("PeerConnection not ready")
                return
                
            # 使用弱引用避免循环引用
            import weakref
            video_track_ref = weakref.ref(self.video_track)
            audio_track_ref = weakref.ref(self.audio_track)
            
            if video_track_ref():
                self.webrtc.pc.addTrack(video_track_ref())
            if audio_track_ref():
                self.webrtc.pc.addTrack(audio_track_ref())
            
            # 限制视频分辨率和帧率
            if not self.video_thread and video_track_ref():
                self.video_thread = VideoUpdateThread(video_track_ref())
                self.video_thread.frame_ready.connect(
                    self.update_video_frame,
                    type=Qt.QueuedConnection
                )
                self.video_thread.start()
                
        except Exception as e:
            print(f"Setup media tracks failed: {e}")
            self.clean_up_resources()

    def on_answer(self, data):
        """统一的answer处理方法"""
        try:
            asyncio.run_coroutine_threadsafe(
                self.webrtc.handle_remote_description(data['sdp'], 'answer'),
                self.loop
            )
            print("Answer processed successfully")
        except Exception as e:
            print(f"处理 answer 失败: {e}")

    def on_ice_candidate(self, data):
        """统一的ICE candidate处理方法"""
        try:
            candidate = RTCIceCandidate(
                sdpMid=data['candidate']['sdpMid'],
                sdpMLineIndex=data['candidate']['sdpMLineIndex'],
                candidate=data['candidate']['candidate']
            )
            asyncio.run_coroutine_threadsafe(
                self.webrtc.pc.addIceCandidate(candidate),
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
        """优化视频帧更新"""
        try:
            if frame is not None and not frame.size == 0:
                # 限制帧大小
                max_size = (640, 480)
                if frame.shape[0] > max_size[1] or frame.shape[1] > max_size[0]:
                    frame = cv2.resize(frame, max_size)
                    
                self.local_video_widget.update_frame(frame)
                self.frame_count += 1
                
                # 定期清理
                if self.frame_count > 1000:
                    self.clean_up_resources()
                    
        except Exception as e:
            print(f"更新本地视频帧失败: {e}")
            self.clean_up_resources()

    def update_remote_frame(self, frame):
        print(222)
        """更新远程视频帧"""
        try:
            if frame is not None and frame.size > 0:
                # 添加帧大小日志
                if hasattr(self, 'remote_frame_count'):
                    self.remote_frame_count += 1
                    if self.remote_frame_count % 30 == 0:
                        print(f"Remote frame {self.remote_frame_count}, shape: {frame.shape}")
                else:
                    self.remote_frame_count = 1
                
                self.remote_video_widget.update_frame(frame)
            else:
                print("收到空的远程视频帧")
        except Exception as e:
            print(f"更新远程视频帧失败: {e}")
            traceback.print_exc()

    def closeEvent(self, event):
        """优化关闭流程"""
        try:
            # 停止视频线程
            if self.remote_video_thread:
                self.remote_video_thread.stop()
                self.remote_video_thread.wait()
                self.remote_video_thread = None
                
            if self.video_thread:
                self.video_thread.stop()
                self.video_thread.wait()
                self.video_thread = None
                
            # 停止所有定时器
            for timer in [self.resource_monitor, self.heartbeat_timer, self.fps_timer]:
                if timer.isActive():
                    timer.stop()
            
            # 其他清理代码保持不变
            # ...existing code...
            
        except Exception as e:
            print(f"关闭时发生错误: {e}")
        finally:
            self.clean_up_resources()
            event.accept()
            QApplication.quit()

    def __del__(self):
        """析构函数确保资源释放"""
        try:
            if hasattr(self, 'loop') and not self.loop.is_closed():
                self.loop.stop()
            if hasattr(self, 'media_manager'):
                self.media_manager.stop_all()
        except:
            pass

    def setup_video_connections(self):
        """设置视频相关的信号连接"""
        # 确保在主线程中更新UI
        self.start_remote_video_signal.connect(self.start_remote_video, Qt.QueuedConnection)
        self.start_remote_audio_signal.connect(self.start_remote_audio, Qt.QueuedConnection)

    def check_resources(self):
        """检查系统资源使用情况"""
        import psutil
        process = psutil.Process()
        memory_percent = process.memory_percent()
        cpu_percent = process.cpu_percent()
        
        if memory_percent > 80 or cpu_percent > 80:
            print(f"Warning: High resource usage - Memory: {memory_percent}%, CPU: {cpu_percent}%")
            self.clean_up_resources()

    def clean_up_resources(self):
        """清理资源"""
        # 停止并清理视频线程
        if hasattr(self, 'remote_video_thread') and self.remote_video_thread:
            self.remote_video_thread.stop()
            self.remote_video_thread.wait()
            self.remote_video_thread = None
            
        import gc
        gc.collect()  
        
        # 重置视频帧缓存
        if hasattr(self, 'frame_count'):
            self.frame_count = 0
            
        # 清理远程视频帧缓存
        if hasattr(self, 'remote_frame_count'):
            self.remote_frame_count = 0

    def send_heartbeat(self):
        """发送心跳包到服务器"""
        if self.server_connected and self.is_room_joined:
            self.socket_thread.sio.emit('heartbeat', {'room': self.room_input.text()})

    def send_message(self):
        """发送聊天消息"""
        try:
            message = self.message_input.text()
            if not message:
                return
                
            room = self.room_input.text()
            if not room:
                print("未加入房间")
                return
                
            self.socket_thread.send_message({'room': room, 'message': message})
            self.display_message(f'你: {message}')
            self.message_input.clear()
        except Exception as e:
            print(f"发送消息失败: {e}")

    def display_message(self, message):
        """显示消息到消息框"""
        try:
            self.message_display.append(message)
        except Exception as e:
            print(f"显示消息失败: {e}")

    def on_message(self, data):
        """处理接收到的消息"""
        try:
            self.display_message(f"对方: {data['message']}")
        except Exception as e:
            print(f"处理消息失败: {e}")

    def on_ready(self):
        """处理房间就绪信号"""
        print("Room is ready for WebRTC connection")
        try:
            # 创建 offer
            future = asyncio.run_coroutine_threadsafe(self.create_offer(), self.loop)
            future.result(timeout=10)  # 设置合理的超时时间
        except Exception as e:
            print(f"处理房间就绪信号失败: {e}")
            traceback.print_exc()

    def handle_offer(self, data):
        """处理收到的offer"""
        try:
            future = asyncio.run_coroutine_threadsafe(self._handle_offer(data), self.loop)
            future.result(timeout=10)
        except Exception as e:
            print(f"处理 offer 失败: {e}")
            traceback.print_exc()

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