import asyncio
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QStackedWidget
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import uic
from supabase import create_async_client
from dotenv import load_dotenv
import os
import threading
import verification

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

def format_message(payload):
    """
    Formats the message received from the payload object into a readable string format.
    The payload comes in the format:
        {
            "data": {}
        }
    where all the information can be accessed through the "data" key.
    The main information of interest comes from payload["data"]["record"] which contains the actual message 
    information such as sender, content, etc.
    """
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    row = data.get("record") if isinstance(data, dict) else None
    event_type = data.get("type") if isinstance(data, dict) else None

    if isinstance(row, dict):
        sender = row.get("sender")
        content = row.get("content")
        if sender and content:
            return f"{sender}: {content}"
        return f"{event_type or 'CHANGE'}: {row}"

    return str(payload)


def on_message(payload):
    """
    Callback function triggered when a message is received from the Supabase realtime channel.
    """
    signals.message_received.emit(format_message(payload))


async def start_realtime_async():
    """
    Asynchronous function that connects to the Supabase realtime channel and listens for changes in the
    following channels:
        - "public:messages" for changes in the "messages" table in the "public" schema    
    """

    # Using the dotenv library to retrieve url and keys from .env file to load Supabase information
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")

    # Waits for the connection to be established and creates the asynchronous client 
    # for Supabase using the url and key retrieved from the .env file
    client = await create_async_client(supabase_url, supabase_key)

    # Creates a client channel to listen for changes on the "public" schema and in the "messages" table
    channel = client.channel("public:messages")

    # Subscribe to changes, specifically, inserts, on the "messages" table in the "public" schema
    # Note: Whenever on_postgres_changes() is triggered, it will automatically call on_message() and pass
    # a payload object as an argument containing the information about the change occured in "messages"
    channel.on_postgres_changes("INSERT", on_message, table="messages", schema="public")
    await channel.subscribe()

    # Activates the signal object status_received and gives it the string value "Connected to Supabase realtime"
    # to indicate that the connection to the Supabase realtime channel has been established successfully since
    # the code has reached this point without the exception above being raised
    signals.status_received.emit("Connected to Supabase realtime")

    while True:
        await asyncio.sleep(60)


def start_realtime():
    """
    Starts the asychronous event loop to listen for realtime changes in the Supabase database.
    Tracked databases are listed in the start_realtime_async function docstring.
    """
    asyncio.run(start_realtime_async())

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
        signals.message_received.connect(self.update_message_preview)
        signals.status_received.connect(self.update_message_preview)

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
    
    app = QApplication([])
    window = Homepage()
    window.show()
    sys.exit(app.exec_())