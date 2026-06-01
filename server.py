from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from database import supabase

##############################################################################
# Setting up FastAPI Application
##############################################################################

api = FastAPI()

connected_users = {}

@api.websocket("/messages")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_users[websocket] = True
    try:
        while True:
            data = await websocket.receive_json()
            # Process the received data
            supabase.table("messages").insert({"sender": data["sender"],
                                               "content": data["content"],
                                               "created_at": data["created_at"],
                                               "receiver": data["receiver"]
            
            }).execute()

            recipient = supabase.table("user_information").select("user_id").eq("user_id", data["receiver"]).execute()
            if recipient:
                await recipient.send_json({
                    "from": data["sender"],
                    "content": data["content"],
                    "created_at": data["created_at"],
                    "receiver": data["receiver"]
                })

    except WebSocketDisconnect:
        del connected_users[websocket]