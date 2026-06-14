client = None

def add_taskboard_to_db(taskboard_name: str):
    try:
        user_id = client.auth.get_user().user.id
        client.from_("taskboards").insert({"taskboard_name": taskboard_name, "members": [user_id], "taskboard_owner": user_id}).execute()
    except Exception as e:
        print(f"An error occurred while adding taskboard: {str(e)}")

def get_taskboards_for_user():
    try:
        user_id = client.auth.get_user().user.id
        response = client.from_("taskboards").select("*").contains("members", [user_id]).execute()
        if response.data:
            return response.data
        else:
            return []
    except Exception as e:
        print(f"An error occurred while fetching taskboards: {str(e)}")
        return []