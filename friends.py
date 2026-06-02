from supabase import create_client
import os
import sys
from dotenv import load_dotenv

load_dotenv()

client = None

async def start_friends_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    global client
    client = await create_client(url, key)

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path) 

async def get_friends():
    user_uuid = client.auth.get_user().user.id

    # Returns a list of length 2 with dictionaries of the uuid pairs of friendships of the current user
    friends = await client.from_('friendships'\
                            .select("uuid_pair")\
                            .contains("uuid_pair", [user_uuid])\
                            .eq("status", "accepted").execute()).get("data")

    # Returns a list of dictionaries of length 1 with the username of each friend in each dictionary
    friends_list = client.from_('user_information')\
                            .select("username")\
                            .contains("uuid", [friend['uuid_pair'][0] if friend['uuid_pair'][0] != user_uuid else friend['uuid_pair'][1] for friend in friends]) \
                            .execute().get("data")
    return friends_list

def get_uuid(addressee_username: str):
    # find uuid of that username
    addressee_uuid = client.from_("user_information")\
                            .select("user_id")\
                            .eq("username", addressee_username)\
                            .execute()\
                            .get("data")[0]["user_id"]
    return addressee_uuid

def send_friend_request(addressee_username: str):
    addressee_uuid = get_uuid(addressee_username)
    
    # set status of friendship to pending with the right uuid pair
    request_exists = client.from_("friendships").select("status")\
                            .contains("uuid_pair", [client.auth.get_user().user.id]) \
                            .contains("uuid_pair", [addressee_uuid]) \
                            .execute().get("data")
    
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