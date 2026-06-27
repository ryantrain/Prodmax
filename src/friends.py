from supabase import Client
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone
import chat as chat

load_dotenv()

client : Client = None

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path) 

def get_friends() -> list:

    if client:

        user_uuid = client.auth.get_user().user.id
        if not user_uuid:
            raise RuntimeError("No authenticated user is available on the friends client")

        # Returns a dictionary with each key containing a list of length 2 uuid pairs

        friends_ids = client.from_('friendships')\
                                .select("uuid_pair")\
                                .contains("uuid_pair", [user_uuid])\
                                .eq("status", "accepted").execute().data
        
        if not friends_ids:
            return []

        # Returns a list of dictionaries of length 1 with the username of each friend in each dictionary                        
        friends_list = []
        friends_list_ids = []
        for row in friends_ids:
            uuid_pair = row.get("uuid_pair")

            uuid = uuid_pair[0] if uuid_pair[0] != user_uuid else uuid_pair[1]
            friends_list_ids.append(uuid)

            friend_username = get_username(uuid)
            
            friends_list.append(friend_username)

        return friends_list, friends_list_ids

    raise RuntimeError("client does not exist")

def get_uuid(addressee_username: str):
    # find uuid of that username
    addressee_uuid = client.from_("user_public_view")\
                            .select("user_id")\
                            .eq("username", addressee_username)\
                            .execute()\
                            .data[0]["user_id"]
    return addressee_uuid

def send_friend_request(addressee_username: str):
    try:
        addressee_uuid = get_uuid(addressee_username)
        
        # set status of friendship to pending with the right uuid pair
        request_exists = client.from_("friendships").select("status")\
                                .contains("uuid_pair", [client.auth.get_user().user.id]) \
                                .contains("uuid_pair", [addressee_uuid]) \
                                .execute().data

        if request_exists:
            raise ValueError("Friend request already exists")
        
        user_id = client.auth.get_user().user.id
        if addressee_uuid:
            response = client.from_("friendships")\
                    .insert({"uuid_pair": [user_id, addressee_uuid], "status": "pending", "sender_id": user_id})\
                    .execute()
        if response:
            return {"success": True, "data": response}
            
        else:
            # tell error that it failed
            raise ValueError("Friend request already exists or user not found")

    except Exception as e:
        raise ValueError(f"An error occurred while sending friend request: {str(e)}")

async def accept_friend_request(addressee_username: str):
    addressee_uuid = get_uuid(addressee_username)
    client.rpc("update_friendship_status_accepted", {"addressee_uuid": addressee_uuid, "new_status": "accepted"}).execute()
    await chat.add_channel_to_db(channel_type="private", channel_members=[addressee_uuid, client.auth.get_user().user.id], channel_name=None)
    channel_id = get_channel_id_with_friend_username(addressee_username)
    return {"channel_id": channel_id}

def decline_friend_request(addressee_uuid: str):
   
    client.rpc("decline_friend_request", {"addressee_uuid": addressee_uuid}).execute()
    
def get_username(uuid: str):
    if client:
        username = client.from_("user_public_view")\
                                .select("username")\
                                .eq("user_id", uuid)\
                                .execute().data[0]["username"]
        return username
    raise RuntimeError("client does not exist")

def get_channel_id_with_friend_username(friend_username: str):
    friend_uuid = get_uuid(friend_username)
    user_id = client.auth.get_user().user.id
    response = client.from_("channel_list").select("channel_id").eq("channel_type", "private").contains("channel_members", [user_id, friend_uuid]).execute().data
    if response:
        return response[0]["channel_id"]
    else:
        raise ValueError("No channel found for the given friend username.")

async def get_channel_members(channel_id: str):
    response = client.from_("channel_list").select("channel_members").eq("channel_id", channel_id).execute()
    try:
        names = [get_username(uuid) for uuid in response.data[0]["channel_members"]]
        return names
    except Exception:
        raise ValueError("No channel found for the given channel id.")

def get_friend_requests() -> list:
    user_id = client.auth.get_user().user.id
    response = client.from_("friendships").select("uuid_pair").contains("uuid_pair", [user_id]).eq("status", "pending").execute()
    friend_requests_names = []
    friend_requests_uuids = []
    for request in response.data:
        uuid_pair = request["uuid_pair"]
        friend_uuid = uuid_pair[0] if uuid_pair[0] != user_id else uuid_pair[1]
        friend_requests_uuids.append(friend_uuid)
        friend_username = get_username(friend_uuid)
        friend_requests_names.append(friend_username)
    return friend_requests_names, friend_requests_uuids