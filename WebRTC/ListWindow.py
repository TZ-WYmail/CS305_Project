from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QDialog


class ListWindow(QDialog):

    def __init__(self,room_list,parent=None):
        super(ListWindow, self).__init__(parent)
        layout = QVBoxLayout()
        self.setWindowTitle('列表界面')
        self.setGeometry(100, 100, 300, 200)  # 设置窗口位置和大小

        # 这里可以添加列表内容，比如一个列表框
        self.listWidget = QListWidget()
        for item in self.room_list:
            self.listWidget.addItem(item.text())
            print(item)
        layout.addWidget(self.listWidget)

    def addItem(self):
        for item in self.room_list:
            self.listWidget.addItem(item.text())
            print(item)
