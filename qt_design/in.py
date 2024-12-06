from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

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

class SIQIUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('P2P Video Chat UI')

        self.setup_ui()

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
        # self.video_button = QPushButton('开启视频')
        # self.audio_button = QPushButton('开启音频')
        # self.video_button.clicked.connect(self.toggle_video)
        # self.audio_button.clicked.connect(self.toggle_audio)
        # control_layout.addWidget(self.video_button)
        # control_layout.addWidget(self.audio_button)

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

        #消息输入
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
        # layout.addLayout(message_layout)

        # 更新按钮状态
        # self.video_button.setEnabled(True)
        # self.audio_button.setEnabled(True)
        # self.video_button.setText('开启视频')
        # self.audio_button.setText('开启音频')

    def toggle_video(self):
        # 视频开关逻辑
        pass

    def toggle_audio(self):
        # 音频开关逻辑
        pass

    def join_room(self):
        # 加入房间逻辑
        room = self.room_input.text()
        if room:
            self.display_message(f'已加入房间: {room}')
        else:
            self.display_message('请输入房间号')

    def send_message(self):
        message = self.message_input.text()
        if message:
            self.display_message(f'你: {message}')
            self.message_input.clear()

    def display_message(self, message):
        self.message_display.append(message)

if __name__ == '__main__':
    app = QApplication([])
    window = SIQIUI()
    window.show()
    app.exec_()
