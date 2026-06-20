import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, "../src"))
sys.path.append(src_path)
import threading
import chat as chat
import friends as friends
import tasks as tasks
import organizations as organizations
from fastapi import FastAPI, Form
from verification import login_user, register_user
from dotenv import load_dotenv
from supabase import create_client
import asyncio

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
friends.client = client
tasks.client = client
organizations.client = client
app = FastAPI()
threading.Thread(target=asyncio.run, args=(chat.start_realtime_async(),)).start()

@app.post("/api/login")
async def login(email: str = Form(...), password: str = Form(...)):
    try:
        response = await login_user(email, password)

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
     taskboards = tasks.get_personal_taskboards_for_user()
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
    
@app.post('/api/add_personal_taskboard')
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
    
@app.post('/api/taskboard/{taskboard_id}')
def get_taskboard(taskboard_id: str):
    try:
        task_list = tasks.retrieve_tasks_for_taskboard(taskboard_id)
        return {"tasks": task_list}
    
    except Exception as e:
        return {"message": f"An error occurred while retrieving tasks for taskboard: {str(e)}"}

@app.post('/api/user/{user_id}')
def get_user_info(user_id: str):
    try:
        response = friends.get_username(user_id)
        return {"username": response}
    except Exception as e:
        return {"message": f"An error occurred while retrieving user information: {str(e)}"}
    
@app.post('/api/taskboard/{taskboard_id}/add_personal_task')
def add_task_to_taskboard(taskboard_id: str, task_name: str = Form(...), task_description: str = Form(...)):
    try:
        response = tasks.add_task_to_private_taskboard(taskboard_id, task_name, task_description)
        print(response)
        return {"message": "Task added successfully", "data": response, "ok": True}
    except Exception as e:
        return {"message": f"An error occurred while adding task to taskboard: {str(e)}"}
    
@app.post('/api/taskboard/{taskboard_id}/edit_task/{task_id}')
def edit_task_in_taskboard(taskboard_id: str, task_id: str, task_name: str = Form(...), task_description: str = Form(...)):
    try:
        response = tasks.edit_task_in_taskboard(task_id, task_name, task_description)
        return {"message": "Task edited successfully", "data": response, "ok": True}
    except Exception as e:
        return {"message": f"An error occurred while editing task in taskboard: {str(e)}"}
    
@app.post('/api/taskboard/{taskboard_id}/delete_task/{task_id}')
def delete_task_from_taskboard(taskboard_id: str, task_id: str):
    try:
        tasks.delete_task_from_taskboard(taskboard_id, task_id)
        return {"message": "Task deleted successfully"}
    except Exception as e:
        return {"message": f"An error occurred while deleting task from taskboard: {str(e)}"}

<<<<<<< HEAD
@app.post('/api/organizations/add_organization')
def add_organization_to_database(organization_name: str = Form(...), organization_description: str = Form(...)):
    try:
        response = organizations.add_organization(organization_name, organization_description)
        return {"message": "Organization added successfully", "data": response, "ok": True}
    except Exception as e:
        return {"message": f"An error occurred while adding organization to taskboard: {str(e)}"}

@app.post('/api/organizations/{organization_id}/delete_organization/}')
def delete_organization_from_database(organization_id: str):
    try:
        tasks.delete_task_from_taskboard(organization_id)
        return {"message": "Organization deleted successfully"}
    except Exception as e:
        return {"message": f"An error occurred while deleting organization from taskboard: {str(e)}"}
=======
@app.post('/api/taskboard/{taskboard_id}/toggle_task_completed/{task_id}')
def toggle_task_completed(taskboard_id: str, task_id: str):
    try:
        tasks.toggle_task_completed(task_id)
        return {"message": "Task completion toggled"}
    except Exception as e:
        return {"message": f"An error occurred while toggling task completion: {str(e)}"}
>>>>>>> 9332314979eeea73d37de8e7c40d4feef435d7b1
