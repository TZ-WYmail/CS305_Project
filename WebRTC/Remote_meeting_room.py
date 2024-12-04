# -*- coding: utf-8 -*-
import threading

from PyQt5.QtCore import QRect, Qt, QCoreApplication, QMetaObject, QSize
from PyQt5.QtGui import QFont, QCursor, QPalette, QColor, QBrush, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QSizePolicy, QDialog
from WebRTC.JoinMeeting import JoinMeetingDialog




class Ui_Remote_meeting_room(object):

    def setupUi(self, Remote_meeting_room, MainWindow):
        self.MainWindow = MainWindow
        self.client = MainWindow.client
        if not Remote_meeting_room.objectName():
            Remote_meeting_room.setObjectName(u"Remote_meeting_room")
        Remote_meeting_room.setWindowModality(Qt.WindowModal)
        Remote_meeting_room.resize(1200, 650)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Remote_meeting_room.sizePolicy().hasHeightForWidth())
        Remote_meeting_room.setSizePolicy(sizePolicy)
        Remote_meeting_room.setAutoFillBackground(False)
        Remote_meeting_room.setStyleSheet(u"border-color: rgb(0, 0, 0);\n"
                                          "border-width: 10px; /* \u8bbe\u7f6e\u8fb9\u754c\u7ebf\u7684\u7c97\u7ec6\u4e3a1\u50cf\u7d20 */")
        self.navigated_widget = QWidget(Remote_meeting_room)
        self.navigated_widget.setObjectName(u"navigated_widget")
        self.navigated_widget.setGeometry(QRect(0, 0, 110, 650))
        sizePolicy.setHeightForWidth(self.navigated_widget.sizePolicy().hasHeightForWidth())
        self.navigated_widget.setSizePolicy(sizePolicy)
        self.navigated_widget.setStyleSheet(u"background-color: rgb(238, 238, 239);\n"
                                            "color: rgb(108, 108, 108);\n"
                                            "font: 10pt \"Arial\";")
        self.header_image = QLabel(self.navigated_widget)
        self.header_image.setObjectName(u"header_image")
        self.header_image.setGeometry(QRect(0, 0, 80, 60))
        sizePolicy.setHeightForWidth(self.header_image.sizePolicy().hasHeightForWidth())
        self.header_image.setSizePolicy(sizePolicy)
        self.conference_Button = QPushButton(self.navigated_widget)
        self.conference_Button.setObjectName(u"conference_Button")
        self.conference_Button.setGeometry(QRect(0, 120, 100, 60))
        sizePolicy.setHeightForWidth(self.conference_Button.sizePolicy().hasHeightForWidth())
        self.conference_Button.setSizePolicy(sizePolicy)
        self.conference_Button.setStyleSheet(u"background-color: rgb(230, 232, 235);\n"
                                             "color: rgb(108, 108, 108);\n"
                                             "font: 8pt \"Arial\";")
        self.list_Button = QPushButton(self.navigated_widget)
        self.list_Button.setObjectName(u"list_Button")
        self.list_Button.setGeometry(QRect(0, 220, 100, 60))
        sizePolicy.setHeightForWidth(self.list_Button.sizePolicy().hasHeightForWidth())
        self.list_Button.setSizePolicy(sizePolicy)
        self.list_Button.setStyleSheet(u"background-color: rgb(230, 232, 235);\n"
                                       "color: rgb(108, 108, 108);\n"
                                       "font: 8pt \"Arial\";")
        self.setting_Button = QPushButton(self.navigated_widget)
        self.setting_Button.setObjectName(u"setting_Button")
        self.setting_Button.setGeometry(QRect(0, 540, 100, 60))
        sizePolicy.setHeightForWidth(self.setting_Button.sizePolicy().hasHeightForWidth())
        self.setting_Button.setSizePolicy(sizePolicy)
        self.setting_Button.setStyleSheet(u"background-color: rgb(230, 232, 235);\n"
                                          "color: rgb(108, 108, 108);\n"
                                          "font: 8pt \"Arial\";")
        self.inform_Button = QPushButton(self.navigated_widget)
        self.inform_Button.setObjectName(u"inform_Button")
        self.inform_Button.setGeometry(QRect(0, 420, 100, 60))
        sizePolicy.setHeightForWidth(self.inform_Button.sizePolicy().hasHeightForWidth())
        self.inform_Button.setSizePolicy(sizePolicy)
        self.inform_Button.setStyleSheet(u"background-color: rgb(230, 232, 235);\n"
                                         "color: rgb(108, 108, 108);\n"
                                         "font: 8pt \"Arial\";")
        self.state_widget = QWidget(Remote_meeting_room)
        self.state_widget.setObjectName(u"state_widget")
        self.state_widget.setGeometry(QRect(592, 0, 760, 650))
        self.state_widget.setStyleSheet(u"background-color: rgb(255, 255, 255);\n"
                                        "color: rgb(108, 108, 108);\n"
                                        "font: 10pt \"Arial\";\n"
                                        "border-color: rgb(223, 223, 223);\n"
                                        "border-width: 1px; /* \u8bbe\u7f6e\u8fb9\u754c\u7ebf\u7684\u7c97\u7ec6\u4e3a1\u50cf\u7d20 */")
        self.time_widget = QWidget(self.state_widget)
        self.time_widget.setObjectName(u"time_widget")
        self.time_widget.setGeometry(QRect(0, 0, 760, 300))
        self.time_widget.setMouseTracking(False)
        self.time_widget.setTabletTracking(False)
        self.time_label = QLabel(self.time_widget)
        self.time_label.setObjectName(u"time_label")
        self.time_label.setGeometry(QRect(20, 20, 140, 60))
        font = QFont()
        font.setFamily(u"Arial Black")
        font.setPointSize(20)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(10)
        self.time_label.setFont(font)
        self.time_label.setStyleSheet(u"font: 87 20pt \"Arial Black\";")
        self.time_label.setTextFormat(Qt.PlainText)
        self.login_label = QLabel(self.time_widget)
        self.login_label.setObjectName(u"login_label")
        self.login_label.setGeometry(QRect(0, 140, 120, 24))
        self.login_label.setStyleSheet(u"font: 9pt \"Arial Narrow\";")
        self.label = QLabel(self.time_widget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(0, 180, 120, 60))
        self.label.setStyleSheet(u"font: 9pt \"Arial Narrow\";")
        self.widget_2 = QWidget(self.state_widget)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setGeometry(QRect(0, 300, 760, 660))
        self.widget = QWidget(Remote_meeting_room)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(110, 0, 480, 650))
        self.widget.setStyleSheet(u"background-color: rgb(255, 255, 255);\n"
                                  "color: rgb(108, 108, 108);\n"
                                  "font: 10pt \"Arial\";\n"
                                  "border-width: 1px; /* \u8bbe\u7f6e\u8fb9\u754c\u7ebf\u7684\u7c97\u7ec6\u4e3a1\u50cf\u7d20 */")
        self.join_Button = QPushButton(self.widget)
        self.join_Button.setObjectName(u"join_Button")
        self.join_Button.setGeometry(QRect(160, 80, 160, 160))
        sizePolicy.setHeightForWidth(self.join_Button.sizePolicy().hasHeightForWidth())
        self.join_Button.setSizePolicy(sizePolicy)
        palette = QPalette()
        brush = QBrush(QColor(255, 255, 255, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        brush1 = QBrush(QColor(11, 117, 255, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Button, brush1)
        brush2 = QBrush(QColor(85, 170, 255, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Light, brush2)
        brush3 = QBrush(QColor(0, 0, 255, 255))
        brush3.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Midlight, brush3)
        palette.setBrush(QPalette.Active, QPalette.Text, brush)
        palette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush4 = QBrush(QColor(255, 255, 255, 128))
        brush4.setStyle(Qt.NoBrush)
        #if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush4)
        #endif
        palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Light, brush2)
        palette.setBrush(QPalette.Inactive, QPalette.Midlight, brush3)
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush5 = QBrush(QColor(255, 255, 255, 128))
        brush5.setStyle(Qt.NoBrush)
        #if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush5)
        #endif
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Light, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.Midlight, brush3)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush6 = QBrush(QColor(255, 255, 255, 128))
        brush6.setStyle(Qt.NoBrush)
        #if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush6)
        #endif
        self.join_Button.setPalette(palette)
        self.join_Button.setStyleSheet(u"background-color: rgb(11, 117, 255);\n"
                                       "color: rgb(255, 255, 255);\n"
                                       "font: 10pt \"Arial\";\n"
                                       "font-weight: bold; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u52a0\u7c97 */\n"
                                       "border-radius: 20px; \n"
                                       "border-color: rgb(223, 223, 223);\n"
                                       "border-width: 1px; /* \u8bbe\u7f6e\u8fb9\u754c\u7ebf\u7684\u7c97\u7ec6\u4e3a1\u50cf\u7d20 */")
        self.join_Button.setIconSize(QSize(64, 64))
        self.join_Button.setAutoDefault(False)
        self.join_Button.setFlat(False)
        self.create_Button = QPushButton(self.widget)
        self.create_Button.setObjectName(u"create_Button")
        self.create_Button.setGeometry(QRect(160, 340, 160, 160))
        sizePolicy.setHeightForWidth(self.create_Button.sizePolicy().hasHeightForWidth())
        self.create_Button.setSizePolicy(sizePolicy)
        self.create_Button.setCursor(QCursor(Qt.ArrowCursor))
        self.create_Button.setStyleSheet(u" background-color: rgb(11, 117, 255);\n"
                                         "    color: rgb(255, 255, 255);\n"
                                         "    font: 10pt \"Arial\";\n"
                                         "    font-weight: bold; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u52a0\u7c97 */\n"
                                         "    border-radius: 20px; /* \u8bbe\u7f6e\u5706\u89d2\u7684\u534a\u5f84\u4e3a10\u50cf\u7d20 */")
        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(170, 250, 131, 61))
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(160, 560, 151, 41))
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setTextFormat(Qt.MarkdownText)
        self.label_3.setScaledContents(False)
        self.label_3.setAlignment(Qt.AlignCenter)

        self.retranslateUi(Remote_meeting_room)

        self.join_Button.setDefault(False)

        QMetaObject.connectSlotsByName(Remote_meeting_room)


        #配置按钮
        self.set_button()

    # setupUi

    def retranslateUi(self, Remote_meeting_room):
        Remote_meeting_room.setWindowTitle(QCoreApplication.translate("Remote_meeting_room", u"Form", None))
        self.header_image.setText(QCoreApplication.translate("Remote_meeting_room", u"\u5934\u50cf", None))
        self.conference_Button.setText(QCoreApplication.translate("Remote_meeting_room", u"\u4f1a\u8bae", None))
        self.list_Button.setText(QCoreApplication.translate("Remote_meeting_room", u"\u5217\u8868", None))
        self.setting_Button.setText(QCoreApplication.translate("Remote_meeting_room", u"\u8bbe\u7f6e", None))
        self.inform_Button.setText(QCoreApplication.translate("Remote_meeting_room", u"\u4fe1\u606f", None))
        self.time_label.setText(QCoreApplication.translate("Remote_meeting_room", u"\u65e5\u671f", None))
        self.login_label.setText(QCoreApplication.translate("Remote_meeting_room", u"\u662f\u5426\u767b\u9646", None))
        self.label.setText(QCoreApplication.translate("Remote_meeting_room", u"\u7528\u6237\u4fe1\u606f", None))
        self.join_Button.setText(QCoreApplication.translate("Remote_meeting_room", u"\u52a0\u5165\u4f1a\u8bae", None))
        self.create_Button.setText(QCoreApplication.translate("Remote_meeting_room", u"\u521b\u5efa\u4f1a\u8bae", None))
        self.label_2.setText(QCoreApplication.translate("Remote_meeting_room", u"\u52a0\u5165\u4f1a\u8bae", None))
        self.label_3.setText(QCoreApplication.translate("Remote_meeting_room", u"\u521b\u5efa\u4f1a\u8bae", None))

    # retranslateUi

    def on_conference_button_clicked(self):
        print("会议按钮被点击")

    def on_list_button_clicked(self):
        print("列表按钮被点击")
        self.client.handle_input('list')

    def on_setting_button_clicked(self):
        print("设置按钮被点击")

    def on_inform_button_clicked(self):
        print("信息按钮被点击")
        self.client.handle_input('help')

    def on_join_meeting_button_clicked(self):
        dialog = JoinMeetingDialog()
        if dialog.exec_() == QDialog.Accepted:  # 如果用户点击了加入按钮
            meeting_id = dialog.get_meeting_id()
            print(f"加入会议号：{meeting_id}")
            self.client.handle_input('join ' + meeting_id)
            # 假设加入会议成功后，显示聊天室窗口
            from Main import MainWindow
            self.MainWindow.showChatRoom()

    def on_create_meeting_button_clicked(self):
        from Main import MainWindow
        print("创建会议按钮被点击")
        self.client.handle_input('create')
        self.MainWindow.showChatRoom()

    # 为按钮设置图标
    def set_button(self):
        # 为conference_Button绑定点击事件
        self.conference_Button.clicked.connect(self.on_conference_button_clicked)
        # 为list_Button绑定点击事件
        self.list_Button.clicked.connect(self.on_list_button_clicked)
        # 为setting_Button绑定点击事件
        self.setting_Button.clicked.connect(self.on_setting_button_clicked)
        # 为inform_Button绑定点击事件
        self.inform_Button.clicked.connect(self.on_inform_button_clicked)
        # 为pushButton_2绑定点击事件
        self.join_Button.clicked.connect(self.on_join_meeting_button_clicked)
        # 为create_Button绑定点击事件
        self.create_Button.clicked.connect(self.on_create_meeting_button_clicked)

        self.conference_Button.setIcon(QIcon("icon/main.png"))
        self.list_Button.setIcon(QIcon("icon/list.png"))
        self.setting_Button.setIcon(QIcon("icon/setting.png"))
        self.inform_Button.setIcon(QIcon("icon/info.png"))

        self.join_Button.setIcon(QIcon("icon/join.png"))
        self.create_Button.setIcon(QIcon("icon/create.png"))


