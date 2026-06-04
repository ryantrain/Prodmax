import asyncio
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QTextEdit
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import uic
from dotenv import load_dotenv
import os
import threading
import verification
import chat
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
    message_preview: QTextEdit

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
        chat.signals.message_received.connect(self.update_message_preview)
        # signals.status_received.connect(self.update_message_preview) prolly move to chat.py

    def switch_to_chat(self, email, password):
        self.stack.setCurrentWidget(self.chat_page)

        def update_friends_list(friends_list: list):
            self.friends_list.clear()
            for friend in friends_list:
                self.friends_list.addItem(str(friend))

        def run_get_friends():
            if not friends.client:
                friends.start_friends_client()

            friends_list = asyncio.run(friends.get_friends(email, password))
            if friends_list is not None:
                update_friends_list(friends_list)
        
        run_get_friends()

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
                if response:
                    friends.start_friends_client()
                    if response.session:
                        friends.client.auth.set_session(
                            response.session.access_token,
                            response.session.refresh_token,
                        )
                    self.switch_to_chat(email, password)

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
                if response:
                    self.switch_to_login()

            except RuntimeError as e:

                print("Registration failed:", e)

        page.register_button.clicked.connect(handle_register)
        self.stack.addWidget(page)
        return page

    def create_chat_page(self):
        page = uic.loadUi(resource_path("layouts/chat.ui"))
        self.message_preview = page.textEdit
        self.friends_list = page.friends_list
        self.message_preview.setPlainText("im poo")
        page.textEdit.setReadOnly(True)

        self.stack.addWidget(page)
        page.button_1.clicked.connect(self.switch_to_login)
        return page

    def update_message_preview(self, message):
        print(message)
        self.message_preview.setPlainText(message)

if __name__ == "__main__":
    thread = threading.Thread(target=chat.start_realtime, daemon=True)
    thread.start()
    
    app = QApplication([])
    window = Homepage()
    window.show()
    sys.exit(app.exec_())