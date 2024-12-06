from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QDialog


class ListWindow(QWidget):
    def __init__(self, room_list, parent=None):
        super(ListWindow, self).__init__(parent)
        self.room_list = room_list
        self.initUI()

    def initUI(self):
        self.setWindowTitle('列表界面')
        self.setGeometry(100, 100, 300, 200)  # 设置窗口位置和大小

        # 创建布局
        layout = QVBoxLayout(self)

        # 创建列表框并添加列表项
        self.listWidget = QListWidget()
        for item in self.room_list:
            self.listWidget.addItem(item)
        layout.addWidget(self.listWidget)  # 将列表框添加到布局中
