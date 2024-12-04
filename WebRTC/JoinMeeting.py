from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton


class JoinMeetingDialog(QDialog):
    def __init__(self, parent=None):
        super(JoinMeetingDialog, self).__init__(parent)
        self.setWindowTitle('加入会议')
        self.setGeometry(100, 100, 300, 150)  # 设置窗口大小和位置

        layout = QVBoxLayout()

        self.meeting_id_label = QLabel('会议号：')
        self.meeting_id_input = QLineEdit()
        self.join_button = QPushButton('加入')

        layout.addWidget(self.meeting_id_label)
        layout.addWidget(self.meeting_id_input)
        layout.addWidget(self.join_button)

        self.setLayout(layout)

        self.join_button.clicked.connect(self.accept)  # 连接加入按钮的点击事件

    def get_meeting_id(self):
        return self.meeting_id_input.text()  # 获取输入的会议号