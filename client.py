from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLineEdit, QTextEdit,
                            QLabel)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QMetaObject, Q_ARG
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from aiortc import (RTCPeerConnection, RTCSessionDescription, 
                   MediaStreamTrack, VideoStreamTrack, RTCIceCandidate,
                   RTCConfiguration, RTCIceServer)  
from aiortc.contrib.media import MediaPlayer, MediaRecorder
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.contrib.media import MediaRelay
import socketio
import asyncio
import sys
import os
import av
import cv2
import numpy as np
from aiortc.mediastreams import MediaStreamTrack
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
        
    def setup_events(self):
        self.sio.on('message', self._on_message)
        self.sio.on('ready', self._on_ready)
        self.sio.on('offer', self._on_offer)
        self.sio.on('answer', self._on_answer)
        self.sio.on('ice_candidate', self._on_ice_candidate)

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def update_frame(self, frame):
        height, width = frame.shape[:2]
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaled(320, 240, Qt.KeepAspectRatio))

class CameraStreamTrack(MediaStreamTrack):
    kind = "video"
    
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("无法打开摄像头")
        
        # 设置摄像头参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.running = True

    async def recv(self):
        if not self.running:
            raise MediaStreamError("Track has ended")
            
        ret, frame = self.cap.read()
        if not ret:
            raise MediaStreamError("Failed to get frame from camera")

        # 将OpenCV的BGR格式转换为RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 创建VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = int(time.time() * 1000) 
        video_frame.time_base = fractions.Fraction(1, 1000) 
        
        return video_frame

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

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

class WebRTCClient(QMainWindow):
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
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # 添加状态标志
        self.is_room_joined = False
        self.is_video_enabled = False
        self.is_audio_enabled = False
        self.server_connected = False  
        self.setup_ui()
        self.setup_socket_signals()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 视频区域
        video_layout = QHBoxLayout()
        self.local_video_widget = VideoWidget()
        self.remote_video_widget = VideoWidget()
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
        self.video_button.setEnabled(False)  # 初始禁用媒体按钮
        self.audio_button.setEnabled(False)
        self.video_button.setText('开启视频')
        self.audio_button.setText('开启音频')

    def setup_socket_signals(self):
        self.socket_thread.message_received.connect(self.on_message)
        self.socket_thread.ready_signal.connect(self.on_ready)
        self.socket_thread.offer_received.connect(self.on_offer)
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
                    self.socket_thread.connect_to_server('http://49.235.44.81:5000')
                    self.server_connected = True
                
                self.socket_thread.join_room(room)
                self.init_webrtc()  # 改名以避免混淆
                
                self.is_room_joined = True
                self.join_button.setText('已加入房间')
                self.join_button.setEnabled(False)
                self.room_input.setEnabled(False)
                
                # 启用媒体控制按钮
                self.video_button.setEnabled(True)
                self.audio_button.setEnabled(True)
                
            except Exception as e:
                print(f"加入房间失败: {e}")

    def init_webrtc(self):
        try:
            ice_servers = [RTCIceServer(urls=['stun:stun.l.google.com:19302'])]
            config = RTCConfiguration(iceServers=ice_servers)
            self.pc = RTCPeerConnection(configuration=config)
            
            @self.pc.on('icecandidate')
            def on_ice_candidate(candidate):
                if candidate:
                    self.socket_thread.sio.emit('ice_candidate', {
                        'room': self.room_input.text(),
                        'candidate': candidate.to_dict()
                    })

            @self.pc.on('track')
            def on_track(track):
                print(f"收到媒体轨道: {track.kind}")
                if track.kind == "video":
                    self.remote_video = track
                    self.start_remote_video()
                elif track.kind == "audio":
                    self.remote_audio = track

        except Exception as e:
            print(f"WebRTC初始化失败: {e}")
            raise e
        
    def toggle_video(self):
        try:
            if not self.is_video_enabled:
                if not self.video_track:
                    self.video_track = CameraStreamTrack()
                    if self.pc:
                        self.loop.run_until_complete(self.add_video_track())
                self.start_video_stream()
                self.is_video_enabled = True
                self.video_button.setText('关闭视频')
                print("视频已开启")
            else:
                self.stop_video_stream()
                if self.video_track:
                    self.video_track.stop()
                    self.video_track = None
                self.is_video_enabled = False
                self.video_button.setText('开启视频')
                print("视频已关闭")
        except Exception as e:
            print(f"视频切换失败: {e}")

    def toggle_audio(self):
        try:
            if not self.is_audio_enabled:
                if not self.audio_track:
                    self.audio_track = AudioStreamTrack()
                    if self.pc:
                        self.loop.run_until_complete(self.add_audio_track())
                self.is_audio_enabled = True
                self.audio_button.setText('关闭音频')
            else:
                if self.audio_track:
                    self.audio_track.enabled = False
                self.is_audio_enabled = False
                self.audio_button.setText('开启音频')
        except Exception as e:
            print(f"音频切换失败: {e}")

    async def add_video_track(self):
        if self.video_track and self.pc:
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
            self.remote_video_thread.frame_ready.connect(self.update_remote_frame)
            self.remote_video_thread.start()

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

    async def on_offer(self, data):
        await self.setup_media_tracks()
        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=data['sdp'], type='offer')
        )
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        self.socket_thread.sio.emit('answer', {
            'room': self.room_input.text(),
            'sdp': self.pc.localDescription.sdp
        })

    async def setup_media_tracks(self):
        self.video_track = VideoStreamTrack()
        self.pc.addTrack(self.video_track)
        
        self.audio_track = AudioStreamTrack()
        self.pc.addTrack(self.audio_track)

    async def on_track(self, track):
        if track.kind == "video":
            self.remote_video = track
        elif track.kind == "audio":
            self.remote_audio = track

    async def create_offer(self):
        await self.setup_media_tracks()
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        self.socket_thread.sio.emit('offer', {
            'room': self.room_input.text(),
            'sdp': self.pc.localDescription.sdp
        })

    def on_answer(self, data):
        print("Received answer")

    def on_ice_candidate(self, data):
        print("Received ICE candidate")

    def handle_ice_candidate(self, candidate_dict):
        self.socket_thread.sio.emit('ice_candidate', {
            'room': self.room_input.text(),
            'candidate': candidate_dict
        })

    def update_video_frame(self, frame):
        self.local_video_widget.update_frame(frame)

    def update_remote_frame(self, frame):
        self.remote_video_widget.update_frame(frame)

    def closeEvent(self, event):
        if self.video_track:
            self.video_track.stop()
        if self.video_thread:
            self.stop_video_stream()
        if self.remote_video_thread:
            self.remote_video_thread.stop()
            self.remote_video_thread.wait()
        if self.pc:
            self.loop.run_until_complete(self.pc.close())
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