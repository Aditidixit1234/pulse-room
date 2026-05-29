from typing import Dict, Set
import socketio
import json

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

# room_id -> set of socket IDs
room_connections: Dict[str, Set[str]] = {}

# socket_id -> user info
connected_users: Dict[str, dict] = {}

# room_id -> list of online users
room_presence: Dict[str, Dict[str, dict]] = {}

@sio.event
async def connect(sid, environ, auth):
    print(f"Client connected: {sid}")
    connected_users[sid] = {"sid": sid}

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    user = connected_users.pop(sid, {})
    room_id = user.get("room_id")

    if room_id:
        # Remove from room connections
        if room_id in room_connections:
            room_connections[room_id].discard(sid)

        # Remove from presence
        user_id = user.get("user_id")
        if room_id in room_presence and user_id:
            room_presence[room_id].pop(user_id, None)

        # Broadcast updated presence
        await broadcast_presence(room_id)

        # Notify room user left
        await sio.emit("user_left", {
            "userId": user.get("user_id"),
            "userName": user.get("user_name"),
        }, room=room_id)

async def broadcast_presence(room_id: str):
    users = list(room_presence.get(room_id, {}).values())
    await sio.emit("presence_update", {
        "roomId": room_id,
        "users": users,
        "count": len(users),
    }, room=room_id)

@sio.event
async def join_room(sid, data):
    room_id = data.get("roomId")
    user_id = data.get("userId")
    user_name = data.get("userName", "Unknown")
    user_initials = data.get("userInitials", "U")
    user_role = data.get("userRole", "member")

    if not room_id:
        return

    sio.enter_room(sid, room_id)

    if room_id not in room_connections:
        room_connections[room_id] = set()
    room_connections[room_id].add(sid)

    connected_users[sid].update({
        "room_id": room_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_initials": user_initials,
    })

    # Add to presence
    if room_id not in room_presence:
        room_presence[room_id] = {}

    room_presence[room_id][user_id] = {
        "userId": user_id,
        "userName": user_name,
        "userInitials": user_initials,
        "userRole": user_role,
        "status": "online",
        "activity": "Viewing room",
        "sid": sid,
    }

    # Send current presence to new user
    await sio.emit("presence_update", {
        "roomId": room_id,
        "users": list(room_presence[room_id].values()),
        "count": len(room_presence[room_id]),
    }, to=sid)

    # Broadcast to room that user joined
    await sio.emit("user_joined", {
        "userId": user_id,
        "userName": user_name,
        "userInitials": user_initials,
        "userRole": user_role,
        "status": "online",
    }, room=room_id, skip_sid=sid)

    # Broadcast updated presence
    await broadcast_presence(room_id)

@sio.event
async def leave_room(sid, data):
    room_id = data.get("roomId")
    if not room_id:
        return

    sio.leave_room(sid, room_id)

    if room_id in room_connections:
        room_connections[room_id].discard(sid)

    user = connected_users.get(sid, {})
    user_id = user.get("user_id")

    if room_id in room_presence and user_id:
        room_presence[room_id].pop(user_id, None)

    await broadcast_presence(room_id)
    await sio.emit("user_left", {
        "userId": user_id,
        "userName": user.get("user_name"),
    }, room=room_id)

@sio.event
async def user_activity(sid, data):
    room_id = data.get("roomId")
    activity = data.get("activity", "")
    user = connected_users.get(sid, {})
    user_id = user.get("user_id")

    if room_id and user_id and room_id in room_presence:
        if user_id in room_presence[room_id]:
            room_presence[room_id][user_id]["activity"] = activity
        await broadcast_presence(room_id)

@sio.event
async def user_typing(sid, data):
    room_id = data.get("roomId")
    is_typing = data.get("isTyping", False)
    user = connected_users.get(sid, {})
    user_id = user.get("user_id")
    user_name = user.get("user_name", "Someone")

    if room_id and user_id and room_id in room_presence:
        if user_id in room_presence[room_id]:
            room_presence[room_id][user_id]["activity"] = "Typing…" if is_typing else "Viewing room"
            room_presence[room_id][user_id]["isTyping"] = is_typing

    await sio.emit("user_typing", {
        "userId": user_id,
        "userName": user_name,
        "isTyping": is_typing,
        "roomId": room_id,
    }, room=room_id, skip_sid=sid)

    if room_id:
        await broadcast_presence(room_id)

@sio.event
async def task_created(sid, data):
    room_id = data.get("roomId")
    user = connected_users.get(sid, {})
    user_id = user.get("user_id")
    user_name = user.get("user_name")

    if room_id and user_id and room_id in room_presence:
        if user_id in room_presence[room_id]:
            room_presence[room_id][user_id]["activity"] = "Created a task"

    if room_id:
        await sio.emit("task_created", data, room=room_id, skip_sid=sid)
        await broadcast_presence(room_id)

@sio.event
async def task_updated(sid, data):
    room_id = data.get("roomId")
    user = connected_users.get(sid, {})
    user_id = user.get("user_id")

    if room_id and user_id and room_id in room_presence:
        if user_id in room_presence[room_id]:
            room_presence[room_id][user_id]["activity"] = "Updated a task"

    if room_id:
        await sio.emit("task_updated", data, room=room_id, skip_sid=sid)
        await broadcast_presence(room_id)

@sio.event
async def task_deleted(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("task_deleted", data, room=room_id, skip_sid=sid)

@sio.event
async def task_moved(sid, data):
    room_id = data.get("roomId")
    user = connected_users.get(sid, {})
    user_id = user.get("user_id")

    if room_id and user_id and room_id in room_presence:
        if user_id in room_presence[room_id]:
            room_presence[room_id][user_id]["activity"] = "Moved a task"

    if room_id:
        await sio.emit("task_moved", data, room=room_id, skip_sid=sid)
        await broadcast_presence(room_id)

@sio.event
async def note_created(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("note_created", data, room=room_id, skip_sid=sid)

@sio.event
async def note_updated(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("note_updated", data, room=room_id, skip_sid=sid)

@sio.event
async def get_presence(sid, data):
    room_id = data.get("roomId")
    if room_id:
        users = list(room_presence.get(room_id, {}).values())
        await sio.emit("presence_update", {
            "roomId": room_id,
            "users": users,
            "count": len(users),
        }, to=sid)