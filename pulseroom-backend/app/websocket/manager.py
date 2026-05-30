from typing import Dict, Set
import socketio
import asyncio
import json

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

room_connections: Dict[str, Set[str]] = {}
connected_users: Dict[str, dict] = {}
room_presence: Dict[str, Dict[str, dict]] = {}


async def start_redis_listener():
    try:
        from app.services.redis_service import subscribe_to_channel
        pubsub = await subscribe_to_channel("pulseroom:events")
        print("Redis pub/sub listener started!")
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    event = data.get("event")
                    room_id = data.get("roomId")
                    payload = data.get("payload", {})
                    if event and room_id:
                        await sio.emit(event, payload, room=room_id)
                except Exception as e:
                    print(f"Redis listener error: {e}")
    except Exception as e:
        print(f"Redis pub/sub not available: {e}")


async def publish_to_redis(event: str, room_id: str, payload: dict):
    try:
        from app.services.redis_service import publish_event
        await publish_event("pulseroom:events", {
            "event": event,
            "roomId": room_id,
            "payload": payload,
        })
    except Exception as e:
        print(f"Redis publish error: {e}")


async def broadcast_presence(room_id: str):
    users = list(room_presence.get(room_id, {}).values())
    await sio.emit("presence_update", {
        "roomId": room_id,
        "users": users,
        "count": len(users),
    }, room=room_id)
    await publish_to_redis("presence_update", room_id, {
        "roomId": room_id,
        "users": users,
        "count": len(users),
    })


@sio.event
async def connect(sid, environ, auth):
    print(f"Connected: {sid}")
    connected_users[sid] = {"sid": sid}


@sio.event
async def disconnect(sid):
    print(f"Disconnected: {sid}")
    user = connected_users.pop(sid, {})
    room_id = user.get("room_id")
    user_id = user.get("user_id")

    if room_id:
        if room_id in room_connections:
            room_connections[room_id].discard(sid)
        if room_id in room_presence and user_id:
            room_presence[room_id].pop(user_id, None)
        await broadcast_presence(room_id)
        await sio.emit("user_left", {
            "userId": user_id,
            "userName": user.get("user_name"),
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

    await sio.enter_room(sid, room_id)

    if room_id not in room_connections:
        room_connections[room_id] = set()
    room_connections[room_id].add(sid)

    connected_users[sid].update({
        "room_id": room_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_initials": user_initials,
    })

    if room_id not in room_presence:
        room_presence[room_id] = {}

    room_presence[room_id][user_id] = {
        "userId": user_id,
        "userName": user_name,
        "userInitials": user_initials,
        "userRole": user_role,
        "status": "online",
        "activity": "Viewing room",
        "isTyping": False,
    }

    try:
        from app.services.redis_service import set_user_online
        await set_user_online(user_id, room_id, room_presence[room_id][user_id])
    except Exception:
        pass

    await sio.emit("presence_update", {
        "roomId": room_id,
        "users": list(room_presence[room_id].values()),
        "count": len(room_presence[room_id]),
    }, to=sid)

    await sio.emit("user_joined", {
        "userId": user_id,
        "userName": user_name,
        "userInitials": user_initials,
        "userRole": user_role,
        "status": "online",
    }, room=room_id, skip_sid=sid)

    await broadcast_presence(room_id)


@sio.event
async def leave_room(sid, data):
    room_id = data.get("roomId")
    if not room_id:
        return

    await sio.leave_room(sid, room_id)

    if room_id in room_connections:
        room_connections[room_id].discard(sid)

    user = connected_users.get(sid, {})
    user_id = user.get("user_id")

    if room_id in room_presence and user_id:
        room_presence[room_id].pop(user_id, None)

    try:
        from app.services.redis_service import set_user_offline
        await set_user_offline(user_id, room_id)
    except Exception:
        pass

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
            room_presence[room_id][user_id]["isTyping"] = is_typing
            room_presence[room_id][user_id]["activity"] = "Typing…" if is_typing else "Viewing room"

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

    if room_id and user_id and room_id in room_presence:
        if user_id in room_presence[room_id]:
            room_presence[room_id][user_id]["activity"] = "Created a task"

    if room_id:
        await sio.emit("task_created", data, room=room_id, skip_sid=sid)
        await publish_to_redis("task_created", room_id, data)
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
        await publish_to_redis("task_updated", room_id, data)
        await broadcast_presence(room_id)


@sio.event
async def task_deleted(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("task_deleted", data, room=room_id, skip_sid=sid)
        await publish_to_redis("task_deleted", room_id, data)


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
        await publish_to_redis("task_moved", room_id, data)
        await broadcast_presence(room_id)


@sio.event
async def note_created(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("note_created", data, room=room_id, skip_sid=sid)
        await publish_to_redis("note_created", room_id, data)


@sio.event
async def note_updated(sid, data):
    room_id = data.get("roomId")
    if room_id:
        await sio.emit("note_updated", data, room=room_id, skip_sid=sid)
        await publish_to_redis("note_updated", room_id, data)


@sio.event
async def get_presence(sid, data):
    room_id = data.get("roomId")
    if room_id:
        try:
            from app.services.redis_service import get_room_presence
            redis_users = await get_room_presence(room_id)
            if redis_users:
                await sio.emit("presence_update", {
                    "roomId": room_id,
                    "users": redis_users,
                    "count": len(redis_users),
                }, to=sid)
                return
        except Exception:
            pass

        users = list(room_presence.get(room_id, {}).values())
        await sio.emit("presence_update", {
            "roomId": room_id,
            "users": users,
            "count": len(users),
        }, to=sid)