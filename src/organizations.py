from datetime import datetime, timezone
from supabase import Client

client : Client = None

def add_organization(name, description="."):
    """Add an organization to the database."""
    try:
        user_id = client.auth.get_user().user.id
        response = client.rpc("add_organization", 
                {
                    "creation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "members": [user_id],
                    "owner": user_id,
                    "organization_name": name, 
                    "organization_description": description,
                }).execute()
        return response
    except Exception as e:      
        print("Error adding organization" + str(e))
        return {"message": f"An error occurred while adding organization to organizations: {str(e)}"} 

def delete_organization(organization_id: str, owner_id: str):
    """Delete an organization from the database."""
    try:
        response = client.rpc("delete_organization", {"organization_id": organization_id, "owner_id": owner_id}).execute()
        return response
    except Exception as e:      
        print("Error removing organization")
        return {"message": f"An error occurred while deleting organization from organizations: {str(e)}"} 

def retrieve_organizations_for_user():
    """Retrieve organizations for a specific user."""
    try:
        user_id = client.auth.get_user().user.id
        response = client.rpc("retrieve_organizations_for_user", {"user_id": user_id}).execute()
        if response.data:
            return response.data
        else:
            return []
    except Exception as e:      
        print("Error retrieving organizations for user")
        return {"message": f"An error occurred while retrieving organizations for user: {str(e)}"}
    
def retrieve_organization_tasks(organization_id):
    """Retrieve organization tasks."""
    try:
        response_tasks = client.from_("taskboards").select("*").eq("organization_id", organization_id).execute()
        response_organization = client.from_("organizations").select("*").eq("organization_id", organization_id).execute()
        if not response_tasks.data or not response_organization.data:
            return []
        return response_tasks.data, response_organization.data
            
    except Exception as e:      
        print("Error retrieving organization tasks for user")
        return {"message": f"An error occurred while retrieving organizations for user: {str(e)}"}