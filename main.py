import asyncio
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QStackedWidget
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import uic
from dotenv import load_dotenv
import os
import threading
import verification
from chat import start_realtime
import friends

# Load the environment variables from the .env file for Supabase configuration
load_dotenv()

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path)


class Signals(QObject):
    """
    Defines custom signals for the application. These signals are used to communicate between
    the asynchronous Supabase realtime listener and the PyQt5 backend. 

    Instance attributes:
        - message_received: Signal emitted when a new message is received from the Supabase realtime channel. 
                            The signal carries the formatted message as a string.
        - status_received: Signal emitted when the status of the Supabase realtime connection changes. 
                        The signal carries the status message as a string.
    """
    message_received = pyqtSignal(str)
    status_received = pyqtSignal(str)

signals = Signals()
#####################################################################
# Loading pages + PyQt5 setup
#####################################################################
class Homepage(QMainWindow):

    login_page: QStackedWidget
    chat_page: QStackedWidget

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Prodmax')
        self.setGeometry(100, 100, 1200, 1000)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = self.create_login_page()
        self.chat_page = self.create_chat_page()
        self.register_page = self.create_register_page()

        self.stack.setCurrentWidget(self.login_page)
        # signals.message_received.connect(self.update_message_preview)
        # signals.status_received.connect(self.update_message_preview) prolly move to chat.py

    def switch_to_chat(self):
        self.stack.setCurrentWidget(self.chat_page)

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_page)

    def switch_to_register(self):
        self.stack.setCurrentWidget(self.register_page)

    def create_login_page(self):
        page = uic.loadUi(resource_path("layouts/login.ui"))

        def handle_login():
            email = page.email_field.text()
            password = page.password_field.text()

            try:
                response = asyncio.run(verification.login_user(email, password))
                self.switch_to_chat()

            except RuntimeError as e:

                print("Login failed:", e)

        page.login_button.clicked.connect(handle_login)
        page.register_button.clicked.connect(self.switch_to_register)
        self.stack.addWidget(page)
        return page
    
    def create_register_page(self):
        page = uic.loadUi(resource_path("layouts/register.ui"))

        def handle_register():
            email = page.email_field.text()
            password = page.password_field.text()
            username = page.username_field.text()
            phone_number = page.phone_number_field.text()

            try:

                response = asyncio.run(verification.register_user(email, password, username, phone_number))
                self.switch_to_login()

            except RuntimeError as e:

                print("Registration failed:", e)

        page.register_button.clicked.connect(handle_register)
        self.stack.addWidget(page)
        return page

    def create_chat_page(self):
        page = uic.loadUi(resource_path("layouts/chat.ui"))
        self.message_preview = QLabel("Waiting for Supabase updates...", page)
        self.message_preview.setGeometry(20, 220, 520, 30)
        page.button_1.clicked.connect(self.switch_to_login)
        self.stack.addWidget(page)
        return page

    def update_message_preview(self, message):
        self.message_preview.setText(message)

if __name__ == "__main__":
    thread = threading.Thread(target=start_realtime, daemon=True)
    thread.start()

    thread2 = threading.Thread(target=friends.start_friends_client, daemon=True)
    thread2.start()
    
    app = QApplication([])
    window = Homepage()
    window.show()
    sys.exit(app.exec_())