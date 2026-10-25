from fastapi import APIRouter
from app.models import SettingsUpdate
from app.db import get_db
from app.config import settings as default_config

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULTS = {
    "style": default_config.DEFAULT_STYLE,
    "persona": default_config.DEFAULT_PERSONA,
    "domain": "Umum",
    "temperature": str(default_config.DEFAULT_TEMPERATURE),
    "length": "sedang",
    "memory_on": "true",
    "timezone": default_config.DEFAULT_TIMEZONE
}

@router.get("", response_model=dict)
def get_settings():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings")
    db_settings = {row["key"]: row["value"] for row in cur.fetchall()}
    merged = {**DEFAULTS, **db_settings}
    return merged

@router.put("", response_model=dict)
def update_settings(payload: SettingsUpdate):
    conn = get_db()
    cur = conn.cursor()
    updates = payload.model_dump(exclude_unset=True)
    for k, v in updates.items():
        if v is not None:
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (k, str(v))
            )
    conn.commit()
    return get_settings()
