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
    Return a tuple of three lists: (list of channel ids, list of channel names, list of channel privacy statuses)
    """
    user = await client.auth.get_user()
    user_id = user.user.id
    response = await client.from_("user_information").select("channel_list").eq("user_id", user_id).execute()
    channel_response = await client.from_("channel_list").select("channel_id", "channel_members", "channel_type", "channel_name")\
                    .contains("channel_members", [user_id]).execute()
    
    channel_list_ids = response.data[0]["channel_list"] if response.data and response.data[0] else []
    channel_list_names = []
    channel_privacy_status = []
    
    try:
        for channel_id in channel_list_ids:
            for row in channel_response.data:
                if row["channel_id"] == channel_id:
                    try:
                        channel_privacy_status.append(row["channel_type"])
                        if row["channel_name"] is None or row["channel_type"] == "private":
                            member_list = [friends.get_username(member) for member in row["channel_members"] if member != user_id]
                            channel_list_names.append(", ".join(member_list))
                            continue
                        else:
                            channel_list_names.append(row["channel_name"])
                            continue

                    except Exception:
                        raise ValueError("No channel found for the given channel id.")

        return channel_list_ids, channel_list_names, channel_privacy_status
    
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
        user = await client.auth.get_user()
        user_id = user.user.id
        timestamp = datetime.now(timezone.utc).isoformat()
        response = await client.from_("channel_list").insert({"created_at": timestamp, "channel_members": channel_members, "channel_type": channel_type, "channel_name": channel_name, "channel_owner": user_id}).execute()
        # Update each user's channel list to include the new channel
        channel_id = response.data[0]["channel_id"]
        for member in channel_members:
            try: 
                await client.rpc('add_to_user_channel_list', {"user_id_lookup": member, "channel_id": channel_id}).execute()
            
            except Exception as member_error:
            # Captures and logs if a specific user couldn't be added due to RLS/friendship rules
                print(f"Skipped updating channel list for member {member}: {member_error}")

        return {"channel_id": channel_id}

    except Exception as e:
        print(f"Error occurred while adding channel: {e}")

async def create_group_channel(channel_name: str = None, selected_friend_names: list = []):
    """
    Creates a group channel with the given channel name and list of selected friend names.
    The selected friend names are the list of friends that the user has selected to be added to the group channel.
    The function retrieves the members of each selected friend and adds them to the group channel.
    """
    try:
        user = await client.auth.get_user()
        channel_members_ids = [user.user.id]
        for friend_name in selected_friend_names:
            friend_uuid = friends.get_uuid(friend_name)
            channel_members_ids.append(friend_uuid)

        response = await add_channel_to_db("group", channel_members_ids, channel_name)
        
        return response

    except Exception as e:
        print(f"Error occurred while creating group channel: {e}")

async def verify_private_channels():
    """
    Verifies that a channel exists for each friend in the user's friend list.
    If a channel does not exist between the user and a friend, then create a channel for the user and that friend.
    """
    friend_list = friends.get_friends()[0]
    for friend in friend_list:
        try:
            friends.get_channel_id_with_friend_username(friend)
        except Exception as e:
            friend_uuid = friends.get_uuid(friend)
            user_id = client.auth.get_user().user.id
            await add_channel_to_db(channel_type="private", channel_members=[user_id, friend_uuid], channel_name=None)

async def verify_organization_channels():

    user = await client.auth.get_user()
    user_id = user.user.id

    response = await client.rpc("verify_organization_channels", {"user_id_lookup": user_id}).execute()
