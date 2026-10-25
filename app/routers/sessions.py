from fastapi import APIRouter, HTTPException
from app.models import SessionCreate
from app.db import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=dict)
def create_session(payload: SessionCreate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (title) VALUES (?)", (payload.title,))
    conn.commit()
    return {"id": cur.lastrowid, "title": payload.title}

@router.get("", response_model=list[dict])
def list_sessions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at FROM sessions ORDER BY id DESC")
    return [dict(r) for r in cur.fetchall()]

@router.get("/{session_id}/messages", response_model=list[dict])
def get_messages(session_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, session_id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    return [dict(r) for r in cur.fetchall()]
