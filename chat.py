import asyncio
import sys
from PyQt5.QtCore import pyqtSignal, QObject
from dotenv import load_dotenv
import os
from supabase import create_async_client
from friends import get_username
from datetime import datetime, timezone
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
    """
    message_received = pyqtSignal(object)

signals = Signals()
client = None

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

    if isinstance(row, dict):
        sender = row.get("sender_user_id")
        content = row.get("content")
        channel_id = row.get("chat_id")
        
        if sender and content:
            sender = get_username(sender)
            return (f"{sender}: {content}", channel_id)

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

    global client
    client = await create_async_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    # Creates a client channel to listen for changes on the "public" schema and in the "messages" table
    channel = client.channel("public:messages")

    # Subscribe to changes, specifically, inserts, on the "messages" table in the "public" schema
    # Note: Whenever on_postgres_changes() is triggered, it will automatically call on_message() and pass
    # a payload object as an argument containing the information about the change occured in "messages"
    channel.on_postgres_changes("INSERT", on_message, table="messages", schema="public")
    await channel.subscribe()

    while True:
        await asyncio.sleep(60)

def load_messages(chat_id: str, client):
    """
    (A)Synchronous function that loads up to 10 messages in the
    message history from the table "messages" in the "public" schema.
    """

    response = client.from_("messages").select("content", "sender_user_id").eq("chat_id", chat_id).order("created_at", desc=True).limit(10).execute()
    messages = response.data if response.data else []
    formatted_messages = []
    for message in messages:
        sender_id = message.get("sender_user_id")
        response = client.from_("user_information").select("username").eq("user_id", sender_id).execute()
        sender_username = response.data[0]["username"]
        formatted_messages.append(f"{sender_username}: {message.get('content', '')}")
    return formatted_messages

def send_message_to_db(chat_id: str, sender_user_id: str, content: str, client):

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        client.from_("messages").insert({"chat_id": chat_id, "sender_user_id": sender_user_id, "content": content, "created_at": timestamp}).execute()
        return True
    except Exception as e:
        print(f"Error occurred while sending message: {e}")

async def load_channel_list():
    """
    Load existing list of channels in a user's channel list.
    Return a tuple of two lists: (list of channel ids, list of channel names)
    """
    user = await client.auth.get_user()
    user_id = user.user.id
    response = await client.from_("user_information").select("channel_list").eq("user_id", user_id).execute()
    channel_response = await client.from_("channel_list").select("channel_id", "channel_members", "channel_type", "channel_name")\
                    .contains("channel_members", [user_id]).execute()
    
    channel_list_ids = response.data[0]["channel_list"] if response.data and response.data[0] else []
    channel_list_names = []
    
    try:
        for channel_id in channel_list_ids:
            for row in channel_response.data:
                if row["channel_id"] == channel_id:
                    try:
                        if row["channel_type"] == "private":
                            friend_uuid = row["channel_members"][0]
                            if friend_uuid == user_id:
                                channel_list_names.append(friends.get_username(row["channel_members"][1]))
                            else:
                                channel_list_names.append(friends.get_username(row["channel_members"][0]))
                            
                            continue
                        else:
                            channel_list_names.append(row["channel_name"])
                            continue

                    except Exception:
                        raise ValueError("No channel found for the given channel id.")

        return channel_list_ids, channel_list_names
    
    except Exception:
        raise ValueError("Error loading channel list.")

def start_realtime():
    """
    Starts the asychronous event loop to listen for realtime changes in the Supabase database.
    Tracked databases are listed in the start_realtime_async function docstring.
    """
    asyncio.run(start_realtime_async())
