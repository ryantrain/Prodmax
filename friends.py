from supabase import Client
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

client : Client = None

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path) 

async def get_friends() -> list:

    if client:

        user_uuid = client.auth.get_user().user.id
        if not user_uuid:
            raise RuntimeError("No authenticated user is available on the friends client")
        
        # Returns a dictionary with each key containing a list of length 2 uuid pairs

        friends = client.from_('friendships')\
                                .select("uuid_pair")\
                                .contains("uuid_pair", [user_uuid])\
                                .eq("status", "accepted").execute().data
        
        if not friends:
            return []

        # Returns a list of dictionaries of length 1 with the username of each friend in each dictionary                        
        friends_list = []
        for row in friends:
            uuid_pair = row.get("uuid_pair")

            uuid = uuid_pair[0] if uuid_pair[0] != user_uuid else uuid_pair[1]

            friend_username = get_username(uuid)
            
            friends_list.append(friend_username)

        return friends_list

    raise RuntimeError("client does not exist")

def get_uuid(addressee_username: str):
    # find uuid of that username
    addressee_uuid = client.from_("user_information")\
                            .select("user_id")\
                            .eq("username", addressee_username)\
                            .execute()\
                            .data[0]["user_id"]
    return addressee_uuid

def send_friend_request(addressee_username: str):
    addressee_uuid = get_uuid(addressee_username)
    
    # set status of friendship to pending with the right uuid pair
    request_exists = client.from_("friendships").select("status")\
                            .contains("uuid_pair", [client.auth.get_user().user.id]) \
                            .contains("uuid_pair", [addressee_uuid]) \
                            .execute().data
    
    if addressee_uuid and not request_exists:
        client.from_("friendships")\
                .insert({"uuid_pair": [client.auth.get_user().user.id, addressee_uuid], "status": "pending"})\
                .execute()
    else:
        # tell error that it failed
        raise ValueError("Friend request already exists or user not found")

def accept_friend_request(addressee_username: str):
    addressee_uuid = get_uuid(addressee_username)
    
    client.from_("friendships").update({"status": "accepted"})\
            .contains("uuid_pair", [client.auth.get_user().user.id]) \
            .contains("uuid_pair", [addressee_uuid])\
            .execute()

def decline_friend_request(addressee_username: str):
    addressee_uuid = get_uuid(addressee_username)
    
    client.from_("friendships")\
            .delete()\
            .contains("uuid_pair", [client.auth.get_user().user.id]) \
            .contains("uuid_pair", [addressee_uuid])
    
def get_username(uuid: str):
    if client:
        username = client.from_("user_information")\
                                .select("username")\
                                .eq("user_id", uuid)\
                                .execute().data[0]["username"]
        return username
    raise RuntimeError("client does not exist")

def get_channel_id(friend_username: str):
    friend_uuid = get_uuid(friend_username)
    user_id = client.auth.get_user().user.id
    response = client.from_("channel_list").select("channel_id").eq("channel_type", "private").contains("channel_members", [user_id, friend_uuid]).execute().data
    if response:
        return response[0]["channel_id"]
    else:
        raise ValueError("No channel found for the given friend username.")

async def verify_channels():
    """
    Verifies that a channel exists for each friend in the user's friend list.
    If a channel does not exist between the user and a friend, then create a channel for the user and that friend.
    """
    friend_list = await get_friends()
    for friend in friend_list:
        try:
            get_channel_id(friend)
        except Exception as e:
            friend_uuid = get_uuid(friend)
            user_id = client.auth.get_user().user.id
            client.from_("channel_list").insert({"created_at": datetime.now(timezone.utc).isoformat(), "channel_members": [user_id, friend_uuid] }).execute()

def get_channel_members(channel_id: str):
    response = client.from_("channel_list").select("channel_members").eq("channel_id", channel_id).execute()
    try:
        names = [get_username(uuid) for uuid in response.data[0]["channel_members"]]
        return names
    except Exception:
        raise ValueError("No channel found for the given channel id.")
    
# def get_channel_members_without_self(channel_id: str):
#     user_id = client.auth.get_user().user.id
#     response = client.from_("channel_list").select("channel_members").eq("channel_id", channel_id).execute()
#     try:
#         names = [get_username(uuid) for uuid in response.data[0]["channel_members"] if user_id != uuid]
#         return names
#     except Exception:
#         raise ValueError("No channel found for the given channel id.")