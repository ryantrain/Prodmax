import asyncio
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QTextEdit
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import uic
from dotenv import load_dotenv
import os
import threading
from supabase import create_client, create_async_client
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
    change_to_chat = pyqtSignal(str, str)

signals = Signals()


#####################################################################
# Loading pages + PyQt5 setup
#####################################################################
class Homepage(QMainWindow):

    login_page: QStackedWidget
    chat_page: QStackedWidget
    message_preview: QTextEdit

    def __init__(self, email, password):
        super().__init__()
        self.setWindowTitle('Prodmax')
        self.setGeometry(100, 100, 1200, 1000)

        self.chat_window = self.create_chat_page()
        self.setCentralWidget(self.chat_window)
        
        self.email = email
        self.password = password

        chat.signals.message_received.connect(self.update_message_preview)

    def initialize_friends_list(self):

        def update_friends_list(friends_list: list):
            self.friends_list.clear()
            for friend in friends_list:
                self.friends_list.addItem(str(friend))

        def run_get_friends():
            if not friends.client:
                friends.start_friends_client()

            friends_list = asyncio.run(friends.get_friends(self.email, self.password))
            if friends_list is not None:
                update_friends_list(friends_list)
        
        run_get_friends()

    def create_chat_page(self):
        page = uic.loadUi(resource_path("layouts/chat.ui"))
        self.message_preview = page.textEdit
        self.friends_list = page.friends_list
        self.message_preview.setPlainText("im poo")
        page.textEdit.setReadOnly(True)

        return page

    def update_message_preview(self, message):
        print(message)
        self.message_preview.setPlainText(message)


class LoginRegisterPage(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Prodmax')
        self.setGeometry(100, 100, 1200, 1000)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = self.create_login_page()
        self.register_page = self.create_register_page()

        self.stack.setCurrentWidget(self.login_page)

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_page)

    def switch_to_register(self):
        self.stack.setCurrentWidget(self.register_page)
    
    def switch_to_chat(self, email, password):
        self.chat_window = Homepage(email, password)
        self.setCentralWidget(self.chat_window)

    def create_login_page(self):
        page = uic.loadUi(resource_path("layouts/login.ui"))

        def handle_login():
            email = page.email_field.text()
            password = page.password_field.text()

            try:
                response = asyncio.run(verification.login_user(email, password))
                if response:
                    # friends.start_friends_client()
                    if response.session:
                        friends.client.auth.set_session(
                            response.session.access_token,
                            response.session.refresh_token,
                        )
                    # self.switch_to_chat(email, password)
                    signals.change_to_chat.emit(email, password)

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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Prodmax')
        self.setGeometry(100, 100, 1200, 1000)

        self.login_register_page = LoginRegisterPage()
        self.setCentralWidget(self.login_register_page)

        signals.change_to_chat.connect(self.handle_change_to_chat)

    def handle_change_to_chat(self, email, password):
        self.chat_window = Homepage(email, password)
        self.chat_window.initialize_friends_list()
        self.setCentralWidget(self.chat_window)

if __name__ == "__main__":

    # Initialize all the clients before starting and setting each client in all other files to the same client
    # to keep clients centralized and avoid multiple clients being created in different files.
    async_client = asyncio.run(create_async_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")))
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    friends.client = client
    verification.async_client = async_client
    chat.async_client = async_client
    
    thread = threading.Thread(target=chat.start_realtime, daemon=True)
    thread.start()
    
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())