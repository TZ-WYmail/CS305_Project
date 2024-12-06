from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication

class InviteMessageWindow(QWidget):
    def __init__(self, meeting_id, attendees, parent=None):
        super(InviteMessageWindow, self).__init__(parent)
        self.meeting_id = meeting_id
        self.attendees = attendees
        self.initUI()

    def initUI(self):
        self.setWindowTitle('会议邀请')
        self.setGeometry(100, 100, 300, 200)  # 设置窗口位置和大小

        layout = QVBoxLayout(self)

        # 添加会议号标签
        meeting_id_label = QLabel(f'会议号: {self.meeting_id}')
        layout.addWidget(meeting_id_label)

        # 添加参会人员标签
        attendees_label = QLabel('参会人员:')
        layout.addWidget(attendees_label)
        for attendee in self.attendees:
            attendee_label = QLabel(attendee)
            layout.addWidget(attendee_label)

        self.setLayout(layout)