import streamlit as st
import requests
import pandas as pd
import io
import time
import json
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BookForge AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Crimson+Pro:ital,wght@0,300;0,400;1,300&display=swap');

html, body, [class*="css"] { font-family: 'Crimson Pro', Georgia, serif; }
.main { background: #0d0d0d; }
.block-container { padding: 2rem 3rem; max-width: 1200px; }
#MainMenu, footer, header { visibility: hidden; }

.hero { text-align: center; padding: 3rem 0 2rem; border-bottom: 1px solid #2a2a2a; margin-bottom: 2.5rem; }
.hero h1 { font-family: 'Playfair Display', serif; font-size: 3.8rem; font-weight: 900; color: #f5e6c8; letter-spacing: -1px; margin-bottom: 0.3rem; text-shadow: 0 0 60px rgba(212,175,55,0.3); }
.hero .sub { font-size: 1.15rem; color: #8a7a5a; font-style: italic; letter-spacing: 0.05em; }

.card { background: #141414; border: 1px solid #252525; border-radius: 12px; padding: 1.8rem; margin-bottom: 1.2rem; }
.card-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #d4af37; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.8rem; }
.step-badge { display: inline-block; background: #d4af37; color: #0d0d0d; font-family: 'Playfair Display', serif; font-weight: 700; font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.5rem; }

.book-card { background: #141414; border: 1px solid #252525; border-left: 4px solid #d4af37; border-radius: 8px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; }
.book-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #f5e6c8; font-weight: 700; margin-bottom: 0.3rem; }
.book-meta { font-size: 0.85rem; color: #6b6b5a; font-style: italic; }

.status-pending  { background:#2a2010; color:#d4af37; border:1px solid #d4af37; padding:2px 10px; border-radius:20px; font-size:0.75rem; }
.status-ready    { background:#0f2a1a; color:#4caf50; border:1px solid #4caf50; padding:2px 10px; border-radius:20px; font-size:0.75rem; }
.status-error    { background:#2a1010; color:#f44336; border:1px solid #f44336; padding:2px 10px; border-radius:20px; font-size:0.75rem; }
.status-outline_ready { background:#101828; color:#6ab4f7; border:1px solid #6ab4f7; padding:2px 10px; border-radius:20px; font-size:0.75rem; }
.status-generating { background:#1a1410; color:#f7c06a; border:1px solid #f7c06a; padding:2px 10px; border-radius:20px; font-size:0.75rem; }

.chapter-box { background: #111; border: 1px solid #222; border-radius: 8px; padding: 1.2rem; margin: 0.5rem 0; max-height: 200px; overflow-y: auto; font-size: 0.9rem; color: #ccc; line-height: 1.7; font-style: italic; }

section[data-testid="stSidebar"] { background: #0a0a0a !important; border-right: 1px solid #1e1e1e; }

.stButton > button { background: #d4af37 !important; color: #0d0d0d !important; font-family: 'Playfair Display', serif !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; padding: 0.5rem 1.5rem !important; letter-spacing: 0.05em !important; }
.stButton > button:hover { background: #f5c842 !important; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; color: #f5e6c8 !important; border-radius: 6px !important; }

[data-testid="metric-container"] { background: #141414; border: 1px solid #252525; border-radius: 10px; padding: 1rem; }
[data-testid="metric-container"] label { color: #8a7a5a !important; font-style: italic; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #d4af37 !important; font-family: 'Playfair Display', serif; }

hr { border-color: #1e1e1e !important; }
[data-testid="stFileUploader"] { background: #141414; border: 1px dashed #2a2a2a; border-radius: 10px; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "books" not in st.session_state:
    st.session_state.books = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "page" not in st.session_state:
    st.session_state.page = "home"


# ── Groq API Helper ───────────────────────────────────────────────────────────
def call_groq(api_key, system_prompt, user_prompt, temperature=0.7, max_tokens=2000):
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        },
        timeout=60
    )
    data = res.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    return data["choices"][0]["message"]["content"].strip()


def clean_json(text):
    """Robustly extract and fix JSON from LLM output."""
    import re
    text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    # Remove control/invisible characters
    text = re.sub(r'[\x00-\x1f\x7f]', ' ', text)
    # Remove trailing commas before ] or }
    text = re.sub(r',\s*([\]}])', r'\1', text)
    return text

def generate_outline(api_key, title, notes):
    system = (
        "You are a JSON-only book outline generator. "
        "Output ONLY raw valid JSON. No markdown, no explanation, no code fences. "
        "All string values must be single-line ASCII."
    )
    prompt = (
        f'Generate a 6-chapter outline for the book: "{title}". Notes: {notes[:400]}\n\n'
        'Return ONLY this JSON (fill in real values, keep strings short and single-line):\n'
        '{"description":"One sentence about the book.","chapters":[' +
        ','.join([
            f'{{"number":{i},"title":"Chapter {i} Title","description":"One sentence."}}'
            for i in range(1, 7)
        ]) + ']}'
    )
    for attempt in range(3):
        try:
            raw = call_groq(api_key, system, prompt, temperature=0.2, max_tokens=900)
            cleaned = clean_json(raw)
            return json.loads(cleaned)
        except (json.JSONDecodeError, Exception) as e:
            if attempt == 2:
                raise Exception(f"Failed to parse outline JSON after 3 tries: {e}")
            time.sleep(1)


def generate_chapter(api_key, title, outline_desc, chapter_num, chapter_title, chapter_desc, previous_summaries, notes=""):
    context = ""
    if previous_summaries:
        context = "PREVIOUS CHAPTERS SUMMARY (for continuity):\n" + "\n".join(
            [f"Ch {s['num']}: {s['summary']}" for s in previous_summaries]
        ) + "\n\n"

    system = "You are a professional book author. Write vivid, engaging, well-structured content."
    prompt = f"""Book: "{title}"
Description: {outline_desc}

{context}Write Chapter {chapter_num}: {chapter_title}
Chapter focus: {chapter_desc}
{"Special instructions: " + notes if notes else ""}

Write approximately 700 words of compelling chapter content. No heading needed."""

    content = call_groq(api_key, system, prompt, temperature=0.8, max_tokens=1500)

    sum_sys = "Summarize concisely."
    sum_prompt = f"Summarize in 2-3 sentences for context:\n\n{content[:1500]}"
    summary = call_groq(api_key, sum_sys, sum_prompt, temperature=0.3, max_tokens=150)

    return content, summary


def create_txt(book):
    lines = [f"{'='*60}", f"  {book['title'].upper()}", f"{'='*60}\n"]
    if book.get("outline"):
        lines.append(book["outline"].get("description", ""))
        lines.append("")
    for ch in book.get("chapters", []):
        lines += [f"\n{'─'*60}", f"Chapter {ch['number']}: {ch['title']}", f"{'─'*60}\n", ch["content"], ""]
    return "\n".join(lines)


def create_docx(book):
    doc = Document()
    h = doc.add_heading(book["title"], 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    if book.get("outline"):
        p = doc.add_paragraph(book["outline"].get("description", ""))
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p.runs:
            p.runs[0].italic = True
    doc.add_page_break()
    for ch in book.get("chapters", []):
        doc.add_heading(f"Chapter {ch['number']}: {ch['title']}", level=1)
        doc.add_paragraph()
        for para in ch["content"].split("\n\n"):
            if para.strip():
                doc.add_paragraph(para.strip())
        doc.add_page_break()
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def word_count(book):
    return sum(len(ch.get("content", "").split()) for ch in book.get("chapters", []))


def do_rerun():
    """Safe rerun that works across Streamlit versions."""
    try:
        st.rerun(scope="app")
    except TypeError:
        st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:1rem 0 1.5rem;'>
        <div style='font-family:Playfair Display,serif; font-size:1.8rem; color:#d4af37; font-weight:900;'>📚 BookForge</div>
        <div style='font-size:0.75rem; color:#6b6b5a; font-style:italic; margin-top:4px;'>AI Book Generation · Groq Powered</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='color:#8a7a5a; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.1em;'>🔑 Groq API Key (Free)</div>", unsafe_allow_html=True)
    api_key = st.text_input("", type="password", placeholder="gsk_...", value=st.session_state.api_key, label_visibility="collapsed")
    if api_key:
        st.session_state.api_key = api_key
        st.markdown("<div style='color:#4caf50; font-size:0.8rem;'>✓ API key set</div>", unsafe_allow_html=True)
    else:
        st.markdown("""<div style='color:#8a7a5a; font-size:0.75rem; font-style:italic;'>
        Get free key at <a href='https://console.groq.com' style='color:#d4af37;'>console.groq.com</a><br>
        <span style='color:#4caf50;'>✓ Works in Pakistan · 14,400 req/day</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='color:#8a7a5a; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.1em;'>📖 Navigation</div>", unsafe_allow_html=True)
    pages = {"🏠  Home": "home", "➕  New Book": "new", "📚  My Library": "library", "ℹ️  How It Works": "howto"}
    for label, pg in pages.items():
        if st.button(label, key=f"nav_{pg}", use_container_width=True):
            st.session_state.page = pg
            do_rerun()

    if st.session_state.books:
        st.markdown("---")
        done = sum(1 for b in st.session_state.books if b.get("status") == "ready")
        st.markdown(f"<div style='color:#d4af37; font-size:0.85rem;'>📚 {len(st.session_state.books)} book(s) · <span style='color:#4caf50;'>✓ {done} done</span></div>", unsafe_allow_html=True)


# ── Pages ─────────────────────────────────────────────────────────────────────
page = st.session_state.page

# ═══════════════ HOME ════════════════════════════════════════════════════════
if page == "home":
    st.markdown("""
    <div class='hero'>
        <h1>BookForge AI</h1>
        <div class='sub'>Automated Book Generation System — powered by Groq + Llama 3.3</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    total = len(st.session_state.books)
    done = sum(1 for b in st.session_state.books if b.get("status") == "ready")
    chapters = sum(len(b.get("chapters", [])) for b in st.session_state.books)
    words = sum(word_count(b) for b in st.session_state.books)
    col1.metric("📚 Books", total)
    col2.metric("✅ Completed", done)
    col3.metric("📄 Chapters", chapters)
    col4.metric("✍️ Words", f"{words:,}")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""<div class='card'>
            <div class='card-title'>⚡ Quick Start</div>
            <p style='color:#aaa; line-height:1.8;'>
            1. Enter your <span style='color:#d4af37;'>Groq API key</span> in the sidebar (free!)<br>
            2. Go to <strong style='color:#f5e6c8;'>New Book</strong> — single or batch Excel<br>
            3. Generate outline → review → generate chapters<br>
            4. Download as <strong style='color:#f5e6c8;'>.TXT</strong> or <strong style='color:#f5e6c8;'>.DOCX</strong>
            </p></div>""", unsafe_allow_html=True)
    with col_b:
        st.markdown("""<div class='card'>
            <div class='card-title'>🧠 AI Engine</div>
            <p style='color:#aaa; line-height:1.9;'>
            🤖 <span style='color:#f5e6c8;'>Llama 3.3 70B</span> via Groq — ultra fast<br>
            📊 <span style='color:#f5e6c8;'>Excel Batch Import</span> — multiple books at once<br>
            🔗 <span style='color:#f5e6c8;'>Context Chaining</span> — consistent narrative<br>
            📝 <span style='color:#f5e6c8;'>DOCX + TXT</span> — professional output<br>
            ✅ <span style='color:#4caf50;'>Works in Pakistan · 100% Free</span>
            </p></div>""", unsafe_allow_html=True)

    if st.session_state.books:
        st.markdown("### 📖 Recent Books")
        for book in reversed(st.session_state.books[-3:]):
            st.markdown(f"""<div class='book-card'>
                <div class='book-title'>{book['title']}</div>
                <div class='book-meta'>{len(book.get('chapters',[]))} chapters · {word_count(book):,} words · <span class='status-{book.get("status","pending")}'>{book.get("status","pending").replace("_"," ").title()}</span></div>
            </div>""", unsafe_allow_html=True)

# ═══════════════ NEW BOOK ═════════════════════════════════════════════════════
elif page == "new":
    st.markdown("<h2 style='font-family:Playfair Display,serif; color:#d4af37;'>✍️ Create New Book</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📝 Single Book", "📊 Batch via Excel"])

    with tab1:
        st.markdown("<div class='step-badge'>Book Details</div>", unsafe_allow_html=True)
        title = st.text_input("Book Title *", placeholder="e.g. The Future of AI in Finance")
        notes = st.text_area("Notes / Focus Areas *",
            placeholder="Describe the book's focus, audience, key themes...\n\nExample: A guide on AI risk management for financial professionals. Cover fraud detection, algorithmic trading, and regulatory compliance.",
            height=120)
        editor_notes = st.text_area("Editor Notes (optional)", placeholder="Style preferences, things to avoid, tone guidance...", height=70)

        if st.button("📚 Add to Library", use_container_width=False):
            if not title.strip() or not notes.strip():
                st.error("Please fill in Title and Notes.")
            else:
                st.session_state.books.append({
                    "id": len(st.session_state.books),
                    "title": title.strip(),
                    "notes": notes.strip(),
                    "editor_notes": editor_notes.strip(),
                    "status": "pending",
                    "outline": None,
                    "chapters": [],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                st.success(f"✅ '{title}' added! Go to Library to generate it.")
                st.session_state.page = "library"
                do_rerun()

    with tab2:
        st.markdown("<div class='step-badge'>Upload Excel File</div>", unsafe_allow_html=True)
        st.markdown("""<div class='card'>
            <div class='card-title'>📋 Required Columns</div>
            <p style='color:#aaa; font-size:0.9rem;'>
            • <code style='color:#d4af37;'>title</code> — Book title (required)<br>
            • <code style='color:#d4af37;'>notes_on_outline_before</code> — Focus areas (required)<br>
            • <code style='color:#d4af37;'>editor_notes</code> — Optional editor guidance
            </p></div>""", unsafe_allow_html=True)

        sample_df = pd.DataFrame({
            "title": ["The Future of AI in Finance", "Blockchain in Banking"],
            "notes_on_outline_before": ["Focus on risk management and fraud detection for financial professionals.", "Explore DeFi, smart contracts, and impact on traditional banking."],
            "editor_notes": ["Include real-world examples", "Add regulatory perspective"]
        })
        buf = io.BytesIO()
        sample_df.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button("⬇️ Download Sample Excel", buf, "sample_books.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx","xls"])
        if uploaded:
            try:
                df = pd.read_excel(uploaded)
                st.success(f"✓ Found {len(df)} books")
                st.dataframe(df, use_container_width=True)
                if st.button("📥 Import All Books"):
                    count = 0
                    for _, row in df.iterrows():
                        t = str(row.get("title","")).strip()
                        n = str(row.get("notes_on_outline_before","")).strip()
                        if t and n and n != "nan":
                            st.session_state.books.append({
                                "id": len(st.session_state.books) + count,
                                "title": t, "notes": n,
                                "editor_notes": str(row.get("editor_notes","")).replace("nan","").strip(),
                                "status": "pending", "outline": None, "chapters": [],
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                            count += 1
                    st.success(f"✅ Imported {count} books!")
                    st.session_state.page = "library"
                    do_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ═══════════════ LIBRARY ══════════════════════════════════════════════════════
elif page == "library":
    st.markdown("<h2 style='font-family:Playfair Display,serif; color:#d4af37;'>📚 Book Library</h2>", unsafe_allow_html=True)

    if not st.session_state.books:
        st.markdown("""<div style='text-align:center; padding:4rem; color:#4a4a4a;'>
            <div style='font-size:3rem; margin-bottom:1rem;'>📭</div>
            <div style='font-family:Playfair Display,serif; font-size:1.3rem; color:#6b6b5a;'>No books yet</div>
            <div style='font-size:0.9rem; margin-top:0.5rem; font-style:italic;'>Go to "New Book" to get started</div>
        </div>""", unsafe_allow_html=True)
    else:
        _, fcol = st.columns([3, 1])
        with fcol:
            sf = st.selectbox("Filter", ["All", "pending", "outline_ready", "generating", "ready"])

        books_to_show = st.session_state.books if sf == "All" else [b for b in st.session_state.books if b.get("status") == sf]
        st.markdown(f"<div style='color:#6b6b5a; font-size:0.85rem; margin-bottom:1rem; font-style:italic;'>Showing {len(books_to_show)} of {len(st.session_state.books)} books</div>", unsafe_allow_html=True)

        for book in books_to_show:
            real_idx = st.session_state.books.index(book)
            status = book.get("status", "pending")

            with st.expander(f"📖  {book['title']}   ·   {len(book.get('chapters',[]))} chapters   ·   {word_count(book):,} words", expanded=False):
                hcol1, hcol2, hcol3 = st.columns([2, 1, 1])
                with hcol1:
                    st.markdown(f"<span class='status-{status}'>{status.replace('_',' ').title()}</span> &nbsp; <span style='color:#6b6b5a; font-size:0.8rem;'>{book.get('created_at','-')}</span>", unsafe_allow_html=True)
                with hcol3:
                    if st.button("🗑️ Delete", key=f"del_{real_idx}"):
                        st.session_state.books.pop(real_idx)
                        do_rerun()

                st.markdown("---")

                # ── STAGE 1: Pending → Generate Outline ──────────────────────
                if status == "pending":
                    st.markdown("<div class='step-badge'>Stage 1 — Generate Outline</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color:#aaa; font-size:0.9rem; margin:8px 0;'><strong style='color:#d4af37;'>Notes:</strong> {book['notes'][:250]}{'...' if len(book['notes'])>250 else ''}</div>", unsafe_allow_html=True)

                    if st.button("⚡ Generate Outline", key=f"outline_{real_idx}"):
                        if not st.session_state.api_key:
                            st.error("Add your Groq API key in the sidebar!")
                        else:
                            with st.spinner("✨ Generating outline with Llama 3.3..."):
                                try:
                                    outline = generate_outline(st.session_state.api_key, book["title"], book["notes"])
                                    st.session_state.books[real_idx]["outline"] = outline
                                    st.session_state.books[real_idx]["status"] = "outline_ready"
                                    do_rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                # ── STAGE 2: Outline ready → Review & Generate Chapters ───────
                elif status in ["outline_ready", "generating"]:
                    outline = book.get("outline", {})
                    st.markdown("<div class='step-badge'>Stage 2 — Review Outline & Generate</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='chapter-box'><strong style='color:#d4af37;'>📖 Book Description:</strong><br>{outline.get('description','')}</div>", unsafe_allow_html=True)

                    st.markdown("<div style='color:#aaa; font-size:0.9rem; margin:1rem 0 0.5rem;'>📋 Chapters:</div>", unsafe_allow_html=True)
                    for ch in outline.get("chapters", []):
                        st.markdown(f"""<div style='background:#111; border-left:3px solid #2a2a2a; padding:8px 12px; margin:4px 0; border-radius:4px;'>
                            <span style='color:#d4af37; font-family:Playfair Display,serif;'>Ch {ch['number']}.</span>
                            <span style='color:#f5e6c8; margin-left:6px; font-weight:600;'>{ch['title']}</span>
                            <div style='color:#777; font-size:0.8rem; margin-top:2px; font-style:italic;'>{ch['description']}</div>
                        </div>""", unsafe_allow_html=True)

                    extra = st.text_area("Additional notes before generating chapters (optional):", key=f"en_{real_idx}", height=60, placeholder="Any extra guidance for chapter writing...")

                    col_g1, col_g2 = st.columns([1, 2])
                    with col_g1:
                        gen_btn = st.button("📖 Generate All Chapters", key=f"gen_{real_idx}", use_container_width=True)
                    with col_g2:
                        if st.button("🔄 Regenerate Outline", key=f"regen_{real_idx}"):
                            st.session_state.books[real_idx]["status"] = "pending"
                            st.session_state.books[real_idx]["outline"] = None
                            do_rerun()

                    if gen_btn:
                        if not st.session_state.api_key:
                            st.error("Add your Groq API key in the sidebar!")
                        else:
                            st.session_state.books[real_idx]["status"] = "generating"
                            chapters_data = outline.get("chapters", [])
                            progress = st.progress(0)
                            status_txt = st.empty()
                            generated = []
                            prev_summaries = []
                            try:
                                for i, ch in enumerate(chapters_data):
                                    status_txt.markdown(f"<div style='color:#d4af37; font-style:italic;'>✍️ Writing Chapter {ch['number']}: {ch['title']}...</div>", unsafe_allow_html=True)
                                    content, summary = generate_chapter(
                                        st.session_state.api_key, book["title"],
                                        outline.get("description",""),
                                        ch["number"], ch["title"], ch["description"],
                                        prev_summaries, extra
                                    )
                                    generated.append({"number": ch["number"], "title": ch["title"], "content": content, "summary": summary})
                                    prev_summaries.append({"num": ch["number"], "summary": summary})
                                    progress.progress((i + 1) / len(chapters_data))
                                    time.sleep(0.3)

                                st.session_state.books[real_idx]["chapters"] = generated
                                st.session_state.books[real_idx]["status"] = "ready"
                                status_txt.markdown("<div style='color:#4caf50;'>✅ All chapters generated!</div>", unsafe_allow_html=True)
                                time.sleep(1)
                                do_rerun()
                            except Exception as e:
                                st.session_state.books[real_idx]["status"] = "outline_ready"
                                st.error(f"Error: {e}")

                # ── STAGE 3: Ready → Download ──────────────────────────────────
                elif status == "ready":
                    st.markdown("<div class='step-badge'>Stage 3 — Download Your Book ✅</div>", unsafe_allow_html=True)
                    wc = word_count(book)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Chapters", len(book.get("chapters",[])))
                    m2.metric("Words", f"{wc:,}")
                    m3.metric("Est. Pages", f"~{wc//250}")

                    st.markdown("<div style='margin:1rem 0 0.5rem; color:#d4af37; font-family:Playfair Display,serif;'>📖 Preview a Chapter</div>", unsafe_allow_html=True)
                    ch_labels = [f"Ch {c['number']}: {c['title']}" for c in book.get("chapters",[])]
                    sel = st.selectbox("", ch_labels, key=f"prev_{real_idx}", label_visibility="collapsed")
                    cidx = int(sel.split(":")[0].replace("Ch","").strip()) - 1
                    st.markdown(f"<div class='chapter-box'>{book['chapters'][cidx]['content'][:800]}...</div>", unsafe_allow_html=True)

                    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button("⬇️ Download .TXT", create_txt(book),
                            f"{book['title'].replace(' ','_')}.txt", "text/plain",
                            key=f"txt_{real_idx}", use_container_width=True)
                    with d2:
                        try:
                            docx_buf = create_docx(book)
                            st.download_button("⬇️ Download .DOCX", docx_buf,
                                f"{book['title'].replace(' ','_')}.docx",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"docx_{real_idx}", use_container_width=True)
                        except Exception:
                            st.info("DOCX unavailable — install python-docx")

                elif status == "error":
                    st.error("Generation failed. Try resetting.")
                    if st.button("🔄 Reset", key=f"reset_{real_idx}"):
                        st.session_state.books[real_idx]["status"] = "pending"
                        do_rerun()

# ═══════════════ HOW IT WORKS ═════════════════════════════════════════════════
elif page == "howto":
    st.markdown("<h2 style='font-family:Playfair Display,serif; color:#d4af37;'>ℹ️ How It Works</h2>", unsafe_allow_html=True)
    steps = [
        ("🔑", "1. Get Free API Key", "Sign up at console.groq.com → create an API key (starts with gsk_). It's 100% free, works globally including Pakistan, and gives you 14,400 requests/day."),
        ("📝", "2. Add Your Books", "Enter a title and focus notes manually, or upload an Excel file with multiple books for batch processing."),
        ("🧠", "3. Generate Outline", "Llama 3.3 70B creates a structured outline with chapter titles and descriptions. Review it before generating chapters."),
        ("✍️", "4. Generate Chapters", "Each chapter is written in sequence. The AI uses context chaining — every chapter is aware of the previous ones for a coherent narrative."),
        ("⬇️", "5. Download", "Download your finished book as .TXT or .DOCX Word document."),
    ]
    for icon, title, desc in steps:
        st.markdown(f"""<div class='card' style='display:flex; gap:1.2rem; align-items:flex-start;'>
            <div style='font-size:2rem; flex-shrink:0;'>{icon}</div>
            <div><div class='card-title'>{title}</div>
            <div style='color:#aaa; font-size:0.95rem; line-height:1.7;'>{desc}</div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""<div class='card'>
        <div class='card-title'>🔗 Context Chaining Explained</div>
        <p style='color:#aaa; line-height:1.8;'>After each chapter is written, the AI generates a short summary.
        When writing the next chapter, all previous summaries are sent as context — so the AI maintains
        continuity, remembers character names, plot points, and themes. The result is a coherent,
        professional-quality book rather than disconnected chapters.</p>
    </div>""", unsafe_allow_html=True)