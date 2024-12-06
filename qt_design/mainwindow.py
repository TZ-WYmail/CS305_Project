from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QPushButton


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 639)


        #消息输入
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText('输入消息')
        self.send_button = QPushButton('发送')
        self.send_button.clicked.connect(self.send_message)
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)


        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(0, 0, 181, 591))
        self.widget.setStyleSheet("background-color: rgb(128, 194, 255);")
        self.widget.setObjectName("widget")

        self.listWidget = QtWidgets.QListWidget(self.widget)
        self.listWidget.setGeometry(QtCore.QRect(10, 20, 151, 551))
        self.listWidget.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.listWidget.setObjectName("listWidget")
        item = QtWidgets.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.listWidget.addItem(item)

        self.widget_chatlog = QtWidgets.QWidget(self.centralwidget)
        self.widget_chatlog.setGeometry(QtCore.QRect(200, 40, 651, 371))
        self.widget_chatlog.setStyleSheet("background-color: rgb(225, 225, 225);\n"
"font: 14pt \"Forte\";")
        self.widget_chatlog.setObjectName("widget_chatlog")

        self.widget_chatlog_2 = QtWidgets.QWidget(self.centralwidget)
        self.widget_chatlog_2.setGeometry(QtCore.QRect(200, 420, 651, 171))
        self.widget_chatlog_2.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.widget_chatlog_2.setObjectName("widget_chatlog_2")

        self.input_space = QtWidgets.QPushButton(self.widget_chatlog_2)
        self.input_space.setGeometry(QtCore.QRect(270, 130, 101, 23))
        self.input_space.setStyleSheet("background-color: rgb(255, 250, 169);")
        self.input_space.setObjectName("input_space")

        self.btn_send = QtWidgets.QPushButton(self.widget_chatlog_2)
        self.btn_send.setGeometry(QtCore.QRect(540, 120, 91, 31))
        self.btn_send.setStyleSheet("background-color: rgb(8, 156, 255);\n"
"color: rgb(255, 255, 255);\n"
"text-align:center;")
        self.btn_send.setObjectName("btn_send")

        self.input_box = QtWidgets.QTextEdit(self.widget_chatlog_2)
        self.input_box.setEnabled(False)
        self.input_box.setGeometry(QtCore.QRect(20, 10, 611, 91))
        self.input_box.setStyleSheet("background-color: rgb(255, 255, 255);\n"
"color: rgb(0, 0, 0);\n"
"font: 14pt \"Forte\";")
        self.input_box.setObjectName("input_box")

        self.label_connect_status = QtWidgets.QLabel(self.centralwidget)
        self.label_connect_status.setGeometry(QtCore.QRect(780, 6, 71, 20))
        self.label_connect_status.setStyleSheet("background-color: rgb(255, 0, 4);\n"
"color: rgb(255, 255, 255);")
        self.label_connect_status.setObjectName("label_connect_status")

        self.widget_2 = QtWidgets.QWidget(self.centralwidget)
        self.widget_2.setGeometry(QtCore.QRect(860, 10, 241, 231))
        self.widget_2.setStyleSheet("background-color: rgb(180, 180, 180);")
        self.widget_2.setObjectName("widget_2")

        self.widget_users = QtWidgets.QWidget(self.centralwidget)
        self.widget_users.setGeometry(QtCore.QRect(860, 250, 241, 341))
        self.widget_users.setStyleSheet("background-color: rgb(128, 194, 255);")
        self.widget_users.setObjectName("widget_users")

        self.listWidget_3 = QtWidgets.QListWidget(self.widget_users)
        self.listWidget_3.setGeometry(QtCore.QRect(10, 40, 221, 291))
        self.listWidget_3.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.listWidget_3.setObjectName("listWidget_3")

        self.label = QtWidgets.QLabel(self.widget_users)
        self.label.setGeometry(QtCore.QRect(20, 10, 201, 21))
        self.label.setStyleSheet("background-color: rgb(139, 155, 255);")
        self.label.setObjectName("label")

        self.btn_voip = QtWidgets.QPushButton(self.centralwidget)
        self.btn_voip.setEnabled(False)
        self.btn_voip.setGeometry(QtCore.QRect(1190, 190, 71, 21))
        self.btn_voip.setStyleSheet("background-color: rgb(124, 255, 150);\n"
"color: rgb(255, 255, 255);")
        self.btn_voip.setObjectName("btn_voip")
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1100, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "XX 聊天室"))
        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        item = self.listWidget.item(0)
        item.setText(_translate("MainWindow", "BB-1"))
        item = self.listWidget.item(1)
        item.setText(_translate("MainWindow", "BB-2"))
        self.listWidget.setSortingEnabled(__sortingEnabled)
        self.input_space.setText(_translate("MainWindow", "输入（空格）"))
        self.btn_send.setText(_translate("MainWindow", "发送（回车）"))
        self.label_connect_status.setText(_translate("MainWindow", "  离线"))
        self.label.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">频道成员</p></body></html>"))
        self.btn_voip.setText(_translate("MainWindow", "📞"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())