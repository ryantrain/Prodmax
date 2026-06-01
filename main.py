import asyncio
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QStackedWidget
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import uic
from supabase import create_async_client
from dotenv import load_dotenv
import os
import threading

# Load the environment variables from the .env file for Supabase configuration
load_dotenv()

class Signals(QObject):
    message_received = pyqtSignal(str)
    status_received = pyqtSignal(str)

signals = Signals()

def format_message(payload):
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    row = data.get("record") if isinstance(data, dict) else None
    event_type = data.get("type") if isinstance(data, dict) else None

    if isinstance(row, dict):
        sender = row.get("sender")
        content = row.get("content")
        if sender and content:
            return f"{sender}: {content}"
        return f"{event_type or 'CHANGE'}: {row}"

    old_row = data.get("old_record") if isinstance(data, dict) else None
    if isinstance(old_row, dict):
        return f"{event_type or 'CHANGE'}: {old_row}"

    return str(payload)


def on_message(payload):
    signals.message_received.emit(format_message(payload))


async def start_realtime_async():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")

    client = await create_async_client(supabase_url, supabase_key)
    channel = client.channel("public:messages")

    # Subscribe to changes, specifically, inserts, on the "messages" table in the "public" schema
    channel.on_postgres_changes("INSERT", on_message, table="messages", schema="public")
    await channel.subscribe()
    signals.status_received.emit("Connected to Supabase realtime")

    while True:
        await asyncio.sleep(60)


def start_realtime():
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
        self.setGeometry(100, 100, 800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = self.create_login_page()
        self.chat_page = self.create_chat_page()

        self.stack.setCurrentWidget(self.login_page)
        signals.message_received.connect(self.update_message_preview)
        signals.status_received.connect(self.update_message_preview)

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