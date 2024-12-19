import asyncio
import threading

from PyQt5 import QtWidgets
from ChatRoomWindow import UI_ChatRoomWindow
from Remote_meeting_room import Ui_Remote_meeting_room
from WebRTC.client import client


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stackedWidget)
        self.network()

        # 创建主窗口UI
        self.mainWidget = QtWidgets.QWidget()
        self.ui = Ui_Remote_meeting_room()
        self.client.Ui_Remote_meeting_room=self.ui
        self.ui.setupUi(self.mainWidget,self)
        self.stackedWidget.addWidget(self.mainWidget)

        # 创建聊天室窗口UI
        self.chatRoomWidget = QtWidgets.QWidget()
        self.chatRoomUi = UI_ChatRoomWindow()
        self.client.UI_ChatRoomWindow=self.chatRoomUi
        self.chatRoomUi.setupUi(self.chatRoomWidget,self)
        self.stackedWidget.addWidget(self.chatRoomWidget)
    
    
    def showChatRoom(self):
        self.stackedWidget.setCurrentWidget(self.chatRoomWidget)




    def showMainWindow(self):
        self.stackedWidget.setCurrentWidget(self.mainWidget)

    def network(self):
        self.client = client()
        # 开启一个新的线程处理
        threading.Thread(target=self.client.run(), daemon=True).start()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())