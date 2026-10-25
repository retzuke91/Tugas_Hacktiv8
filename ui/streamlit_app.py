import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")

st.set_page_config(page_title="Nara — Asisten Produktivitas", page_icon="✨", layout="wide")

# Helper to communicate with backend
def api_request(method: str, path: str, json: dict = None, params: dict = None):
    url = f"{BACKEND_URL}{path}"
    try:
        resp = requests.request(method, url, json=json, params=params, timeout=45)
        if resp.status_code >= 400:
            return None, f"Error {resp.status_code}: {resp.text}"
        return resp.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"Gagal menghubungi server backend: {e}"

# Fetch or init settings
settings_data, err = api_request("GET", "/api/settings")
if not settings_data:
    settings_data = {
        "persona": "nara",
        "style": "santai",
        "domain": "Umum",
        "temperature": 0.6,
        "length": "sedang",
        "memory_on": "true",
        "timezone": "Asia/Jakarta"
    }

# Sidebar - Settings & Sessions
with st.sidebar:
    st.title("✨ Nara AI")
    st.caption("Asisten Produktivitas Pribadi")
    st.divider()

    # Session Management
    st.subheader("Sesi Percakapan")
    sessions_data, _ = api_request("GET", "/api/sessions")
    sessions = sessions_data or []

    if st.button("➕ Sesi Baru", use_container_width=True):
        new_sess, _ = api_request("POST", "/api/sessions", json={"title": f"Sesi #{len(sessions) + 1}"})
        if new_sess:
            st.session_state["session_id"] = new_sess["id"]
            st.rerun()

    session_options = {s["id"]: f"#{s['id']} {s['title']}" for s in sessions}
    if not session_options:
        # Auto create first session
        first_sess, _ = api_request("POST", "/api/sessions", json={"title": "Sesi #1"})
        if first_sess:
            st.session_state["session_id"] = first_sess["id"]
            st.rerun()

    current_session_id = st.session_state.get("session_id", list(session_options.keys())[0] if session_options else 1)
    if current_session_id not in session_options and session_options:
        current_session_id = list(session_options.keys())[0]

    chosen_session = st.selectbox(
        "Pilih Sesi",
        options=list(session_options.keys()),
        format_func=lambda sid: session_options.get(sid, f"#{sid}"),
        index=list(session_options.keys()).index(current_session_id) if current_session_id in session_options else 0
    )
    st.session_state["session_id"] = chosen_session

    st.divider()
    st.subheader("⚙️ Pengaturan")

    persona = st.selectbox(
        "Persona",
        ["nara", "coach", "sekretaris"],
        index=["nara", "coach", "sekretaris"].index(settings_data.get("persona", "nara").lower()) if settings_data.get("persona", "nara").lower() in ["nara", "coach", "sekretaris"] else 0,
        help="Nara (ramah), Coach (tegas), Sekretaris (rapi)"
    )

    style = st.selectbox(
        "Gaya Bahasa",
        ["santai", "formal", "singkat", "motivator"],
        index=["santai", "formal", "singkat", "motivator"].index(settings_data.get("style", "santai").lower()) if settings_data.get("style", "santai").lower() in ["santai", "formal", "singkat", "motivator"] else 0
    )

    domain = st.selectbox(
        "Domain Fokus",
        ["Umum", "Kuliah", "Kerja", "Freelance"],
        index=["Umum", "Kuliah", "Kerja", "Freelance"].index(settings_data.get("domain", "Umum")) if settings_data.get("domain", "Umum") in ["Umum", "Kuliah", "Kerja", "Freelance"] else 0
    )

    temp_val = float(settings_data.get("temperature", 0.6))
    temperature = st.slider("Kreativitas (Temperature)", min_value=0.0, max_value=1.0, value=temp_val, step=0.1)

    length = st.selectbox(
        "Panjang Jawaban",
        ["ringkas", "sedang", "detail"],
        index=["ringkas", "sedang", "detail"].index(settings_data.get("length", "sedang").lower()) if settings_data.get("length", "sedang").lower() in ["ringkas", "sedang", "detail"] else 1
    )

    memory_on = st.toggle("Memory Jangka Panjang", value=str(settings_data.get("memory_on", "true")).lower() == "true")
    timezone = st.text_input("Zona Waktu (IANA)", value=settings_data.get("timezone", "Asia/Jakarta"))

    if st.button("Simpan Pengaturan", use_container_width=True):
        api_request("PUT", "/api/settings", json={
            "persona": persona,
            "style": style,
            "domain": domain,
            "temperature": temperature,
            "length": length,
            "memory_on": memory_on,
            "timezone": timezone
        })
        st.success("Pengaturan tersimpan!")

# Tabs Navigation
tab_chat, tab_tasks, tab_notes, tab_memories = st.tabs(["💬 Chat", "📋 Tugas", "📝 Catatan", "🧠 Memory"])

# Tab 1: Chat
with tab_chat:
    active_session_id = st.session_state.get("session_id")
    if active_session_id:
        msgs, err = api_request("GET", f"/api/sessions/{active_session_id}/messages")
        if err:
            st.error(err)
        else:
            # FR-21: Saran proaktif hanya di awal sesi (belum ada pesan)
            if not msgs:
                summary, _ = api_request("GET", "/api/chat/proactive-summary")
                if summary and summary.get("message"):
                    st.info(f"💡 {summary['message']}")

            for m in (msgs or []):
                role = "user" if m["role"] == "user" else "assistant"
                with st.chat_message(role):
                    st.write(m["content"])

        user_input = st.chat_input("Ketik pesan atau instruksi untuk Nara...")
        if user_input:
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Nara sedang berpikir..."):
                    payload = {
                        "session_id": active_session_id,
                        "message": user_input,
                        "persona": persona,
                        "style": style,
                        "domain": domain,
                        "temperature": temperature,
                        "length": length,
                        "max_output_tokens": 800 if length == "sedang" else (400 if length == "ringkas" else 1500),
                        "memory_on": memory_on,
                        "timezone": timezone
                    }
                    res, err = api_request("POST", "/api/chat", json=payload)
                    if err:
                        st.error(f"Gagal memproses pesan: {err}")
                    else:
                        st.write(res.get("reply", ""))
            st.rerun()

# Tab 2: Tugas
with tab_tasks:
    st.subheader("Daftar Tugas")
    col_filter, col_add = st.columns([1, 2])
    with col_filter:
        status_filter = st.selectbox("Filter Status", ["all", "todo", "done"])

    with col_add:
        with st.expander("➕ Tambah Tugas Manual"):
            with st.form("add_task_form"):
                new_title = st.text_input("Judul Tugas", placeholder="Contoh: Kumpul laporan PKL")
                new_due = st.text_input("Due Date (YYYY-MM-DD HH:MM)", placeholder="2026-10-30 15:00")
                new_prio = st.selectbox("Prioritas (1 = Tinggi, 3 = Rendah)", [1, 2, 3], index=1)
                submitted = st.form_submit_button("Simpan Tugas")
                if submitted and new_title:
                    api_request("POST", "/api/tasks", json={
                        "title": new_title,
                        "due_at": new_due or None,
                        "priority": new_prio
                    })
                    st.success("Tugas ditambahkan!")
                    st.rerun()

    tasks_list, _ = api_request("GET", "/api/tasks", params={"status": status_filter})
    if tasks_list:
        for t in tasks_list:
            cols = st.columns([0.1, 0.4, 0.25, 0.15, 0.1])
            is_done = t["status"] == "done"
            status_symbol = "✅" if is_done else "⏳"
            cols[0].write(status_symbol)
            cols[1].markdown(f"**{t['title']}**" if not is_done else f"~~{t['title']}~~")
            cols[2].caption(f"📅 {t.get('due_at') or 'Tanpa deadline'}")
            cols[3].caption(f"Prio: {t.get('priority') or '-'}")
            btn_col = cols[4]
            if not is_done:
                if btn_col.button("✓", key=f"done_{t['id']}", help="Selesaikan"):
                    api_request("POST", f"/api/tasks/{t['id']}/complete")
                    st.rerun()
            else:
                if btn_col.button("🗑️", key=f"del_{t['id']}", help="Hapus"):
                    api_request("DELETE", f"/api/tasks/{t['id']}")
                    st.rerun()
    else:
        st.info("Tidak ada tugas.")

# Tab 3: Catatan
with tab_notes:
    st.subheader("Catatan")
    col_search, col_add_note = st.columns([2, 1])
    with col_search:
        search_q = st.text_input("🔍 Cari Catatan", placeholder="Ketik kata kunci...")
    with col_add_note:
        with st.expander("➕ Tambah Catatan"):
            with st.form("add_note_form"):
                note_content = st.text_area("Isi Catatan")
                note_tags = st.text_input("Tags (opsional)", placeholder="mis. skripsi, ide")
                note_sub = st.form_submit_button("Simpan")
                if note_sub and note_content:
                    api_request("POST", "/api/notes", json={"content": note_content, "tags": note_tags or None})
                    st.success("Catatan disimpan!")
                    st.rerun()

    notes_list, _ = api_request("GET", "/api/notes", params={"q": search_q} if search_q else None)
    if notes_list:
        for n in notes_list:
            c1, c2 = st.columns([0.9, 0.1])
            c1.markdown(f"**{n['content']}**")
            if n.get("tags"):
                c1.caption(f"🏷️ `{n['tags']}` · 🕒 {n.get('created_at', '')}")
            if c2.button("🗑️", key=f"del_note_{n['id']}"):
                api_request("DELETE", f"/api/notes/{n['id']}")
                st.rerun()
            st.divider()
    else:
        st.info("Belum ada catatan.")

# Tab 4: Memory Jangka Panjang
with tab_memories:
    st.subheader("Memory Jangka Panjang")
    st.caption("Fakta dan preferensi pengguna yang diingat oleh Nara.")

    with st.expander("➕ Tambah Memory Baru"):
        with st.form("add_mem_form"):
            mem_key = st.text_input("Kunci / Topik", placeholder="mis. jam_produktif, panggilan")
            mem_val = st.text_input("Isi / Preferensi", placeholder="mis. Pagi hari pukul 08:00 - 11:00")
            mem_sub = st.form_submit_button("Simpan Memory")
            if mem_sub and mem_key and mem_val:
                api_request("POST", "/api/memories", json={"key": mem_key, "value": mem_val})
                st.success("Memory disimpan!")
                st.rerun()

    memories_list, _ = api_request("GET", "/api/memories")
    if memories_list:
        for m in memories_list:
            mc1, mc2 = st.columns([0.85, 0.15])
            mc1.markdown(f"**{m['key']}**: {m['value']}")
            mc1.caption(f"Diperbarui: {m.get('updated_at', m.get('created_at', ''))}")
            if mc2.button("🗑️", key=f"del_mem_{m['id']}"):
                api_request("DELETE", f"/api/memories/{m['id']}")
                st.rerun()
            st.divider()
    else:
        st.info("Belum ada memory tersimpan.")
