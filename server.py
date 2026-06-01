from fastapi import FastAPI
from database import supabase

##############################################################################
# Setting up FastAPI Application
##############################################################################

api = FastAPI()

@api.get("/messages")
def get_messages():
    response = supabase.table("messages").select("*").execute()
    return response.data