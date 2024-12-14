import gc
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
from av import AudioFrame
import traceback 
import sounddevice as sd 
class EventLoopManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._loop = None
        self._thread = None

    def init(self):
        if not self._loop:
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def get_loop(self):
        return self._loop

    def stop(self):
        """改进的事件循环停止方法"""
        if self._loop and self._loop.is_running():
            try:
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                
                # 确保所有任务都被取消
                self._loop.call_soon_threadsafe(lambda: [
                    task.cancel() for task in asyncio.all_tasks(self._loop)
                ])
                
                # 停止事件循环
                self._loop.call_soon_threadsafe(self._loop.stop)
                
                if threading.current_thread() != self._thread:
                    self._thread.join(timeout=1)
            except Exception as e:
                print(f"停止事件循环时出错: {e}")

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
        self._current_frame = None
        self._frame_lock = threading.Lock()
        self.last_frame_time = time.time()
        self.frame_queue = asyncio.Queue(maxsize=2)  # 添加帧缓冲队列，限制大小为2
        self._frame_lock = threading.Lock()
        self._current_frame = None
        self._last_frame_time = time.time()
        self._frame_queue = asyncio.Queue(maxsize=1)  # 限制队列大小为1
        self._processing = False
        self._frame_processed = threading.Event()  # 添加帧处理状态标志
        self._closing = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(int(1000 / 60))  
        
    def closeEvent(self, event):
        self._closing = True
        self._frame_processed.set()  # 解除帧处理等待
        super().closeEvent(event)

    async def _process_frame_queue(self):
        while True:
            try:
                if not self._processing:
                    break
                frame = await self._frame_queue.get()
                current_time = time.time()
                
                if current_time - self._last_frame_time >= self.update_interval:
                    with self._frame_lock:
                        self._current_frame = frame
                    self._last_frame_time = current_time
                    
                    # 使用invokeMethod确保在主线程更新UI
                    QMetaObject.invokeMethod(self.image_label, "setPixmap",
                                           Qt.QueuedConnection,
                                           Q_ARG(QPixmap, self._create_pixmap(frame)))
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"帧处理错误: {e}")

    def _create_pixmap(self, frame):
        height, width = frame.shape[:2]
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, 
                        bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_image).scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )

    def update_frame(self, frame):
        if self._closing:
            return
            
        try:
            if frame is None or frame.size == 0:
                return
            frame_copy = frame.copy()
            height, width = frame_copy.shape[:2]
            bytes_per_line = 3 * width
            
            q_image = QImage(frame_copy.data, width, height,
                           bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            
            self._frame_processed.set()
        except Exception as e:
            print(f"帧更新错误: {e}")

    def set_frame(self, frame):
        self._current_frame = frame

    def update_image(self):
        if (self._current_frame is not None):
            height, width = self._current_frame.shape[:2]
            bytes_per_line = 3 * width
            q_image = QImage(self._current_frame.data, width, height, 
                            bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image).scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)

class DummyVideoTrack(MediaStreamTrack):
    kind = "video"
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.last_frame_time = time.time()
        
    async def recv(self):
        if not self.running:
            raise MediaStreamError
            
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        
        # 控制帧率
        if elapsed < self.frame_interval:
            await asyncio.sleep(self.frame_interval - elapsed)
            
        video_frame = VideoFrame.from_ndarray(self.frame, format="rgb24") 
        video_frame.pts = int(time.time() * 1000)
        video_frame.time_base = fractions.Fraction(1, 1000)
        
        self.last_frame_time = time.time()
        return video_frame

class SwitchableVideoTrack(MediaStreamTrack):
    kind = "video"  
    
    def __init__(self):
        super().__init__()
        self.enable_camera = False  # ��保初始状态为False
        self.cap = None
        # 创建一个静态的黑色帧
        self.black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.last_frame_time = time.time()
        self.frame_interval = 1.0 / 60  # 60 FPS限制
        
    async def recv(self):
        try:
            current_time = time.time()
            elapsed = current_time - self.last_frame_time
            
            # 控制帧率
            if elapsed < self.frame_interval:
                await asyncio.sleep(self.frame_interval - elapsed)
            
            # 如果没开启摄像头，直接返回黑屏
            if not self.enable_camera:
                frame = self.black_frame
                if self.cap and self.cap.isOpened():
                    self.cap.release()
                    self.cap = None
            else:
                # 摄像头启用时的逻辑
                if not self.cap or not self.cap.isOpened():
                    if not self._init_camera():
                        frame = self.black_frame
                    else:
                        ret, frame = self.cap.read()
                        if ret:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        else:
                            frame = self.black_frame
                else:
                    ret, frame = self.cap.read()
                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    else:
                        frame = self.black_frame

            # 创建并返回视频帧
            video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            video_frame.pts = int(time.time() * 1000)
            video_frame.time_base = fractions.Fraction(1, 1000)
            
            self.last_frame_time = current_time
            return video_frame
            
        except Exception as e:
            print(f"视频帧处理错误: {e}")
            return VideoFrame.from_ndarray(self.black_frame, format="rgb24")
        
    def switch(self, enable):
        """切换摄像头状态"""
        self.enable_camera = enable
        if not enable and self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def _init_camera(self):
        """初始化摄像头"""
        try:
            if not self.cap:
                self.cap = cv2.VideoCapture(0)  # 打开默认摄像头
                if not self.cap.isOpened():
                    print("无法打开摄像头")
                    return False
                    
                # 设置摄像头分辨率
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                # 读取一帧测试摄像头是否正常工作
                ret, _ = self.cap.read()
                if not ret:
                    print("摄像头读取失败")
                    self.cap.release()
                    self.cap = None
                    return False
                    
                return True
        except Exception as e:
            print(f"初始化摄像头失败: {e}")
            if self.cap:
                self.cap.release()
                self.cap = None
            return False
        
        return False
    
    def stop(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        self.running = False

class SwitchableAudioTrack(AudioStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.enabled = False
        self.audio_stream = None
        self.lock = threading.Lock()
        self.sample_rate = 48000
        self.samples_per_frame = 960
        self.pts = 0
        self.time_base = fractions.Fraction(1, self.sample_rate)

    async def recv(self):
        if not self.enabled:
            # Return silent frame when disabled
            audio_data = np.zeros((self.samples_per_frame,), dtype=np.int16)
        else:
            try:
                if not self.audio_stream:
                    self._init_audio_stream()
                data, _ = self.audio_stream.read(self.samples_per_frame)
                audio_data = data.reshape(-1)
            except Exception as e:
                print(f"读取音频数据失败: {e}")
                audio_data = np.zeros((self.samples_per_frame,), dtype=np.int16)

        frame = AudioFrame.from_ndarray(audio_data, format='s16', layout='mono')
        frame.pts = self.pts
        frame.time_base = self.time_base
        self.pts += self.samples_per_frame
        return frame

    def switch(self, enabled):
        with self.lock:
            self.enabled = enabled
            if not enabled:
                self._cleanup_audio_stream()

    def _init_audio_stream(self):
        try:
            self.audio_stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                dtype='int16',
                blocksize=self.samples_per_frame)
            self.audio_stream.start()
        except Exception as e:
            print(f"初始化音频输入流失败: {e}")
            self.audio_stream = None

    def _cleanup_audio_stream(self):
        if self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception as e:
                print(f"关闭音频输入流失败: {e}")
            self.audio_stream = None

    def stop(self):
        with self.lock:
            self.enabled = False
            self._cleanup_audio_stream()
            super().stop()

class VideoUpdateThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    fps_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, video_track, is_remote=False, parent_loop=None):
        super().__init__()
        self.video_track = video_track
        self.running = True
        self.is_remote = is_remote
        
        # FPS相关
        self.frame_count = 0
        self._fps = 0
        self.frame_interval = 1.0 / 60  # 添加缺失的帧率控制
        self.last_frame_time = time.time()
        self._last_fps_update = time.time()
        
        # 事件循环
        self.loop = parent_loop if parent_loop else EventLoopManager.instance().get_loop()
        
        # 统一帧缓存管理 (移除重复定义)
        self._pool_lock = threading.Lock()  # 修改这里，将_frame_lock改为_pool_lock
        self._frame_pool = []
        self._pool_size = 2
        self._frame_queue = asyncio.Queue(maxsize=1)
        self._stop_event = threading.Event()

    def _get_frame_from_pool(self):
        with self._pool_lock:  # 现在使用正确的锁名称
            if not self._frame_pool:
                return np.zeros((480, 640, 3), dtype=np.uint8)
            return self._frame_pool.pop()

    def _return_frame_to_pool(self, frame):
        with self._pool_lock:  # 现在使用正确的锁名称
            if len(self._frame_pool) < self._pool_size:
                self._frame_pool.append(frame)

    async def receive_frames(self):
        last_gc_time = time.time()
        frame_buffer = None
        
        try:
            while self.running:
                current_time = time.time()
                
                # 周期性触发GC
                if current_time - last_gc_time > 30:  # 每30秒
                    gc.collect()
                    last_gc_time = current_time
                
                if current_time - self.last_frame_time < self.frame_interval:
                    await asyncio.sleep(0.001)
                    continue

                try:
                    frame = await self.video_track.recv()
                    if not frame:
                        continue

                    # 重用帧缓冲
                    if frame_buffer is None:
                        frame_buffer = self._get_frame_from_pool()
                    
                    # 转换帧
                    frame_data = frame.to_ndarray(format="bgr24")
                    np.copyto(frame_buffer, frame_data)
                    
                    self.frame_ready.emit(frame_buffer)
                    self.last_frame_time = current_time
                    
                    # 更新FPS
                    self.frame_count += 1
                    if current_time - self._last_fps_update >= 1.0:
                        self._fps = self.frame_count
                        self.fps_updated.emit(self._fps)
                        self.frame_count = 0
                        self._last_fps_update = current_time
                        
                except MediaStreamError:
                    break
                except Exception as e:
                    print(f"帧处理错误: {e}")
                    await asyncio.sleep(0.1)
                    
        finally:
            if frame_buffer is not None:
                self._return_frame_to_pool(frame_buffer)

    def run(self):
        """QThread的运行方法"""
        try:
            # 使用 run_coroutine_threadsafe 替代直接运行事件循环
            future = asyncio.run_coroutine_threadsafe(
                self.receive_frames(),
                self.loop
            )
            # 等待协程完成
            future.result()
        except Exception as e:
            print(f"视频线程错误: {e}")
            self.error_occurred.emit(str(e))

    def stop(self):
        """改进的线程停止方法"""
        self._stop_event.set()
        self.quit()  # 请求退出事件循环
        self.wait(1000)  # 等待最多1秒
        if self.isRunning():
            self.terminate()  # 强制终止
            self.wait(500)  # 再等待0.5秒确保结束

    async def process_frame(self):
        while not self._stop_event.is_set():
            try:
                # 使用timeout避免永久阻塞
                frame = await asyncio.wait_for(self.video_track.recv(), timeout=1.0)
                if self._frame_queue.full():
                    try:
                        self._frame_queue.get_nowait()  # 丢弃旧帧
                    except asyncio.QueueEmpty:
                        pass
                await self._frame_queue.put(frame)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"帧处理错误: {e}")
                await asyncio.sleep(0.1)

class WebRTCManager:
    def __init__(self, loop):
        self.pc = None
        self.loop = loop
        self.video_track = None
        self.audio_track = None
        self._setup_ice_servers()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 1.0
        self.reconnecting = False
        self._tracks = []  # 保存轨道引用
        
    def _setup_ice_servers(self):
        self.config = RTCConfiguration([
            RTCIceServer(urls=['stun:49.235.44.81:3478'])
        ])
        
    async def create_peer_connection(self):
        """创建新的 PeerConnection 实例"""
        if self.pc:
            await self.close_connection()
            
        ice_servers = [
            RTCIceServer(urls=['stun:49.235.44.81:3478']),
            RTCIceServer(urls=['stun:stun1.l.google.com:19302']),
            RTCIceServer(urls=['stun:stun2.l.google.com:19302'])
        ]
        
        self.config = RTCConfiguration(iceServers=ice_servers)
        self.pc = RTCPeerConnection(configuration=self.config)
        
        # 添加连接监控
        @self.pc.on('connectionstatechange')
        async def on_connectionstatechange():
            print(f"连接状态变更: {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                if not self.reconnecting and self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnecting = True
                    self.reconnect_attempts += 1
                    print(f"连接失败,尝试第{self.reconnect_attempts}次重连...")
                    try:
                        await self.reconnect()
                    finally:
                        self.reconnecting = False
            elif self.pc.connectionState == "connected":
                # 重置重连计数
                self.reconnect_attempts = 0
                
        @self.pc.on('iceconnectionstatechange') 
        async def on_iceconnectionstatechange():
            if self.pc.iceConnectionState == "disconnected":
                print("ICE连接断开,尝试恢复...")
                # 先尝试ICE重启
                try:
                    await self.handle_ice_disconnect()
                except Exception as e:
                    print(f"ICE重连失败: {e}")
                    # ICE重连失败则尝试完全重连
                    if not self.reconnecting:
                        await self.reconnect()
                        
        return self.pc

    async def handle_ice_disconnect(self):
        """改进的ICE重连处理"""
        if not self.pc:
            return
            
        try:
            print("尝试重启ICE...")
            await self.pc.restartIce()
            
            # 等待ICE重连结果
            start_time = time.time()
            while time.time() - start_time < 5:  # 5秒超时
                if self.pc.iceConnectionState in ["connected", "completed"]:
                    print("ICE重连成功")
                    return True
                await asyncio.sleep(0.5)
                
            raise Exception("ICE重连超时")
            
        except Exception as e:
            print(f"ICE重连失败: {e}")
            raise e
            
    async def reconnect(self):
        """改进的重连逻辑"""
        try:
            print(f"开始第{self.reconnect_attempts}次重连...")
            await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
            
            # 创建新连接
            old_pc = self.pc
            self.pc = None  # 清空引用
            pc = await self.create_peer_connection()
            
            # 重新添加之前的轨道
            for track in self._tracks:
                pc.addTrack(track)
                
            # 创建新offer
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)
            
            # 发送重连信号
            if hasattr(self, 'socket_thread'):
                self.socket_thread.sio.emit('reconnect', {
                    'room': self.room_input.text(),
                    'sdp': offer.sdp
                })
                
            # 清理旧连接
            if old_pc:
                await old_pc.close()
                
        except Exception as e:
            print(f"重连失败: {e}")
            self.reconnecting = False
            traceback.print_exc()
        
    async def close_connection(self):
        """关闭当前连接"""
        if self.pc:
            await self.pc.close()
            self.pc = None
            await asyncio.sleep(0.5)
            
    def add_track(self, track):
        """添加媒体轨道"""
        if self.pc and track:
            self._tracks.append(track)  # 保存轨道引用
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

    def create_tracks(self):
        """新增的公共方法来初始化轨道"""
        self._init_tracks()
        
    def _init_tracks(self):
        """初始化媒体轨道"""
        try:
            self.video_track = SwitchableVideoTrack()
            self.audio_track = SwitchableAudioTrack()
        except Exception as e:
            print(f"初��化媒体轨道失败: {e}")
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

    def start_local_preview(self):
        """优化的本地预览启动"""
        try:
            if not hasattr(self, 'video_thread') or not self.video_thread:
                print("开始初始化本地视频预览...")
                self.video_thread = VideoUpdateThread(self.video_track, is_remote=False)
                
                # 确保使用 Qt.QueuedConnection
                self.video_thread.frame_ready.connect(
                    self.local_video_widget.update_frame,
                    type=Qt.QueuedConnection
                )
                self.video_thread.fps_updated.connect(
                    self.update_local_fps,
                    type=Qt.QueuedConnection
                )
                
                self.video_thread.start()
                print("本地视频预览线程已启动")
        except Exception as e:
            print(f"启动本地预览失败: {e}")
            traceback.print_exc()

    def stop_local_preview(self):
        """停止本地视频预览"""
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread.wait()
            self.video_thread = None

    def stop_all(self):
        """改进资源清���"""
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

    def toggle_video(self, enabled):
        """切换视频状态"""
        try:
            if self.video_track:
                self.video_track.switch(enabled)
                print(f"视频状态已切换为: {'开启' if enabled else '关闭'}")
        except Exception as e:
            print(f"切换视频状态失败: {e}")
            
    def toggle_audio(self, enabled):
        """切换音频状态"""
        try:
            if self.audio_track:
                self.audio_track.switch(enabled)
                print(f"音频状态已切换为: {'开启' if enabled else '关闭'}")
        except Exception as e:
            print(f"切换音频状态失败: {e}")

class WebRTCClient(QMainWindow):

    start_remote_video_signal = pyqtSignal()
    start_remote_audio_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('P2P Video Chat')
        
        # 使用单例事件循环管���器
        self.loop_manager = EventLoopManager.instance()
        self.loop_manager.init()
        self.loop = self.loop_manager.get_loop()
        
        # 添加帧计数���关属性
        self.frame_count = 0
        self._last_frame_update = time.time()
        
        # 基础组件初始化
        self.socket_thread = SocketThread()
        self.pc = None
        self.local_video = None
        self.remote_video = None
        self.video_track = None 
        self.audio_track = None
        self.video_thread = None
        self.remote_video_thread = None
        self.is_room_joined = False
        self.is_video_enabled = False
        self.is_audio_enabled = False
        self.server_connected = False
        self.local_video_enabled = False
        self.remote_audio = None  # 添加远程音频轨道属性
        
        # 创建事件循环
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()
        
        # 等待主事件循环启动
        time.sleep(0.1)
        
        self.start_remote_video_signal.connect(self.start_remote_video, Qt.QueuedConnection)
        self.start_remote_audio_signal.connect(self.start_remote_audio, Qt.QueuedConnection)
        
        # 初始化界面和连接
        self.setup_ui()
        self.setup_socket_signals()
        self.webrtc = WebRTCManager(self.loop)
        self.media_manager = MediaTrackManager()
        self.media_manager.create_tracks()
        self.setup_default_tracks()
        self.start_local_preview()
        self._cleanup_lock = threading.Lock()
        self._is_closing = False
        self._shutdown_event = threading.Event()
        self.setup_audio_handling()  # 添加这行代码

    def closeEvent(self, event):
        """完全重写的关闭事件处理"""
        if self._is_closing:
            event.accept()
            return
            
        self._is_closing = True
        
        try:
            # 1. 首先断开所有信号连接
            self.disconnect_all_signals()
            
            # 2. 停止视频相关线程
            self.stop_video_threads()
            
            # 3. 清理WebRTC连接
            self.cleanup_webrtc()
            
            # 4. 停止媒体管��器
            self.cleanup_media_manager()
            
            # 5. 最后停止事件循环
            self.stop_event_loop()
            
        except Exception as e:
            print(f"关闭时发生错误: {e}")
            traceback.print_exc()
        finally:
            self._is_closing = False
            event.accept()
            # 使用单独的线程确保应用程序退出
            threading.Thread(target=self.force_quit).start()

    def disconnect_all_signals(self):
        """断开所有信号连接"""
        try:
            if hasattr(self, 'socket_thread'):
                self.socket_thread.message_received.disconnect()
                self.socket_thread.ready_signal.disconnect()
                self.socket_thread.offer_received.disconnect()
                self.socket_thread.answer_received.disconnect()
                self.socket_thread.candidate_received.disconnect()
        except Exception as e:
            print(f"断开信号连接时出错: {e}")

    def stop_video_threads(self):
        """停止所有视频相关线程"""
        threads = [
            ('video_thread', self.video_thread),
            ('remote_video_thread', self.remote_video_thread)
        ]
        
        for name, thread in threads:
            if thread:
                try:
                    print(f"正在停止 {name}...")
                    thread.stop()
                    thread.wait(1000)
                    if thread.isRunning():
                        thread.terminate()
                        thread.wait(500)
                except Exception as e:
                    print(f"停止 {name} 时出错: {e}")

    def cleanup_webrtc(self):
        """清理WebRTC连接"""
        if hasattr(self, 'webrtc') and self.webrtc and self.webrtc.pc:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.webrtc.close_connection(),
                    self.loop
                )
                future.result(timeout=1)
            except Exception as e:
                print(f"清理WebRTC连接时出错: {e}")

    def cleanup_media_manager(self):
        """清理媒体管理器"""
        if hasattr(self, 'media_manager'):
            try:
                self.media_manager.stop_all()
                self.cleanup_audio()
            except Exception as e:
                print(f"清理媒体管理器时出错: {e}")

    def stop_event_loop(self):
        """停止事件循环"""
        if hasattr(self, 'loop_manager'):
            try:
                self.loop_manager.stop()
            except Exception as e:
                print(f"停止事件循环��出错: {e}")

    def force_quit(self):
        """强制退出应用程序"""
        try:
            time.sleep(0.5)  # 给予清理过程一些时间
            os._exit(0)  # 强制终止进程
        except:
            sys.exit(1)

    def __del__(self):
        """优化析构函数"""
        if not self._is_closing:
            self.closeEvent(None)

    def setup_default_tracks(self):
        """初始化默认的媒体轨道（���屏和��音）"""
        self.video_track = self.media_manager.get_video_track(False)
        self.audio_track = self.media_manager.get_audio_track(False)

    def start_local_preview(self):
        if hasattr(self, 'media_manager'):
            if not hasattr(self.media_manager, 'local_video_widget'):
                self.media_manager.local_video_widget = self.local_video_widget
            if not hasattr(self.media_manager, 'update_local_fps'):
                self.media_manager.update_local_fps = self.update_local_fps
            self.media_manager.start_local_preview()
        else:
            print("MediaTrackManager 未初始化")

    def start_remote_video(self):
        try:
            if not self.remote_video_thread:
                if not hasattr(self, 'remote_video') or not self.remote_video:
                    print("警告: 远程视频轨道尚未就绪")
                    return
                    
                print("开始初始化远程视频线程")
                self.remote_video_thread = VideoUpdateThread(
                    self.remote_video, 
                    is_remote=True,
                    parent_loop=self.loop
                )
                
                # 确保信号连接使用 Qt.QueuedConnection
                self.remote_video_thread.frame_ready.connect(
                    self.remote_video_widget.update_frame,
                    type=Qt.QueuedConnection
                )
                self.remote_video_thread.fps_updated.connect(
                    self.update_remote_fps,
                    type=Qt.QueuedConnection
                )
                self.remote_video_thread.error_occurred.connect(
                    lambda err: print(f"视频线程错误: {err}"),
                    type=Qt.QueuedConnection
                )
                
                # 启动线程前确保之前的线程已完全停止
                if hasattr(self, '_prev_remote_thread'):
                    self._prev_remote_thread.stop()
                    self._prev_remote_thread.wait()
                    
                self.remote_video_thread.start()
                self._prev_remote_thread = self.remote_video_thread
                print("远程视频线程已启动")
                
        except Exception as e:
            print(f"启动远程视频流失败: {e}")
            traceback.print.exc()
    
    def _on_remote_video_finished(self):
        print("远程视频线程已结束")
        self.remote_video_thread = None

    def update_local_fps(self, fps):
        self.local_fps_label.setText(f"Local FPS: {fps}")

    def update_remote_fps(self, fps):
        self.remote_fps_label.setText(f"Remote FPS: {fps}")

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def setup_ui(self):
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 视频显示区域
        video_layout = QHBoxLayout()
        
        # 本地视频部分
        local_container = QVBoxLayout()
        self.local_video_widget = VideoWidget("本地视频")
        self.local_fps_label = QLabel("Local FPS: 0")
        local_container.addWidget(self.local_video_widget)
        local_container.addWidget(self.local_fps_label)
        
        # 远程视频部分
        remote_container = QVBoxLayout()
        self.remote_video_widget = VideoWidget("远程视频")
        self.remote_fps_label = QLabel("Remote FPS: 0")
        remote_container.addWidget(self.remote_video_widget)
        remote_container.addWidget(self.remote_fps_label)
        
        # 添加到视频布局
        video_layout.addLayout(local_container)
        video_layout.addLayout(remote_container)
        main_layout.addLayout(video_layout)
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        self.video_button = QPushButton('开启视频')
        self.audio_button = QPushButton('开启音频')
        control_layout.addWidget(self.video_button)
        control_layout.addWidget(self.audio_button)
        main_layout.addLayout(control_layout)
        
        # 房间控制区域
        room_layout = QHBoxLayout()
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText('输入房间号')
        self.join_button = QPushButton('加入房间')
        room_layout.addWidget(self.room_input)
        room_layout.addWidget(self.join_button)
        main_layout.addLayout(room_layout)
        
        # FPS显示区域
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(self.local_fps_label)
        fps_layout.addWidget(self.remote_fps_label)
        main_layout.addLayout(fps_layout)
        
        # 消息显示区域
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setMinimumHeight(100)
        main_layout.addWidget(self.message_display)
        
        # 消息输入区域
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText('输入消息')
        self.send_button = QPushButton('发送')
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)
        main_layout.addLayout(message_layout)
        
        # 设置中央窗口部件的布局
        central_widget.setLayout(main_layout)
        
        # 绑定按钮事件
        self.video_button.clicked.connect(self.toggle_video)
        self.audio_button.clicked.connect(self.toggle_audio)
        self.join_button.clicked.connect(self.join_room)
        self.send_button.clicked.connect(self.send_message)
        
        # 初始化按钮状态
        self.video_button.setEnabled(False)
        self.audio_button.setEnabled(False)
        
        # 设置窗口大小
        self.setMinimumSize(800, 600)

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
                print(f"加入��间失败: {e}")

    def create_new_peer_connection(self):
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
                    print(f"收到新轨道: {track.kind}")
                    if track.kind == "video":
                        async def test_track():
                            try:
                                test_frame = await track.recv()
                                print(f"测试帧接收成功: {test_frame is not None}")
                            except Exception as e:
                                print(f"测试帧接收失败: {e}")
                        asyncio.run_coroutine_threadsafe(test_track(), self.loop)
                        
                        self.remote_video = track
                        self.start_remote_video_signal.emit()
                        print("远程视频轨道处理完成")
                    elif track.kind == "audio":
                        self.remote_audio = track
                        self.start_remote_audio_signal.emit()
                
                # 直接添加轨道，始终保持活跃
                pc.addTrack(self.video_track)
                pc.addTrack(self.audio_track)
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
            had_video = self.video_track is not None
            had_audio = self.audio_track is not None
            if self.pc:
                await self.pc.close()
                self.pc = None
                await asyncio.sleep(0.5)
            ice_configuration = RTCConfiguration([
                RTCIceServer(urls=['stun:49.235.44.81:3478'])
            ])
            self.pc = RTCPeerConnection(configuration=ice_configuration)
            @self.pc.on('connectionstatechange')
            def on_connectionstatechange():
                print(f"连接状态变更: {self.pc.connectionState}")
                
            @self.pc.on('signalingstatechange')    
            def on_signalingstatechange():
                print(f"信令状态变更: {self.pc.signalingState}")
            
            await asyncio.sleep(0.5)
            if had_video:
                await self.add_video_track()
            if had_audio:
                await self.add_audio_track()
                
            await self.pc.setRemoteDescription(
                RTCSessionDescription(sdp=data['sdp'], type='offer')
            )
            
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            
            self.socket_thread.sio.emit('answer', {
                'room': self.room_input.text(),
                'sdp': self.pc.localDescription.sdp
            })
            
        except Exception as e:
            print(f"处理offer失败: {e}")
            print(f"当前信令状态: {self.pc.signalingState if self.pc else 'None'}")
            traceback.print.exc()
            raise e

    async def setup_media_tracks(self):
        try:
            if not self.webrtc.pc:
                return
            if self.video_track:
                self.webrtc.pc.addTrack(self.video_track)
            if self.audio_track:
                self.webrtc.pc.addTrack(self.audio_track)
        except Exception as e:
            print(f"设置媒体轨道失败: {e}")

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
        try:
            self.local_video_enabled = not self.local_video_enabled
            if hasattr(self.media_manager, 'toggle_video'):
                self.media_manager.toggle_video(self.local_video_enabled)
                self.video_button.setText('关闭视频' if self.local_video_enabled else '开启视频')
        except Exception as e:
            print(f"视频切换失败: {e}")
            traceback.print.exc()

    def toggle_audio(self):
        """音频开关处理"""
        self.is_audio_enabled = not self.is_audio_enabled
        self.media_manager.toggle_audio(self.is_audio_enabled)
        self.audio_button.setText('关闭音频' if self.is_audio_enabled else '开启音频')

    async def add_video_track(self):
        if self.video_track and self.pc:
            print("添加视频轨道")
            self.pc.addTrack(self.video_track)

    async def add_audio_track(self):
        if self.audio_track and self.pc:
            self.pc.addTrack(self.audio_track)

    def start_remote_audio(self):
        """改进的远程音频启动"""
        if self.remote_audio:
            try:
                print("开始处理远程音频轨道")
                self.remote_audio_enabled = True
                self.handle_remote_audio(self.remote_audio)
            except Exception as e:
                print(f"启动远程音频失败: {e}")
                traceback.print_exc()

    def setup_audio_handling(self):
        """设置音频处理"""
        self.audio_enabled = False
        self.remote_audio_enabled = False
        self.audio_output = None
        try:
            import sounddevice as sd
            self.audio_output = sd.OutputStream(
                channels=1,
                samplerate=48000,
                dtype='int16'
            )
            self.audio_output.start()
        except Exception as e:
            print(f"初始化音频输出失败: {e}")

    def cleanup_audio(self):
        """清理音频资源"""
        try:
            if self.audio_output:
                self.audio_output.stop()
                self.audio_output.close()
                self.audio_output = None
        except Exception as e:
            print(f"清理音频资源失败: {e}")

    def handle_remote_audio(self, audio_track):
        """处理远程音频"""
        try:
            if not self.audio_output:
                self.setup_audio_handling()
                
            async def process_remote_audio():
                while True:
                    try:
                        frame = await audio_track.recv()
                        if self.audio_output and self.remote_audio_enabled:
                            self.audio_output.write(frame.to_ndarray())
                    except MediaStreamError:
                        break
                    except Exception as e:
                        print(f"处理远程音频失败: {e}")
                        await asyncio.sleep(0.1)
                        
            asyncio.run_coroutine_threadsafe(
                process_remote_audio(),
                self.loop
            )
        except Exception as e:
            print(f"启动远程音频处理失败: {e}")

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

    def closeEvent(self, event):
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
     
    def clean_up_resources(self):
        with self._cleanup_lock:
            if self._is_closing:
                return
            self._is_closing = True
            
            try:
                # 停止视频处理
                if self.video_thread:
                    self.video_thread.stop()
                    self.video_thread.wait(1000)
                
                if self.remote_video_thread:
                    self.remote_video_thread.stop()
                    self.remote_video_thread.wait(1000)
                
                # 关闭WebRTC连接
                if self.webrtc and self.webrtc.pc:
                    future = asyncio.run_coroutine_threadsafe(
                        self.webrtc.close_connection(),
                        self.loop
                    )
                    future.result(timeout=5)
                
                # 停止媒体轨道
                if hasattr(self, 'media_manager'):
                    self.media_manager.stop_all()
                
                # 清理事件循环
                if self.loop and not self.loop.is_closed():                    
                    self.loop.call_soon_threadsafe(self.loop.stop)                                
            except Exception as e:                
                print(f"清理资源时发生错误: {e}")            
            finally:                
                self._is_closing = False    
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
            self.display_message(f'我: {message}')            
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
            traceback.print.exc()

    def handle_offer(self, data):
        try:
            future = asyncio.run_coroutine_threadsafe(self._handle_offer(data), self.loop)
            future.result(timeout=10)
        except Exception as e:
            print(f"处理 offer 失败: {e}")
            traceback.print.exc()

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