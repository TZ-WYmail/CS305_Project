import sys

from PyQt5.QtWidgets import QMainWindow, QApplication


class FirstWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("First Window")
        self.setGeometry(100, 100, 280, 80)
        self.show()


class SecondWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Second Window")
        self.setGeometry(500, 500, 280, 80)
        self.show()


def main():
    app = QApplication(sys.argv)

    # 创建并显示第一个窗口
    window1 = FirstWindow()

    # 创建并显示第二个窗口
    window2 = SecondWindow()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()