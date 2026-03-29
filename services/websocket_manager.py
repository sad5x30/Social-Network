import json
from collections import defaultdict

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(set)
        # chat_id -> {websocket, websocket}

    async def connect(self, chat_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[chat_id].add(websocket)

    def disconnect(self, chat_id: int, websocket: WebSocket):
        connections = self.active_connections.get(chat_id)
        if not connections:
            return

        connections.discard(websocket)

        if not connections:
            self.active_connections.pop(chat_id, None)

    async def send_to_chat(self, chat_id: int, message: str):
        stale_connections = []

        for connection in list(self.active_connections.get(chat_id, set())):
            if connection.client_state != WebSocketState.CONNECTED:
                stale_connections.append(connection)
                continue

            try:
                await connection.send_text(message)
            except (RuntimeError, WebSocketDisconnect):
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(chat_id, connection)

    async def send_json_to_chat(self, chat_id: int, payload: dict):
        await self.send_to_chat(chat_id, json.dumps(payload, ensure_ascii=False))


manager = ConnectionManager()
