client = None

def add_taskboard_to_db(taskboard_name: str):
    try:
        user_id = client.auth.get_user().user.id
        response = client.from_("taskboards").insert({"taskboard_name": taskboard_name, "members": [user_id], "taskboard_owner": user_id}).execute()
        return response
    
    except Exception as e:
        print(f"An error occurred while adding taskboard: {str(e)}")
        return {"message": f"An error occurred while adding taskboard: {str(e)}"}

def get_personal_taskboards_for_user():
    try:
        user_id = client.auth.get_user().user.id
        response = client.from_("taskboards").select("*").contains("members", [user_id]).eq("privacy", "private").execute()
        if response.data:
            return response.data
        else:
            return []
    except Exception as e:
        print(f"An error occurred while fetching taskboards: {str(e)}")
        return []

def get_shared_taskboards_for_user():
    try:
        user_id = client.auth.get_user().user.id
        response = client.from_("taskboards").select("*").contains("members", [user_id]).eq("privacy", "public").execute()
        if response.data:
            return response.data
        else:
            return []
    except Exception as e:
        print(f"An error occurred while fetching taskboards: {str(e)}")
        return []

def retrieve_tasks_for_taskboard(taskboard_id: str):
    try:
        print(taskboard_id)
        response = client.from_("tasks").select("*").eq("parent_taskboard", taskboard_id).execute()
        if response.data:
            return response.data
        else:
            return []
    except Exception as e:
        print(f"An error occurred while fetching tasks for taskboard: {str(e)}")
        return []
    
def add_task_to_private_taskboard(taskboard_id: str, task_name: str, task_description: str):
    try:
        response = client.from_("tasks").insert({"task_name": task_name, "task_description": task_description, "parent_taskboard": taskboard_id}).execute()
        task_id = response.data[0]["id"]
        client.rpc("insert_task_into_taskboard", {"taskboard_id": taskboard_id, "task_id": task_id}).execute()
        return None
    except Exception as e:
        print(f"An error occurred while adding task to private taskboard: {str(e)}")
        return None
    
def edit_task_in_taskboard(task_id: str, task_name: str, task_description: str):
    try:
        response = client.rpc("edit_task_in_taskboard", {"task_id": task_id, "task_name_new": task_name, "task_description_new": task_description}).execute()
        return response
    except Exception as e:
        print(f"An error occurred while editing task in taskboard: {str(e)}")
        return None
    
def delete_task_from_taskboard(taskboard_id: str, task_id: str):
    try:
        response = client.rpc("delete_task_from_taskboard", {"taskboard_id": taskboard_id, "task_id": task_id}).execute()
        return response
    except Exception as e:
        print(f"An error occurred while deleting task from taskboard: {str(e)}")
        return {"message": f"An error occurred while deleting task from taskboard: {str(e)}"} 
    
def toggle_task_completed(task_id: str):
    try:
        response = client.rpc("toggle_task_completion", {"task_id": task_id}).execute()
        return response
    except Exception as e:
        print(f"An error occurred while toggling task completion: {str(e)}")
        return {"message": f"An error occurred while toggling task completion: {str(e)}"}
