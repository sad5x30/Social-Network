from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from services.websocket_manager import connect, disconnect

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await connect(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnect(user_id)