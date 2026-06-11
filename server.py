import os
import threading
import chat
import chat
import friends
from fastapi import FastAPI, Form
from pydantic import BaseModel
from verification import login_user, register_user
from dotenv import load_dotenv
from supabase import create_client
import asyncio

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
friends.client = client
app = FastAPI()
threading.Thread(target=asyncio.run, args=(chat.start_realtime_async(),)).start()

class ProcessData(BaseModel):
    param1: str
    param2: int

@app.post("/api/run-logic")
async def run_logic(data: ProcessData):


    result = f"Received param1: {data.param1} and param2: {data.param2}"
    
    return {"message": result}

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
