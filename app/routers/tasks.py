from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import TaskCreate, TaskUpdate, NoteCreate, MemoryCreate, MemoryUpdate, SessionCreate, ChatRequest, SettingsUpdate
from app.db import get_db
from app.tools import list_tasks, add_task, update_task, complete_task, delete_task, add_note, search_notes, save_memory

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=dict)
def create_task(payload: TaskCreate):
    result = add_task(payload.title, payload.due_at, payload.priority)
    return result

@router.get("", response_model=List[dict])
def read_tasks(status: str = "all"):
    return list_tasks(status)

@router.patch("/{task_id}", response_model=dict)
def modify_task(task_id: int, payload: TaskUpdate):
    result = update_task(task_id, payload.title, payload.due_at, payload.priority, payload.status)
    return result

@router.post("/{task_id}/complete", response_model=dict)
def mark_done(task_id: int):
    return complete_task(task_id)

@router.delete("/{task_id}", response_model=dict)
def remove_task(task_id: int):
    return delete_task(task_id)
