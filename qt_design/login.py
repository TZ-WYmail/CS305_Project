from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_login_window(object):
    def setupUi(self, login_window):
        login_window.setObjectName("login_window")
        login_window.resize(463, 302)
        self.centralwidget = QtWidgets.QWidget(login_window)
        self.centralwidget.setObjectName("centralwidget")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(0, 0, 461, 301))
        self.widget.setStyleSheet("background-color: rgb(248, 255, 161);")
        self.widget.setObjectName("widget")
        self.input_password = QtWidgets.QLineEdit(self.widget)
        self.input_password.setGeometry(QtCore.QRect(170, 120, 113, 20))
        self.input_password.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.input_password.setObjectName("input_password")
        self.input_account = QtWidgets.QLineEdit(self.widget)
        self.input_account.setGeometry(QtCore.QRect(170, 90, 113, 20))
        self.input_account.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.input_account.setObjectName("input_account")
        self.btn_login = QtWidgets.QPushButton(self.widget)
        self.btn_login.setGeometry(QtCore.QRect(300, 180, 75, 23))
        self.btn_login.setStyleSheet("background-color: rgb(255, 197, 146);")
        self.btn_login.setObjectName("btn_login")
        login_window.setCentralWidget(self.centralwidget)

        self.retranslateUi(login_window)
        QtCore.QMetaObject.connectSlotsByName(login_window)

    def retranslateUi(self, login_window):
        _translate = QtCore.QCoreApplication.translate
        login_window.setWindowTitle(_translate("login_window", "BB - 今天你BB了吗"))
        self.btn_login.setText(_translate("login_window", "登录"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    login_window = QtWidgets.QMainWindow()
    ui = Ui_login_window()
    ui.setupUi(login_window)
    login_window.show()
    sys.exit(app.exec_())
