import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from app.db import get_db
from app.config import settings

PERSONA_DESCRIPTIONS = {
    "nara": "Nara, asisten produktivitas pribadi yang ramah, hangat, dan suportif.",
    "coach": "Coach Produktivitas yang tegas, disiplin, berorientasi aksi, dan tanpa basa-basi.",
    "sekretaris": "Sekretaris pribadi yang rapi, terstruktur, cermat, dan profesional."
}

STYLE_DESCRIPTIONS = {
    "formal": "Gunakan bahasa Indonesia baku yang sopan, terstruktur, dan resmi.",
    "santai": "Gunakan bahasa Indonesia santai, akrab, luwes, dan bersahabat.",
    "singkat": "Sangat singkat, langsung ke inti permasalahan, tanpa pengantar atau penutup panjang.",
    "motivator": "Penuh semangat, berikan motivasi positif dan dorongan untuk segera menyelesaikan tugas."
}

LENGTH_DESCRIPTIONS = {
    "ringkas": "Jawab dengan ringkas (1-3 kalimat).",
    "sedang": "Jawab dengan panjang sedang, proporsional dan jelas.",
    "detail": "Jawab secara mendalam dan berikan detail atau breakdown langkah-langkah jika diperlukan."
}

def build_system_prompt(
    persona: Optional[str] = None,
    style: Optional[str] = None,
    domain: Optional[str] = None,
    length: Optional[str] = None,
    memory_on: bool = True,
    tz_name: Optional[str] = None
) -> str:
    persona_key = (persona or settings.DEFAULT_PERSONA).lower()
    style_key = (style or settings.DEFAULT_STYLE).lower()
    domain_val = domain or "Umum"
    if isinstance(length, int):
        length_key = "ringkas" if length <= 400 else ("detail" if length >= 1200 else "sedang")
    else:
        length_key = (str(length) if length else "sedang").lower()
    timezone = tz_name or settings.DEFAULT_TIMEZONE

    try:
        now_dt = datetime.datetime.now(ZoneInfo(timezone))
    except Exception:
        now_dt = datetime.datetime.now()
        timezone = "UTC"

    now_str = now_dt.strftime("%A, %Y-%m-%d %H:%M:%S")

    persona_desc = PERSONA_DESCRIPTIONS.get(persona_key, PERSONA_DESCRIPTIONS["nara"])
    style_desc = STYLE_DESCRIPTIONS.get(style_key, STYLE_DESCRIPTIONS["santai"])
    length_desc = LENGTH_DESCRIPTIONS.get(length_key, LENGTH_DESCRIPTIONS["sedang"])

    prompt = [
        f"Kamu adalah {persona_desc}",
        f"Gaya bahasa: {style_desc}",
        f"Panjang jawaban: {length_desc}",
        f"Domain fokus: {domain_val}.",
        f"Waktu sekarang: {now_str} ({timezone}).",
    ]

    if memory_on:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM memories ORDER BY updated_at DESC")
        rows = cur.fetchall()
        if rows:
            memories_list = [f"- {r['key']}: {r['value']}" for r in rows]
            prompt.append("Hal yang kamu ketahui tentang pengguna (memory):\n" + "\n".join(memories_list))

    prompt.append(
        "Aturan wajib:\n"
        "1. Selalu gunakan tools untuk membaca, membuat, mengubah, atau menghapus tugas dan catatan. JANGAN PERNAH mengarang data.\n"
        "2. Panggil get_current_datetime bila perlu memastikan waktu saat pengguna berkata 'besok', 'lusa', atau hari tertentu.\n"
        "3. Jika tanggal/waktu atau rincian tugas ambigu, tanyakan konfirmasi singkat kepada pengguna.\n"
        "4. Konfirmasi hasil eksekusi tool secara ringkas dan ramah sesuai persona.\n"
        "5. Jika pengguna meminta rencana harian atau bantuan jadwal ('susun jadwalku', 'rencana hari ini'), panggil list_tasks(status='todo'), pertimbangkan preferensi dari memory (misal jam produktif), lalu urutkan berdasarkan due date dan prioritas, serta susun jadwal terstruktur.\n"
        "6. Jika pengguna membagikan preferensi pribadi, kebiasaan, atau fakta penting ('aku lebih produktif pagi hari', 'panggil aku Dimas'), simpan menggunakan tool save_memory.\n"
        "7. Tolak permintaan di luar cakupan produktivitas pribadi dengan sopan dan arahkan kembali."
    )

    return "\n\n".join(prompt)
