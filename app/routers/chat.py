from fastapi import APIRouter, HTTPException
from typing import List
from app.models import ChatRequest, SettingsUpdate
from app.prompts import build_system_prompt
from app.llm import run_chat, run_chat_stream
from app.db import get_db

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=dict)
def chat_endpoint(request: ChatRequest):
    # Load session history
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (request.session_id,)
    )
    history = [dict(r) for r in cur.fetchall()]

    system_prompt = build_system_prompt(
        persona=request.persona,
        style=request.style,
        domain=request.domain,
        length=request.length or request.max_output_tokens,
        memory_on=request.memory_on,
        tz_name=request.timezone
    )

    reply = run_chat(
        history=history,
        new_message=request.message,
        system_prompt=system_prompt,
        temperature=request.temperature,
        max_output_tokens=request.max_output_tokens,
    )

    # Store user and assistant messages
    cur.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (request.session_id, "user", request.message)
    )
    cur.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (request.session_id, "assistant", reply)
    )
    conn.commit()

    return {"reply": reply}

@router.post("/stream", response_model=List[str])
def chat_stream(request: ChatRequest):
    # Similar to above but return list of chunks (simplified)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (request.session_id,)
    )
    history = [dict(r) for r in cur.fetchall()]

    system_prompt = build_system_prompt(
        persona=request.persona,
        style=request.style,
        domain=request.domain,
        length=request.length or request.max_output_tokens,
        memory_on=request.memory_on,
        tz_name=request.timezone
    )

    chunks = []
    for chunk in run_chat_stream(
        history=history,
        new_message=request.message,
        system_prompt=system_prompt,
        temperature=request.temperature,
        max_output_tokens=request.max_output_tokens,
    ):
        chunks.append(chunk)

    # Store messages
    cur.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (request.session_id, "user", request.message)
    )
    cur.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (request.session_id, "assistant", "".join(chunks))
    )
    conn.commit()

    return chunks

@router.get("/proactive-summary", response_model=dict)
def proactive_summary():
    """FR-21: Saran proaktif ringan di awal sesi."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, due_at, priority FROM tasks WHERE status = 'todo' ORDER BY priority ASC, due_at ASC")
    tasks = [dict(r) for r in cur.fetchall()]

    if not tasks:
        return {"message": "Semua tugas selesai! Santai sejenak atau buat rencana baru."}

    # Check due soon
    due_tasks = [t for t in tasks if t.get("due_at")]
    if due_tasks:
        titles = ", ".join([f"'{t['title']}'" for t in due_tasks[:3]])
        return {
            "message": f"Ada {len(tasks)} tugas aktif. Tugas terdekat: {titles}.",
            "count": len(tasks)
        }
    return {
        "message": f"Kamu memiliki {len(tasks)} tugas aktif. Mau saya bantu susun jadwal?",
        "count": len(tasks)
    }
