import sys
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5 import uic
import requests

class Homepage(QMainWindow):

    login_page: QStackedWidget
    chat_page: QStackedWidget

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Prodmax')
        self.setGeometry(100, 100, 800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = self.create_login_page()
        self.chat_page = self.create_chat_page()

        self.stack.setCurrentWidget(self.login_page)

    def switch_to_chat(self):
        self.stack.setCurrentWidget(self.chat_page)

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_page)

    def create_login_page(self):
        page = uic.loadUi("login.ui")
        page.button_1.clicked.connect(self.switch_to_chat)
        self.stack.addWidget(page)
        return page

    def create_chat_page(self):
        page = uic.loadUi("chat.ui")
        page.button_1.clicked.connect(self.switch_to_login)
        self.stack.addWidget(page)
        return page

app = QApplication([])
window = Homepage()
window.show()
sys.exit(app.exec_())