import os
import threading
import chat
import friends
import tasks
from fastapi import FastAPI, Form
from pydantic import BaseModel
from verification import login_user, register_user
from dotenv import load_dotenv
from supabase import create_client
import asyncio

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
friends.client = client
tasks.client = client
app = FastAPI()
threading.Thread(target=asyncio.run, args=(chat.start_realtime_async(),)).start()

@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        response = await login_user(username, password)

        if response:
            access_token = response.session.access_token
            refresh_token = response.session.refresh_token
            client.auth.set_session(access_token, refresh_token)
            if getattr(chat, "client", None):
                    await chat.client.auth.set_session(access_token, refresh_token)

        return {"message": "Login successful", "data": response}
    
    except RuntimeError as e:
        return {"message": str(e)}

@app.post("/api/dashboard")
async def dashboard():
     taskboards = tasks.get_taskboards_for_user()
     return {"taskboards": taskboards}

@app.post('/api/navbar')
async def navbar():
    friends_list = friends.get_friends()
    channel_list = await chat.load_channel_list()
    friend_requests = friends.get_friend_requests()
    return {"friends": friends_list, "channels": channel_list, "friend_requests": friend_requests}

@app.post('/api/register')
async def register(username: str = Form(...), password: str = Form(...), email: str = Form(...), phone_number: str = Form(None)):
    try:
        response = await register_user(email, password, username, phone_number)
        if response:
            return {"message": "Registration successful", "data": response}
        else:
            return {"message": "Registration failed"}
    except Exception:
        return {"message": "An error occurred during registration"}
    
@app.post('/api/load_messages/{channel_id}')
async def load_messages(channel_id: str):
    channel_id = str(channel_id)
    try:
        messages = await chat.load_messages(channel_id)
        return {"messages": messages}
    except Exception as e:
        return {"message": f"An error occurred while loading messages: {str(e)}"}

@app.post('/api/send_message')
async def send_message(channel_id: str = Form(...), content: str = Form(...)):
    user = client.auth.get_user()
    sender_user_id = user.user.id
    try:
        response = await chat.send_message_to_db(channel_id, sender_user_id, content)
        username = friends.get_username(sender_user_id)

        return {"message": f"{username}: {content}", "data": response}
    except Exception as e:
        return {"message": f"An error occurred while sending message: {str(e)}"}
    
@app.post('/api/add_taskboard')
def add_taskboard(taskboard_name: str = Form(...)):
    try:
        tasks.add_taskboard_to_db(taskboard_name)
    except Exception as e:
        return f"An error occured while adding taskboard:{str(e)}"
    
@app.post('/api/add_friend')
def add_friend(query: str = Form(...)):
    try:
        response = friends.send_friend_request(query)

        if response['success']:
            return True
        else:
            raise ValueError("Failed to send friend request.")
    except Exception as e:
        return {"message": f"An error occurred while sending friend request: {str(e)}"}
    
@app.post('/api/accept_friend_request')
async def accept_friend_request(addressee_username: str = Form(...)):
    try:
        response = await friends.accept_friend_request(addressee_username)
        return {"message": "Friend request accepted", "data": response}
    except Exception as e:
        return {"message": f"An error occurred while accepting friend request: {str(e)}"}
    
@app.post('/api/decline_friend_request')
def decline_friend_request(addressee_username: str = Form(...)):
    try:
        friends.decline_friend_request(addressee_username)
        return {"message": "Friend request declined"}
    except Exception as e:
        return {"message": f"An error occurred while declining friend request: {str(e)}"}

