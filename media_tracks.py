import av
import cv2
import numpy as np
import threading
from aiortc import MediaStreamTrack

class VideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        # 尝试多个摄像头设备
        for i in range(2):
            self.cap = cv2.VideoCapture(i)
            if self.cap.isOpened():
                break
        if not self.cap.isOpened():
            raise RuntimeError("无法打开摄像头")
            
        # 设置摄像头分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._enabled = True
        self._frame = None
        self._frame_lock = threading.Lock()

    @property
    def enabled(self):
        return getattr(self, '_enabled', True)

    @enabled.setter
    def enabled(self, value):
        self._enabled = bool(value)

    def get_frame(self):
        with self._frame_lock:
            if not self.enabled:
                return None
            ret, frame = self.cap.read()
            if ret:
                # 水平翻转，使其像镜子
                frame = cv2.flip(frame, 1)
                self._frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return self._frame.copy() if self._frame is not None else None

    async def recv(self):
        frame = self.get_frame()
        if frame is None:
            return None
        
        video_frame = av.VideoFrame.from_ndarray(frame, format='rgb24')
        return video_frame

    def __del__(self):
        self.cap.release()

class AudioStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.enabled = True
        # 这里可以添加音频输入设备的初始化

    async def recv(self):
        # 实现音频帧的获取和处理
        pass