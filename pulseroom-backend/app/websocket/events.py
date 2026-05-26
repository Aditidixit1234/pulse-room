from app.websocket.manager import sio

async def emit_to_room(room_id: str, event: str, data: dict):
    await sio.emit(event, data, room=room_id)

async def emit_to_user(sid: str, event: str, data: dict):
    await sio.emit(event, data, to=sid)

async def emit_task_created(room_id: str, task: dict):
    await emit_to_room(room_id, "task_created", task)

async def emit_task_updated(room_id: str, task_id: str, data: dict):
    await emit_to_room(room_id, "task_updated", {"id": task_id, "data": data})

async def emit_task_deleted(room_id: str, task_id: str):
    await emit_to_room(room_id, "task_deleted", {"id": task_id})

async def emit_notification(sid: str, notification: dict):
    await emit_to_user(sid, "notification", notification)