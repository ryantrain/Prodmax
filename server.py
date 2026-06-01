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
            
    except WebSocketDisconnect:
        del connected_users[websocket]