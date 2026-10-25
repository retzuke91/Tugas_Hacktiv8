from fastapi import APIRouter
from app.models import NoteCreate
from app.tools import add_note, search_notes
from app.db import get_db

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("", response_model=dict)
def create_note(payload: NoteCreate):
    return add_note(payload.content, payload.tags)

@router.get("", response_model=list[dict])
def list_or_search_notes(q: str = ""):
    if q:
        return search_notes(q)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, content, tags, created_at FROM notes ORDER BY id DESC")
    return [dict(r) for r in cur.fetchall()]

@router.delete("/{note_id}", response_model=dict)
def delete_note(note_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    return {"status": "success", "note_id": note_id, "deleted_rows": cur.rowcount}
