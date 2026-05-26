import redis.asyncio as aioredis
from app.core.config import settings

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

async def set_user_online(user_id: str, room_id: str, data: dict):
    r = await get_redis()
    import json
    await r.hset(f"presence:{room_id}", user_id, json.dumps(data))
    await r.expire(f"presence:{room_id}", 3600)

async def set_user_offline(user_id: str, room_id: str):
    r = await get_redis()
    await r.hdel(f"presence:{room_id}", user_id)

async def get_room_presence(room_id: str) -> list:
    r = await get_redis()
    import json
    data = await r.hgetall(f"presence:{room_id}")
    return [json.loads(v) for v in data.values()]

async def cache_set(key: str, value: str, expire: int = 300):
    r = await get_redis()
    await r.setex(key, expire, value)

async def cache_get(key: str):
    r = await get_redis()
    return await r.get(key)

async def publish_event(channel: str, message: str):
    r = await get_redis()
    await r.publish(channel, message)