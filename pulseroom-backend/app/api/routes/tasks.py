from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.task import Task
from app.schemas.task import CreateTaskRequest, UpdateTaskRequest, TaskResponse
from app.core.dependencies import get_current_user
from app.websocket.events import emit_task_created, emit_task_updated, emit_task_deleted

router = APIRouter(prefix="/rooms/{room_id}/tasks", tags=["tasks"])

@router.get("", response_model=List[TaskResponse])
def get_tasks(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.room_id == room_id).all()
    return tasks

@router.post("", response_model=TaskResponse)
async def create_task(room_id: str, data: CreateTaskRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = Task(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        tag=data.tag,
        due_date=data.due_date,
        room_id=room_id,
        assignee_id=data.assignee_id,
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    await emit_task_created(room_id, {
        "id": str(task.id),
        "title": task.title,
        "status": task.status,
        "roomId": room_id,
    })
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(room_id: str, task_id: str, data: UpdateTaskRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.room_id == room_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    await emit_task_updated(room_id, task_id, update_data)
    return task

@router.delete("/{task_id}")
async def delete_task(room_id: str, task_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.room_id == room_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    await emit_task_deleted(room_id, task_id)
    return {"message": "Task deleted"}