from datetime import datetime, timezone

client = None

def add_organization(name, description="."):
    """Add an organization to the database."""
    try:
        user_id = client.get_user_id().user.id
        response = client.rpc("add_organization", 
                        {
                            "creation_timestamp": datetime.now(timezone.utc).isoformat(),
                            "organization_name": name, 
                            "organization_description": description,
                            "members": [user_id],
                            "owner": user_id
                        })
        return response
    except Exception as e:      
        print("Error adding organization" + str(e))
        return {"message": f"An error occurred while adding organization to organizations: {str(e)}"} 


def delete_organization(organization_id: str):
    """Delete an organization from the database."""
    try:
        response = client.rpc("delete_organization", {"organization_id": organization_id}).execute()
        return response
    except Exception as e:      
        print("Error removing organization")
        return {"message": f"An error occurred while deleting organization from organizations: {str(e)}"} 
