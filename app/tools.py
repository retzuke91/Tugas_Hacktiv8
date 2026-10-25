import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Any
from app.db import get_db
from app.config import settings


def get_current_datetime() -> dict[str, str]:
    tz_name = settings.DEFAULT_TIMEZONE
    try:
        now = datetime.datetime.now(ZoneInfo(tz_name))
    except Exception:
        now = datetime.datetime.now()
        tz_name = "UTC"
    return {
        "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "timezone": tz_name
    }


def add_task(title: str, due_at: Optional[str] = None, priority: Optional[int] = None) -> dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, due_at, priority) VALUES (?, ?, ?)",
        (title, due_at, priority)
    )
    conn.commit()
    return {"status": "success", "task_id": cur.lastrowid, "title": title, "due_at": due_at, "priority": priority}


def list_tasks(status: Optional[str] = None, range: Optional[str] = None) -> list[dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT id, title, description, due_at, priority, status, created_at FROM tasks"
    params: list[Any] = []
    conditions: list[str] = []

    if status and status != "all":
        conditions.append("status = ?")
        params.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY CASE WHEN due_at IS NULL THEN 1 ELSE 0 END, due_at ASC, priority ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def update_task(id: int, title: Optional[str] = None, due_at: Optional[str] = None, priority: Optional[int] = None, status: Optional[str] = None) -> dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    fields: list[str] = []
    params: list[Any] = []

    if title is not None:
        fields.append("title = ?")
        params.append(title)
    if due_at is not None:
        fields.append("due_at = ?")
        params.append(due_at)
    if priority is not None:
        fields.append("priority = ?")
        params.append(priority)
    if status is not None:
        fields.append("status = ?")
        params.append(status)

    if not fields:
        return {"status": "no_change", "task_id": id}

    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(id)
    sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
    cur.execute(sql, params)
    conn.commit()
    return {"status": "success", "task_id": id, "updated_rows": cur.rowcount}


def complete_task(id: int) -> dict[str, Any]:
    return update_task(id=id, status="done")


def delete_task(id: int) -> dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    return {"status": "success", "task_id": id, "deleted_rows": cur.rowcount}


def add_note(content: str, tags: Optional[str] = None) -> dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (content, tags) VALUES (?, ?)",
        (content, tags)
    )
    conn.commit()
    return {"status": "success", "note_id": cur.lastrowid, "content": content, "tags": tags}


def search_notes(query: str) -> list[dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, content, tags, created_at FROM notes WHERE content LIKE ? OR tags LIKE ? ORDER BY id DESC",
        (f"%{query}%", f"%{query}%")
    )
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def save_memory(key: str, value: str) -> dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM memories WHERE key = ?", (key,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE memories SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (value, row["id"])
        )
        mem_id = row["id"]
    else:
        cur.execute(
            "INSERT INTO memories (key, value) VALUES (?, ?)",
            (key, value)
        )
        mem_id = cur.lastrowid
    conn.commit()
    return {"status": "success", "memory_id": mem_id, "key": key, "value": value}


# Function definitions registry for tool calling execution

def generate_daily_plan(prefer_morning: bool = True) -> dict:
    """Create simple daily schedule from pending tasks.
    If prefer_morning True, prioritize tasks in morning slot.
    Returns dict with 'plan' key.
    """
    conn = get_db()
    cur = conn.cursor()
    # fetch pending tasks
    cur.execute(
        "SELECT id, title, due_at, priority FROM tasks WHERE status = 'todo' ORDER BY priority ASC, due_at ASC"
    )
    rows = cur.fetchall()
    if not rows:
        return {"plan": "Tidak ada tugas pending hari ini."}
    parts = []
    for r in rows:
        title = r["title"]
        due = r["due_at"] or "tanpa deadline"
        prio = r["priority"] or "-"
        parts.append(f"- {title} (prio {prio}, deadline {due})")
    plan = "Rencana harian: \n" + "\n".join(parts)
    if prefer_morning:
        plan += "\nPrioritaskan tugas di pagi hari bila memungkinkan."
    return {"plan": plan}

TOOLS_REGISTRY = {
    "get_current_datetime": get_current_datetime,
    "add_task": add_task,
    "list_tasks": list_tasks,
    "update_task": update_task,
    "complete_task": complete_task,
    "delete_task": delete_task,
    "add_note": add_note,
    "search_notes": search_notes,
    "save_memory": save_memory,
    "generate_daily_plan": generate_daily_plan,
}

TOOL_DECLARATIONS = [
    get_current_datetime,
    add_task,
    list_tasks,
    update_task,
    complete_task,
    delete_task,
    add_note,
    search_notes,
    save_memory,
    generate_daily_plan,
]

TOOL_DECLARATIONS = [
    get_current_datetime,
    add_task,
    list_tasks,
    update_task,
    complete_task,
    delete_task,
    add_note,
    search_notes,
    save_memory,
]
