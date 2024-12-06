import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget


class QTencentMeeting(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('腾讯会议')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        # 创建一个按钮用于模拟加入会议
        join_button = QPushButton('加入会议', self)
        join_button.clicked.connect(self.join_meeting)

        # 创建一个垂直布局，并添加按钮
        layout = QVBoxLayout()
        layout.addWidget(join_button)

        # 创建一个widget，并设置布局
        main_widget = QWidget()
        main_widget.setLayout(layout)

        # 设置主widget
        self.setCentralWidget(main_widget)

    def join_meeting(self):
        # 模拟加入会议的逻辑
        print('正在加入会议...')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = QTencentMeeting()
    main.show()
    sys.exit(app.exec_())