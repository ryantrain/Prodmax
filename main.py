import asyncio
import sys
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QMainWindow, QStackedWidget, QTextEdit, QVBoxLayout, QWidget, QLineEdit, QListWidgetItem
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
        - status_received: Signal emitted when the status of the Supabase realtime connection changes. 
                        The signal carries the status message as a string.
    """
    change_to_chat = pyqtSignal()

signals = Signals()


#####################################################################
# Loading pages + PyQt5 setup
#####################################################################
class Homepage(QMainWindow):

    chat_page: QStackedWidget
    message_preview: QTextEdit

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Prodmax')
        self.setGeometry(100, 100, 1200, 1000)

        self.chat_window = self.create_chat_page()
        self.setCentralWidget(self.chat_window)

        chat.signals.message_received.connect(self.add_message)

    @asyncSlot()
    async def initialize_friends_list(self):

        def update_friends_list(friends_list: list):
            self.friends_list.clear()
            for friend in friends_list:
                item = QListWidgetItem(str(friend))
                item.setData(Qt.UserRole, friends.get_channel_id(friend))
                self.friends_list.addItem(item)

        async def run_get_friends():
            if not friends.client:
                friends.start_friends_client()
            
            await friends.verify_channels()
            
            friends_list = await (friends.get_friends())
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
        self.current_channel_id = None
       
        self.messages_window.hide()
        self.message_input_field.hide()
        self.profile_container.layout().setContentsMargins(0, 0, 0, 0)
        self.message_preview.setPlainText("im poo")

        page.friends_list.itemClicked.connect(self.select_profile_pane)
        page.friends_list.itemClicked.connect(lambda item: self.show_messages_window(item))
        page.message_input_field.returnPressed.connect(self.send_message)
        page.textEdit.setReadOnly(True)

        return page

    def add_message(self, message):
        if self.current_channel_id and message[1] == self.current_channel_id:
            self.messages_window.addItem(message[0])

        else:
            for index in range(self.friends_list.count()):
                item = self.friends_list.item(index)
                if item.data(Qt.UserRole) == message[1]:
                    item.setText(item.text() + " (new)")
                    self.friends_list.update()
                    break

    def send_message(self, *args):
        message = self.message_input_field.text()
        channel_id = self.current_channel_id
        self.message_input_field.clear()
        chat.send_message_to_db(channel_id, client.auth.get_user().user.id, message, client)
       
    def select_profile_pane(self, item):

        # Removes the "new" notification text
        self.friends_list.currentItem().setText(self.friends_list.currentItem().text().replace(" (new)", ""))

        while self.profile_container.layout().count():
            child = self.profile_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        item.setText(item.text().replace(" (new)", ""))
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

    def show_messages_window(self, item):
        channel_id = item.data(Qt.UserRole)
        self.current_channel_id = channel_id
        self.messages_window.clear()
        messages = chat.load_messages(channel_id, client)
        self.messages_window.addItems(reversed(messages))
        self.messages_window.show()
        self.message_input_field.show()

    def close_messages_window(self):
        self.messages_window.hide()
        self.message_input_field.hide()
        self.current_channel_id = None


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
                
                # Sets other clients to also be logged in as well with the same session 
                # to keep clients centralized and avoid multiple clients being created in different files.
                if response and response.session:
                    access_token = response.session.access_token
                    refresh_token = response.session.refresh_token
                    client.auth.set_session(access_token, refresh_token)
                    if getattr(chat, "client", None):
                        await chat.client.auth.set_session(access_token, refresh_token)

                page.email_field.clear()
                page.password_field.clear()
                signals.change_to_chat.emit()

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
        self.center_on_screen()

        signals.change_to_chat.connect(self.handle_change_to_chat)

    def handle_change_to_chat(self):
        self.chat_window = Homepage()
        self.chat_window.initialize_friends_list()
        self.setCentralWidget(self.chat_window)

    def center_on_screen(self):
        window_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        window_geometry.moveCenter(screen_center)
        self.move(window_geometry.topLeft())

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