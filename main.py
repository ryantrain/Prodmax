import sys
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt5 import uic

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

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.chat_page)

        self.stack.setCurrentWidget(self.login_page)

    def switch_to_chat(self):
        self.stack.setCurrentWidget(self.chat_page)

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_page)

    def create_login_page(self):
        page = uic.loadUi("test.ui")
        layout = page.layout()
        label = QLabel("Login Page", self)
        label.setAttribute(self.underMouse(), True)
        layout.addWidget(label)
        page.button_1.clicked.connect(self.switch_to_chat)
        return page

    def create_chat_page(self):
        page = uic.loadUi("test.ui")
        layout = page.layout()
        label = QLabel("Chat Page", self)
        label.setAttribute(self.underMouse(), True)
        layout.addWidget(label)
        page.button_1.clicked.connect(self.switch_to_login)
        return page

app = QApplication(sys.argv)
window = Homepage()
window.show()
window.raise_()
window.activateWindow()
sys.argv=[]
sys.exit(app.exec_())