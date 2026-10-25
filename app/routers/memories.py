from fastapi import APIRouter, HTTPException
from app.models import MemoryCreate, MemoryUpdate
from app.tools import save_memory
from app.db import get_db

router = APIRouter(prefix="/memories", tags=["memories"])

@router.get("", response_model=list[dict])
def list_memories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, key, value, created_at, updated_at FROM memories ORDER BY id DESC")
    return [dict(r) for r in cur.fetchall()]

@router.post("", response_model=dict)
def create_memory(payload: MemoryCreate):
    return save_memory(payload.key, payload.value)

@router.patch("/{memory_id}", response_model=dict)
def update_memory(memory_id: int, payload: MemoryUpdate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE memories SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (payload.value, memory_id)
    )
    conn.commit()
    return {"status": "success", "memory_id": memory_id}

@router.delete("/{memory_id}", response_model=dict)
def delete_memory(memory_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    return {"status": "success", "memory_id": memory_id, "deleted_rows": cur.rowcount}
