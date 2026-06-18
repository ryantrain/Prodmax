import asyncio
import sys
from dotenv import load_dotenv
import os
from supabase import create_async_client
from friends import get_username
from datetime import datetime, timezone
import friends as friends

# Load the environment variables from the .env file for Supabase configuration
load_dotenv()


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path) 

async def start_realtime_async():
    """
    Asynchronous function that connects to the Supabase realtime channel and listens for changes in the
    following channels:
        - "public:messages" for changes in the "messages" table in the "public" schema    
    """

    global client
    client = await create_async_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    while True:
        await asyncio.sleep(60)

async def load_messages(chat_id: str):
    """
    Asynchronous function that loads up to 10 messages in the
    message history from the table "messages" in the "public" schema.
    """

    response = await client.from_("messages").select("content", "sender_user_id").eq("chat_id", chat_id).order("created_at", desc=True).limit(10).execute()
    messages = response.data if response.data else []
    formatted_messages = []
    for message in messages:
        sender_id = message.get("sender_user_id")
        response = await client.from_("user_information").select("username").eq("user_id", sender_id).execute()
        sender_username = response.data[0]["username"]
        formatted_messages.append(f"{sender_username}: {message.get('content', '')}")
    return formatted_messages

async def send_message_to_db(chat_id: str, sender_user_id: str, content: str):

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        await client.from_("messages").insert({"chat_id": chat_id, "sender_user_id": sender_user_id, "content": content, "created_at": timestamp}).execute()
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

async def add_channel_to_db(channel_type: str, channel_members: list, channel_name: str = None):
    """
    Adds a channel to the "channel_list" table in the "public" schema in the Supabase database.
    The channel can be of type "private" or "group". If the channel is of type "private", then the channel name is not needed
    and will be set to None. If the channel is of type "group", then the channel name is needed.
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        response = await client.from_("channel_list").insert({"created_at": timestamp, "channel_members": channel_members, "channel_type": channel_type, "channel_name": channel_name}).execute()
            # Update each user's channel list to include the new channel
        channel_id = response.data[0]["channel_id"]
        for member in channel_members:
            user_response = await client.from_("user_information").select("channel_list").eq("user_id", member).execute()
            channel_list = user_response.data[0]["channel_list"] if user_response.data and user_response.data[0] else []
            channel_list.append(channel_id)
            await client.from_("user_information").update({"channel_list": channel_list}).eq("user_id", member).execute()

    except Exception as e:
        print(f"Error occurred while adding channel: {e}")
