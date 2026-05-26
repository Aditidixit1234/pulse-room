from typing import Dict, Set
import socketio

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

# room_id -> set of socket IDs
room_connections: Dict[str, Set[str]] = {}

# socket_id -> user info
connected_users: Dict[str, dict] = {}

@sio.event
async def connect(sid, environ, auth):
    print(f"Client connected: {sid}")
    connected_users[sid] = {"sid": sid}

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    user = connected_users.pop(sid, {})
    room_id = user.get("room_id")
    if room_id and room_id in room_connections:
        room_connections[room_id].discard(sid)
        await sio.emit("user_left", {"userId": user.get("user_id")}, room=room_id)

@sio.event
async def join_room(sid, data):
    room_id = data.get("roomId")
    user_id = data.get("userId")
    user_name = data.get("userName", "Unknown")

    if room_id:
        sio.enter_room(sid, room_id)
        if room_id not in room_connections:
            room_connections[room_id] = set()
        room_connections[room_id].add(sid)
        connected_users[sid].update({
            "room_id": room_id,
            "user_id": user_id,
            "user_name": user_name
        })
        await sio.emit("user_joined", {
            "userId": user_id,
            "userName": user_name,
            "sid": sid
        }, room=room_id, skip_sid=sid)

@sio.event
async def leave_room(sid, data):
    room_id = data.get("roomId")
    if room_id:
        sio.leave_room(sid, room_id)
        if room_id in room_connections:
            room_connections[room_id].discard(sid)
        user = connected_users.get(sid, {})
        await sio.emit("user_left", {
            "userId": user.get("user_id")
        }, room=room_id)

@sio.event
async def task_created(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("task_created", data, room=room_id, skip_sid=sid)

@sio.event
async def task_updated(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("task_updated", data, room=room_id, skip_sid=sid)

@sio.event
async def task_deleted(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("task_deleted", data, room=room_id, skip_sid=sid)

@sio.event
async def user_typing(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("user_typing", data, room=room_id, skip_sid=sid)