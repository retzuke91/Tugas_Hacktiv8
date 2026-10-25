from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: Optional[str] = None
    priority: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None


class NoteCreate(BaseModel):
    content: str
    tags: Optional[str] = None


class MemoryCreate(BaseModel):
    key: str
    value: str


class MemoryUpdate(BaseModel):
    value: str


class SessionCreate(BaseModel):
    title: str = "Sesi Baru"


class ChatRequest(BaseModel):
    session_id: int
    message: str
    style: Optional[str] = None
    persona: Optional[str] = None
    domain: Optional[str] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    length: Optional[str] = None          # ringkas / sedang / detail
    memory_on: Optional[bool] = True
    timezone: Optional[str] = None


class SettingsUpdate(BaseModel):
    style: Optional[str] = None
    persona: Optional[str] = None
    domain: Optional[str] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    memory_on: Optional[bool] = None
    timezone: Optional[str] = None
