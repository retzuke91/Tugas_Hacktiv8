import time
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from app.db import get_db
from app.config import settings
from app.routers import tasks, notes, sessions, memories, chat, settings as settings_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("nara")

# Rate limiter: IP -> list of timestamps
_rate_limits: dict[str, list[float]] = defaultdict(list)

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_db()  # init schema on startup
    log.info("Nara backend initialized with WAL mode SQLite.")
    yield

app = FastAPI(title="Nara API", lifespan=lifespan)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Only rate-limit chat endpoint (LLM calls); other API calls are DB-only
    if not request.url.path.startswith("/api/chat"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    window = 60.0

    timestamps = [t for t in _rate_limits[client_ip] if now - t < window]
    if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
        log.warning("Rate limit exceeded for IP %s", client_ip)
        return JSONResponse(
            status_code=429,
            content={"detail": "Batas permintaan per menit tercapai. Mohon tunggu sesaat."}
        )

    timestamps.append(now)
    _rate_limits[client_ip] = timestamps
    return await call_next(request)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled exception: %s", exc, exc_info=True)
    msg = str(exc)
    if "GEMINI_API_KEY" in msg:
        return JSONResponse(
            status_code=400,
            content={"detail": "GEMINI_API_KEY belum dikonfigurasi atau tidak valid. Silakan periksa file .env."}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": f"Terjadi kesalahan pada sistem: {msg}"}
    )

app.include_router(tasks.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(memories.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
