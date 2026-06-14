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
# Turn this into a 'POST' request later
@app.get("/api/dashboard")
async def dashboard():
     friends_list = await friends.get_friends()
     channel_list = await chat.load_channel_list()
     return {"friends": friends_list, "channels": channel_list}

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
    
@app.post('/api/get_taskboards')
def get_taskboards():
    try:
        taskboards = tasks.get_taskboards_for_user()
        return {"taskboards": taskboards}
    except Exception as e:
        return {"message": f"An error occurred while fetching taskboards: {str(e)}"}