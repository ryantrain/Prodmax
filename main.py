import asyncio
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QTextEdit, QVBoxLayout, QWidget, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5 import uic
from dotenv import load_dotenv
import os
import threading
from supabase import create_client
import verification
import chat
import friends
from qasync import QEventLoop, asyncSlot

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

        chat.signals.message_received.connect(self.add_message)

    @asyncSlot()
    async def initialize_friends_list(self):

        def update_friends_list(friends_list: list):
            self.friends_list.clear()
            for friend in friends_list:
                self.friends_list.addItem(str(friend))

        async def run_get_friends():
            if not friends.client:
                friends.start_friends_client()

            friends_list = await (friends.get_friends(self.email, self.password))
            if friends_list is not None:
                update_friends_list(friends_list)
        
        await run_get_friends()

    def create_chat_page(self):

        page = uic.loadUi(resource_path("layouts/chat.ui"))
        self.message_preview = page.textEdit
        self.friends_list = page.friends_list
        self.profile_container = page.profile_container
        self.profile_layout = QVBoxLayout(self.profile_container)
        self.messages_window = page.chat_window
        self.message_input_field = page.message_input_field
       
        self.messages_window.hide()
        self.message_input_field.hide()
        self.profile_container.layout().setContentsMargins(0, 0, 0, 0)
        self.message_preview.setPlainText("im poo")

        page.friends_list.itemClicked.connect(self.select_profile_pane)
        page.friends_list.itemClicked.connect(self.show_messages_window)
        page.message_input_field.returnPressed.connect(self.send_message)
        page.textEdit.setReadOnly(True)

        return page

    def add_message(self, message):
        self.messages_window.addItem(message)

    @asyncSlot()
    async def send_message(self):
        message = self.message_input_field.text()
        self.message_input_field.clear()
        await chat.send_message_to_db("9e5628ee-877d-40d8-8b4f-382a409546ae", friends.client.auth.get_user().user.id, message)
       
    def select_profile_pane(self, item):

        while self.profile_container.layout().count():
            child = self.profile_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        profile_pane = ProfilePane(item)
        self.profile_container.layout().addWidget(profile_pane)
        self.profile_container.show()        

    def close_profile_pane(self):

        if self.profile_container.layout():
            while self.profile_container.layout().count():
                self.profile_container.layout().takeAt(0)
                self.profile_container.hide()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if event.button() == Qt.LeftButton:

            if not self.profile_container.geometry().contains(event.pos()) or not self.messages_window.geometry().contains(event.pos()):
                self.close_profile_pane()
                self.close_messages_window()

    @asyncSlot()
    async def show_messages_window(self, *args):
        self.messages_window.clear()
        messages = await chat.load_messages("9e5628ee-877d-40d8-8b4f-382a409546ae")
        self.messages_window.addItems(reversed(messages))
        self.messages_window.show()
        self.message_input_field.show()

    def close_messages_window(self):
        self.messages_window.hide()
        self.message_input_field.hide()


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
        [widget.clear() for widget in self.register_page.findChildren(QLineEdit)]

    def switch_to_register(self):
        self.stack.setCurrentWidget(self.register_page)
        [widget.clear() for widget in self.login_page.findChildren(QLineEdit)]
    
    def switch_to_chat(self, email, password):
        self.chat_window = Homepage(email, password)
        self.setCentralWidget(self.chat_window)

        asyncio.ensure_future(self.chat_window.initialize_friends_list())
    
    def create_login_page(self):
        page = uic.loadUi(resource_path("layouts/login.ui"))

        @asyncSlot()
        async def handle_login(*args):
            email = page.email_field.text()
            password = page.password_field.text()

            try:
                response = await verification.login_user(email, password)
                page.email_field.clear()
                page.password_field.clear()

                if response:
                    if response.session:
                        friends.client.auth.set_session(
                            response.session.access_token,
                            response.session.refresh_token,
                        )
                    signals.change_to_chat.emit(email, password)


            except RuntimeError as e:

                print("Login failed:", e)

        page.login_button.clicked.connect(handle_login)
        page.register_button.clicked.connect(self.switch_to_register)
        self.stack.addWidget(page)
        return page
    
    def create_register_page(self):
        page = uic.loadUi(resource_path("layouts/register.ui"))

        @asyncSlot()
        async def handle_register(*args):
            email = page.email_field.text()
            password = page.password_field.text()
            username = page.username_field.text()
            phone_number = page.phone_number_field.text()
        
            try:
                response = await verification.register_user(email, password, username, phone_number)
                if response:
                    page.email_field.clear()
                    page.password_field.clear()
                    page.username_field.clear()
                    page.phone_number_field.clear()
                    self.switch_to_login()

            except RuntimeError as e:
                print("Registration failed:", e)

        page.register_button.clicked.connect(handle_register)
        page.previous_button.clicked.connect(self.switch_to_login)
        self.stack.addWidget(page)
        return page
    
    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.stack.currentWidget() == self.login_page:

                if self.login_page.email_field.hasFocus() or self.login_page.password_field.hasFocus() or self.login_page.login_button.hasFocus():
                    self.login_page.login_button.click()
                elif self.login_page.register_button.hasFocus():
                    self.login_page.register_button.click()

            elif self.stack.currentWidget() == self.register_page and (self.register_page.email_field.hasFocus() or self.register_page.password_field.hasFocus() or self.register_page.username_field.hasFocus() or self.register_page.phone_number_field.hasFocus() or self.register_page.register_button.hasFocus()):
                self.register_page.register_button.click()


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

class ProfilePane(QWidget):

    def __init__(self, name):
        super().__init__()

        self.name = name.text()
        self.show_profile()

    def show_profile(self):
        self.pane = uic.loadUi(resource_path("layouts/profile_pane.ui"))
        self.pane.profile_name.setText(self.name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pane)
        self.setLayout(layout)


if __name__ == "__main__":

    # Initialize all the clients before starting and setting each client in all other files to the same client
    # to keep clients centralized and avoid multiple clients being created in different files.
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    friends.client = client

    thread = threading.Thread(target=chat.start_realtime, daemon=True)
    thread.start()
    
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    
    with loop:
        loop.run_forever()