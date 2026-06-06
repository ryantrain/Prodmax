import asyncio
import sys
from PyQt5.QtCore import pyqtSignal, QObject
from dotenv import load_dotenv
import os
from supabase import create_async_client
from friends import get_username

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
    """
    message_received = pyqtSignal(str)

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
        sender = row.get("sender_user_id")
        content = row.get("content")
        
        if sender and content:
            sender = get_username(sender)
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

    async_client = await create_async_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    # Creates a client channel to listen for changes on the "public" schema and in the "messages" table
    channel = async_client.channel("public:messages")

    # Subscribe to changes, specifically, inserts, on the "messages" table in the "public" schema
    # Note: Whenever on_postgres_changes() is triggered, it will automatically call on_message() and pass
    # a payload object as an argument containing the information about the change occured in "messages"
    channel.on_postgres_changes("INSERT", on_message, table="messages", schema="public")
    await channel.subscribe()

    while True:
        await asyncio.sleep(60)


def start_realtime():
    """
    Starts the asychronous event loop to listen for realtime changes in the Supabase database.
    Tracked databases are listed in the start_realtime_async function docstring.
    """
    asyncio.run(start_realtime_async())