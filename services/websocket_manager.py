connections = {}

async def connect(user_id, websocket):
    await websocket.accept()
    connections[user_id] = websocket

def disconnect(user_id):
    connections.pop(user_id, None)

async def send_message(user_id, data: dict):
    websocket = connections.get(user_id)
    if websocket:
        await websocket.send_json(data)