import os
import chat
import chat
import friends
from fastapi import FastAPI, Form
from pydantic import BaseModel
from verification import login_user, register_user
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
friends.client = client
app = FastAPI()

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

@app.post("/api/dashboard")
def dashboard():
     friends_list = friends.get_friends()
     channel_list = chat.get_channels()
     return {"friends": friends_list, "channels": channel_list}
