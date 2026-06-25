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
        return response_tasks.data, response_organization.data
            
    except Exception as e:      
        print("Error retrieving organization tasks for user")
        return {"message": f"An error occurred while retrieving organizations for user: {str(e)}"}
    
def invite_members_to_organization(organization_id: str, member_ids: list):
    """Invite members to an organization."""
    try:
        user_response = client.auth.get_user()
        user_id = user_response.user.id
        response = client.rpc("invite_members_to_organization", {"selected_organization_id": organization_id, "user_id": user_id, "members_to_invite": member_ids}).execute()
        return response
    except Exception as e:
        print("Error inviting members to organization")
        print(e)
        return {"message": f"An error occurred while inviting members to organization: {str(e)}"}
    
def retrieve_organization_invitations_for_user():
    try:
        user = client.auth.get_user()
        user_id = user.user.id

        response = client.from_("organization_invitations").select("*").eq("recipient_id", user_id).execute()

        organization_ids = [invitation["organization_id"] for invitation in response.data] if response.data else []
        organization_names = retrieve_organization_names_for_invitations(organization_ids)

        return response.data, organization_names
    except Exception as e:
        print("Error retrieving organization invitations for user:")
        print(e)
        return {"message": f"An error occurred while retrieving organization invitations for user: {str(e)}"}
    
def retrieve_organization_names_for_invitations(organization_ids: list):
    try:
        response = client.rpc("retrieve_organization_names_for_invitations", {"organization_ids": organization_ids}).execute()
        return response.data
    
    except Exception as e:
        print("Error retrieving organization names:")
        print(e)
        return {"message": f"An error occurred while retrieving organization names: {str(e)}"}
    
def accept_organization_invitation(organization_id: str):
    try:
        user = client.auth.get_user()
        user_id = user.user.id

        response = client.rpc("accept_organization_invitation", {"target_organization_id": organization_id, "user_id": user_id}).execute()

        return response.data[0] if response.data else []
    except Exception as e:
        print("Error accepting organization invitation:")
        print(e)
        return {"message": f"An error occurred while accepting organization invitation: {str(e)}"}
    
def decline_organization_invitation(organization_id: str):
    try:
        user = client.auth.get_user()
        user_id = user.user.id

        response = client.rpc("decline_organization_invitation", {"target_organization_id": organization_id, "user_id": user_id}).execute()

        return response.data[0] if response.data else []
    except Exception as e:
        print("Error declining organization invitation:")
        print(e)
        return {"message": f"An error occurred while declining organization invitation: {str(e)}"}