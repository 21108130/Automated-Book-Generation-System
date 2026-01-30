# Automated Book Generation System

This project is a **modular, Supabase-backed, LLM-powered book generation system** that demonstrates:

- **Input + Outline Stage** with human-in-the-loop notes and gating
- **Chapter Generation Stage** with **context-chained chapter summaries** and notes-based regeneration
- **Final Compilation Stage** into `.txt` (and optionally `.docx`) with gating and notifications
- **Supabase** used as the system-of-record for books, outlines, chapters, notes, and statuses
- **Excel input**, **SMTP email** and **MS Teams webhook** notifications

---

## Tech Stack

- **Automation Engine:** Python 3 scripts (CLI orchestrator)
- **Database:** Supabase (PostgreSQL) via `supabase-py`
- **AI Model:** OpenAI Chat Completion models (e.g. `gpt-4.1`, configurable)
- **Input Source:** Local Excel (`.xlsx`) via `pandas` + `openpyxl`
- **Notifications:**
  - Email via SMTP
  - MS Teams via incoming webhook
- **Output Files:**
  - Per-chapter text stored in Supabase
  - Final book exported as `.txt` (and optionally `.docx`) to local `outputs/`

You can easily swap out the LLM provider or DB by replacing the adapters in `book_gen/llm.py` and `book_gen/db.py`.

---

## Project Layout

```text
.
├── README.md
├── requirements.txt
├── config_example.yaml
├── main.py
└── book_gen/
    ├── __init__.py
    ├── config.py
    ├── db.py
    ├── llm.py
    ├── models.py
    ├── input_excel.py
    ├── notifications.py
    ├── workflow_outline.py
    ├── workflow_chapters.py
    └── workflow_compile.py
```

You will also create:

- `outputs/` directory for compiled books
- An Excel file for input, e.g. `inputs/books.xlsx`

---

## Supabase Schema

Create these tables (SQL definitions can be run in Supabase SQL editor).

### `books`

```sql
create table public.books (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  notes_on_outline_before text,
  outline text,
  notes_on_outline_after text,
  status_outline_notes text check (status_outline_notes in ('yes','no','no_notes_needed')),
  final_review_notes text,
  final_review_notes_status text check (final_review_notes_status in ('yes','no','no_notes_needed')),
  book_output_status text default 'pending',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index books_title_idx on public.books (title);
```

### `chapters`

```sql
create table public.chapters (
  id uuid primary key default gen_random_uuid(),
  book_id uuid references public.books(id) on delete cascade,
  chapter_number int not null,
  chapter_title text,
  content text,
  summary text,
  chapter_notes text,
  chapter_notes_status text check (chapter_notes_status in ('yes','no','no_notes_needed')),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (book_id, chapter_number)
);

create index chapters_book_idx on public.chapters (book_id);
```

### `outline_versions` (optional but useful)

```sql
create table public.outline_versions (
  id uuid primary key default gen_random_uuid(),
  book_id uuid references public.books(id) on delete cascade,
  outline text not null,
  notes_on_outline_before text,
  notes_on_outline_after text,
  created_at timestamptz default now()
);
```

---

## Configuration

Copy `config_example.yaml` to `config.yaml` and fill in your values:

```bash
cp config_example.yaml config.yaml
```

Key sections:

- **supabase:** URL and anon/service key
- **openai:** API key and model name
- **notifications:** SMTP + Teams webhook

You can also override via environment variables if you prefer (`SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY`, etc.).

---

## Installation

```bash
pip install -r requirements.txt
```

Ensure Python 3.10+ is used for best compatibility.

---

## Excel Input Format

Create an Excel file, e.g. `inputs/books.xlsx`, with at least these columns in the **first sheet**:

- `title` (string, mandatory)
- `notes_on_outline_before` (string, required before generating outline)
- `status_outline_notes` (one of: `yes`, `no`, `no_notes_needed`)

Example first row:

| title                         | notes_on_outline_before                 | status_outline_notes |
|------------------------------|------------------------------------------|----------------------|
| The Future of AI in Finance  | Focus on risk management and regulation. | yes                  |

You can then let editors add **outline** and **notes_on_outline_after** from the DB/UI side, or by updating fields in Supabase console.

---

## CLI Workflows

Run commands from the project root (`e:\GB`). Examples assume `python` is Python 3.

### 1. Import books from Excel

```bash
python main.py import-from-excel --excel-path inputs/books.xlsx
```

This will insert/update `books` records in Supabase.

### 2. Generate outlines

```bash
python main.py generate-outlines
```

Logic per book:

- Only generate outline if:
  - `notes_on_outline_before` exists (non-empty), and
  - `outline` is empty.
- After generation, check `status_outline_notes`:
  - `yes`  → system sets book as **waiting** for post-outline notes; no chapters generated.
  - `no` or empty → system **pauses**; needs explicit status update.
  - `no_notes_needed` → proceed directly to chapter generation step (when you run it).

Editors can then:

- Add `notes_on_outline_after` and tweak `status_outline_notes` in Supabase.
- You can re-run `generate-outlines` to regenerate when notes change.

### 3. Generate chapters

```bash
python main.py generate-chapters
```

Logic per book:

- Uses `outline` as the source of chapters.
- For chapter **N**, the prompt receives:
  - Book `title`
  - Full `outline`
  - A concatenated summary of chapters `1..N-1` from `chapters.summary`.
- Gating per chapter:
  - If `chapter_notes_status = 'yes'`: system waits for notes, does **not** regenerate yet.
  - If `chapter_notes_status = 'no_notes_needed'`: proceeds or finalizes chapter.
  - If `chapter_notes_status` is `no` or empty: system **pauses** for that chapter.

Editors can:

- Add/update `chapter_notes` and `chapter_notes_status` in `chapters` table.
- Re-run `generate-chapters` to regenerate based on new notes.

### 4. Compile final book

```bash
python main.py compile-books
```

Logic:

- Compiles only if for a given book:
  - `final_review_notes_status = 'no_notes_needed'` **OR**
  - `final_review_notes` is non-empty.
- Orders chapters by `chapter_number` and concatenates `content`.
- Writes a `.txt` file to `outputs/BOOK_ID.txt` (and optionally `.docx` if enabled in config).
- Updates `book_output_status` to `ready`.

---

## Notifications

Integrated in `book_gen/notifications.py`. Triggered events:

- **Outline ready for review**
- **Waiting for chapter notes**
- **Final draft compiled**
- **Error or pause due to missing input**

You can configure:

- `notifications.email.enabled` and SMTP details
- `notifications.teams.enabled` and `webhook_url`

---

## LLM Usage and Context

The system uses a simple but explicit prompt layering:

- **Outline generation prompt:** uses `title` and `notes_on_outline_before` (and later `notes_on_outline_after` when regenerating) to generate a structured outline.
- **Chapter generation prompt:** uses:
  - Book title
  - Entire outline
  - Summaries of all previous chapters
  - Optional chapter-specific notes

Example chapter prompt skeleton (implemented in `workflow_chapters.py`):

> "Using the following chapter summaries, write Chapter N of the book titled X..."

Summaries are stored in `chapters.summary` and reused on regeneration.

---

## Source-backed Research (Optional Extensions)

The code includes clear extension points (TODO markers) where you can:

- Call web search APIs (SerpAPI, Brave Search, Bing) and inject source snippets into the LLM prompt.
- Pull external data via scraping workflows (n8n + Browserless, Puppeteer, etc.), store into Supabase or a vector DB, and fetch relevant snippets.
- Use OpenAI models with web search enabled.

These are left as stubs to keep this trial self-contained, but the architecture supports them via dedicated helpers in `llm.py`.

---

## How to Demo (for your Loom video)

Suggested flow for your recording:

1. **Explain the architecture** (show `README.md`, `config_example.yaml`, and the `book_gen/` modules).
2. **Show Supabase tables** (`books`, `chapters`) and their columns.
3. **Import from Excel** and point at the new rows in Supabase.
4. **Run outline generation** and show how `outline` is saved and how `status_outline_notes` controls gating.
5. **Simulate editor notes** by updating fields in Supabase and re-running.
6. **Run chapter generation**, explain how context chaining with summaries works.
7. **Compile final draft**, open the `.txt` output file.
8. **Show email / Teams notifications** (even if using a test inbox / test channel).

---

## Stack Summary for Submission

- **Automation:** Python 3 CLI scripts
- **DB:** Supabase (PostgreSQL) via `supabase-py`
- **LLM:** OpenAI GPT models via `openai` Python SDK
- **Input:** Local Excel using `pandas` + `openpyxl`
- **Notifications:** SMTP email + MS Teams Webhook via `requests`
- **Outputs:** Per-chapter in Supabase, final book as `.txt` (and optional `.docx`) in `outputs/`

You can zip this folder, push to GitHub, or share as requested along with:

- A screenshot of the DB structure
- Sample output file from `outputs/`
- Any additional screenshots of the flows.
