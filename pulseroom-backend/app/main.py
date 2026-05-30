from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import asyncio
from app.core.config import settings
from app.db.database import create_tables
from app.websocket.manager import sio, start_redis_listener
from app.api.routes import auth, rooms, tasks, members, notifications, messages, notes, activity, search, analytics

app = FastAPI(
    title="PulseRoom API",
    description="Real-time collaborative workspace backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(tasks.router)
app.include_router(members.router)
app.include_router(notifications.router)
app.include_router(messages.router)
app.include_router(notes.router)
app.include_router(activity.router)
app.include_router(search.router)
app.include_router(analytics.router)

socket_app = socketio.ASGIApp(sio, app)

@app.on_event("startup")
async def startup():
    create_tables()
    # Start Redis pub/sub listener
    asyncio.create_task(start_redis_listener())
    print("PulseRoom backend started!")

@app.get("/")
def root():
    return {"message": "PulseRoom API running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}