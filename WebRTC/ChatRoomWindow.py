import threading
import time

import cv2
import numpy as np
import pyaudio
from PyQt5 import Qt
from PyQt5.QtCore import QSize, QRect, QMetaObject, QCoreApplication, Qt
from PyQt5.QtGui import QCursor, QPixmap, QImage
from PyQt5.QtWidgets import QGridLayout, QFrame, QPushButton, QTextEdit, QSizePolicy, QLabel

from WebRTC.ListWindow import ListWindow
from WebRTC.MessageWindow import MessageWindow


class UI_ChatRoomWindow(object):
    def setupUi(self, ChatRoomWindow, MainWindow):
        self.MainWindow = MainWindow
        self.client = MainWindow.client
        self.client.ChatRoomWindow = ChatRoomWindow

        self.is_video = False

        self.is_audio = False
        self.is_audio = False
        self.audio_format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()
        self.lock = threading.Lock()

        ChatRoomWindow.setObjectName("ChatRoomWindow")
        ChatRoomWindow.resize(1100, 639)
        if not ChatRoomWindow.objectName():
            ChatRoomWindow.setObjectName(u"Room_Form")
        ChatRoomWindow.resize(863, 651)
        self.gridLayout = QGridLayout(ChatRoomWindow)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_video = QFrame(ChatRoomWindow)
        self.frame_video.setObjectName(u"frame_video")
        self.frame_video.setStyleSheet(u"\n"
                                       "background-color: rgb(198, 198, 198);")
        self.frame_video.setFrameShape(QFrame.StyledPanel)
        self.frame_video.setFrameShadow(QFrame.Raised)

        self.gridLayout.addWidget(self.frame_video, 0, 0, 1, 1)

        self.videoLayout = QGridLayout(self.frame_video)  # 创建九宫格布局
        self.videoLayout.setObjectName(u"videoLayout")
        self.videoLayout.setContentsMargins(0, 0, 0, 0)
        self.videoLayout.setSpacing(5)  # 设置网格间距为0
        self.videoLabels = []

        # 创建9个QLabel用于显示视频帧
        for i in range(3):
            for j in range(3):
                self.videoLabels.append(QLabel(self.frame_video))
                self.videoLabels[-1].setObjectName(u"videoLabel")
                self.videoLayout.addWidget(self.videoLabels[-1], i, j)

        self.Room_frame = QFrame(ChatRoomWindow)
        self.Room_frame.setObjectName(u"Room_frame")
        self.Room_frame.setMaximumSize(QSize(16777215, 50))
        self.Room_frame.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        self.Room_frame.setFrameShape(QFrame.StyledPanel)
        self.Room_frame.setFrameShadow(QFrame.Raised)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ChatRoomWindow.sizePolicy().hasHeightForWidth())
        ChatRoomWindow.setSizePolicy(sizePolicy)

        # 创建并设置按钮样式
        self.Video_Button = QPushButton(self.Room_frame)
        self.Video_Button.setObjectName(u"Video_Button")
        self.Video_Button.setGeometry(QRect(20, 0, 50, 50))
        button_style = """
        QPushButton {
            background-color: rgb(11, 117, 255); /* 默认背景颜色 */
            color: rgb(255, 255, 255); /* 默认文字颜色 */
            font: 10pt "Arial";
            font-weight: bold;
            border-radius: 0px; /* 设置为0px以实现方形边框 */
            border: 1px solid rgb(0, 0, 0); /* 添加边框，颜色为黑色 */
        }
        QPushButton:hover {
            background-color: rgb(0, 150, 255); /* 悬停时背景颜色 */
        }
        QPushButton:pressed {
            background-color: rgb(0, 100, 200); /* 按下时背景颜色 */
        }
        """

        self.Video_Button.setStyleSheet(button_style)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Video_Button.sizePolicy().hasHeightForWidth())
        self.Video_Button.setSizePolicy(sizePolicy)
        self.Video_Button.setCursor(QCursor(Qt.ArrowCursor))

        self.Audio_Button = QPushButton(self.Room_frame)
        self.Audio_Button.setObjectName(u"Audio_Button")
        self.Audio_Button.setGeometry(QRect(130, 0, 50, 50))

        # 设置按钮的默认样式、悬停样式和按下样式

        self.Audio_Button.setStyleSheet(button_style)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Audio_Button.sizePolicy().hasHeightForWidth())
        self.Audio_Button.setSizePolicy(sizePolicy)
        self.Audio_Button.setCursor(QCursor(Qt.ArrowCursor))

        self.Sound_Button = QPushButton(self.Room_frame)
        self.Sound_Button.setObjectName(u"Sound_Button")
        self.Sound_Button.setGeometry(QRect(240, 0, 50, 50))
        # 设置按钮的默认样式、悬停样式和按下样式

        self.Sound_Button.setStyleSheet(button_style)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Sound_Button.sizePolicy().hasHeightForWidth())
        self.Sound_Button.setSizePolicy(sizePolicy)
        self.Sound_Button.setCursor(QCursor(Qt.ArrowCursor))

        self.Quit_Button = QPushButton(self.Room_frame)
        self.Quit_Button.setObjectName(u"Quit_Button")
        self.Quit_Button.setGeometry(QRect(670, 10, 121, 31))
        # 设置按钮的默认样式、悬停样式和按下样式

        self.Quit_Button.setStyleSheet(button_style)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Quit_Button.sizePolicy().hasHeightForWidth())
        self.Quit_Button.setSizePolicy(sizePolicy)
        self.Quit_Button.setCursor(QCursor(Qt.ArrowCursor))

        self.invite_Button = QPushButton(self.Room_frame)
        self.invite_Button.setObjectName(u"invite_Button")
        self.invite_Button.setGeometry(QRect(460, 0, 50, 50))
        # 设置按钮的默认样式、悬停样式和按下样式

        self.invite_Button.setStyleSheet(button_style)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.invite_Button.sizePolicy().hasHeightForWidth())
        self.invite_Button.setSizePolicy(sizePolicy)
        self.invite_Button.setCursor(QCursor(Qt.ArrowCursor))

        self.list_Button = QPushButton(self.Room_frame)
        self.list_Button.setObjectName(u"list_Button")
        self.list_Button.setGeometry(QRect(350, 0, 50, 50))

        # 设置按钮的默认样式、悬停样式和按下样式
        self.list_Button.setStyleSheet(button_style)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.list_Button.sizePolicy().hasHeightForWidth())
        self.list_Button.setSizePolicy(sizePolicy)
        self.list_Button.setCursor(QCursor(Qt.ArrowCursor))

        self.gridLayout.addWidget(self.Room_frame, 1, 0, 1, 2)

        self.chat_text = QFrame(ChatRoomWindow)
        self.chat_text.setObjectName(u"chat_text")
        self.chat_text.setMaximumSize(QSize(250, 16777215))
        self.chat_text.setStyleSheet(u"QFrame{\n"
                                     "	background-color:rgb(255, 255, 255)\n"
                                     "}")
        self.chat_text.setFrameShape(QFrame.StyledPanel)
        self.chat_text.setFrameShadow(QFrame.Raised)
        self.line = QFrame(self.chat_text)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(0, 450, 250, 20))
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.Send_Button = QPushButton(self.chat_text)
        self.Send_Button.setObjectName(u"Send_Button")
        self.Send_Button.setGeometry(QRect(160, 560, 91, 31))
        self.Send_Button.setStyleSheet(u"QPushButton{\n"
                                       "	background-color:rgb(0, 0, 0)\n"
                                       "	color: rgb(0, 0, 127);\n"
                                       "}")

        self.Clear_Button = QPushButton(self.chat_text)
        self.Clear_Button.setObjectName(u"Clear_Button")
        self.Clear_Button.setGeometry(QRect(0, 560, 91, 31))
        self.Clear_Button.setStyleSheet(u"QPushButton{\n"
                                        "	background-color:rgb(0, 0, 0)\n"
                                        "	color: rgb(0, 0, 127);\n"
                                        "}")

        self.message_in = QTextEdit(self.chat_text)
        self.message_in.setObjectName(u"message_in")
        self.message_in.setGeometry(QRect(0, 460, 251, 101))
        self.message_output = QTextEdit(self.chat_text)
        self.message_output.setObjectName(u"message_output")
        self.message_output.setGeometry(QRect(3, 10, 251, 447))
        self.message_output.setReadOnly(True)

        self.gridLayout.addWidget(self.chat_text, 0, 1, 1, 1)

        self.retranslateUi(ChatRoomWindow)

        self.Quit_Button.setDefault(False)

        self.set_button()

        QMetaObject.connectSlotsByName(ChatRoomWindow)

    # setupUi

    def retranslateUi(self, Room_Form):
        Room_Form.setWindowTitle(QCoreApplication.translate("Room_Form", u"Form", None))
        self.Video_Button.setText(QCoreApplication.translate("Room_Form", u"\u89c6\u9891", None))
        self.Audio_Button.setText(QCoreApplication.translate("Room_Form", u"\u58f0\u97f3", None))
        self.Sound_Button.setText(QCoreApplication.translate("Room_Form", u"\u97f3\u91cf", None))
        self.Quit_Button.setText(QCoreApplication.translate("Room_Form", u"\u9000\u51fa\u4f1a\u8bae", None))
        self.list_Button.setText(QCoreApplication.translate("Room_Form", u"\u6210\u5458", None))
        self.invite_Button.setText(QCoreApplication.translate("Room_Form", u"\u9080\u8bf7", None))
        self.Send_Button.setText(QCoreApplication.translate("Room_Form", u"\u53d1\u9001", None))
        self.Clear_Button.setText(QCoreApplication.translate("Room_Form", u" \u6e05\u9664", None))
        self.message_in.setHtml(QCoreApplication.translate("Room_Form",
                                                           u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                                           "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                                                           "p, li { white-space: pre-wrap; }\n"
                                                           "</style></head><body style=\" font-family:'SimSun'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
                                                           "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\u8bf7\u8f93\u5165\u6587\u672c\u4fe1\u606f...</p></body></html>",
                                                           None))

    # retranslateUi

    def set_button(self):
        self.Video_Button.clicked.connect(self.send_video_message)
        self.Audio_Button.clicked.connect(self.send_audio_message)
        # self.Sound_Button.clicked.connect(self.show_sound)
        self.Quit_Button.clicked.connect(self.quit_meeting)
        self.Send_Button.clicked.connect(self.send_chat_message)
        self.Clear_Button.clicked.connect(self.clear_chat_message)
        self.list_Button.clicked.connect(self.show_member_list)
        self.invite_Button.clicked.connect(self.show_invite_mseeage)

    def quit_meeting(self):
        self.client.handle_input('quit')
        self.clear_chat_message()
        self.is_video=False
        self.is_audio=False

    def show_chat_message(self, message):
        self.message_output.append(message)

    def send_chat_message(self):
        message = self.message_in.toPlainText()
        self.message_in.clear()
        self.client.send_chat_message(message)

    def clear_chat_message(self):
        self.message_output.clear()

    def show_member_list(self):
        print("列表按钮被点击")
        print('client.member_list', self.client.member_list)
        # 检查房间列表是否为空，如果不为空，则显示 ListWindow
        self.list_window = ListWindow(self.client.member_list)
        self.list_window.show()  # 显示 ListWindow

    def show_invite_mseeage(self):
        print("邀请按钮被点击")
        # 假设这些是您的会议号和参会人员列表
        meeting_id = self.client.room_id
        attendees = self.client.member_list
        # 创建 InviteMessageWindow 实例并显示
        self.invite_window = MessageWindow(meeting_id, attendees)
        self.invite_window.show()

    def send_video_message(self):
        if not self.is_video:
            self.is_video = True
            threading.Thread(target=self.capture_and_send).start()
        else:
            self.is_video = False

    def capture_and_send(self):
        cap = cv2.VideoCapture(0)
        while self.is_video:
            ret, frame = cap.read()
            time.sleep(0.1)
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                self.client.send_video_message(jpeg.tobytes())
        cap.release()
        # 在线程结束后发送 black.jpg
        self.send_black_frame()

    def send_black_frame(self):
        # 加载一张黑色的图片
        black_image = np.zeros((480, 640, 3), dtype=np.uint8)  # 假设图片大小为 640x480
        ret, jpeg = cv2.imencode('.jpg', black_image)
        if ret:
            self.client.send_video_message(jpeg.tobytes())

    def convert_cv_qt(self, frame_data):
        jpg = np.frombuffer(frame_data, dtype=np.uint8)
        image = cv2.imdecode(jpg, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.videoLabels[0].width(), self.videoLabels[0].height(), Qt.KeepAspectRatio)
        return p

    def show_video_message(self, index, video_message):
        image = self.convert_cv_qt(video_message)
        self.videoLabels[index].setPixmap(QPixmap.fromImage(image))

    def send_audio_message(self):
        if not self.is_audio:
            self.is_audio = True
            threading.Thread(target=self.capture_and_send_audio).start()
        else:
            self.is_audio = False

    def capture_and_send_audio(self):
        global stream
        try:
            stream = self.audio.open(format=self.audio_format,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.chunk)

            while self.is_audio:
                audio_data = stream.read(self.chunk)
                reduced_noise_audio_data = self.reduce_noise(audio_data)
                # 将音频数据发送到服务器
                self.client.send_audio_message(audio_data)
                time.sleep(0.01)  # 降低音频捕获的帧率
        except Exception as e:
            print(f"Error capturing audio: {e}")
        finally:
            with self.lock:  # 确保线程安全
                if self.is_audio:
                    self.is_audio = False
                    stream.stop_stream()
                    stream.close()
                    self.audio.terminate()
                    print("Audio stream stopped and resources released.")


    def reduce_noise(self, audio_data):
        # 降噪过程
        pass

    def show_audio_message(self, data):
        # 直接播放接收到的音频数据
        if self.is_audio:
            stream = self.audio.open(format=self.audio_format,
                                     channels=self.channels,
                                     rate=self.rate,
                                     output=True)

            # 播放音频数据

            stream.write(data)
            stream.stop_stream()
            stream.close()