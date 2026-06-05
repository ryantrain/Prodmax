from supabase import Client
import os
import sys
from dotenv import load_dotenv

load_dotenv()

client : Client = None

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base_path, relative_path) 

async def get_friends(email, password) -> list:

    if client:
        client.auth.sign_in_with_password({"email": email, "password": password})
        user_uuid = client.auth.get_user().user.id
        if not user_uuid:
            raise RuntimeError("No authenticated user is available on the friends client")
        
        # Returns a dictionary with each key containing a list of length 2 uuid pairs
        friends = client.from_('friendships')\
                                .select("uuid_pair")\
                                .contains("uuid_pair", [user_uuid])\
                                .eq("status", "accepted").execute().data[0]
        
        # Turns friends dictionairy into a list of uuid pairs
        result = list(friends.values())

        # Returns a list of dictionaries of length 1 with the username of each friend in each dictionary                        
        friends_list = []
        for friends in result:
            uuid = friends[0] if friends[0] != user_uuid else friends[1]

            friend_username = client.from_('user_information')\
                                    .select("username")\
                                    .eq("user_id", uuid) \
                                    .execute().data[0]["username"]
            
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
    username = client.from_("user_information")\
                            .select("username")\
                            .eq("user_id", uuid)\
                            .execute().data[0]["username"]
    return username