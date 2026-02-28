# Automated Book Generation System 📚🤖

A modular, scalable, and AI-powered system that automates the entire book generation process — from title to compiled manuscript. This system integrates Supabase for data management, **Groq API (Llama 3.3 70B)** for ultra-fast content generation, and supports human-in-the-loop feedback at every stage.

> ⚠️ **Migration Notice:** This project previously used Google Gemini API. Due to reliability issues with the Gemini key, the AI backend has been switched to **Groq API** (powered by Llama 3.3 70B). Groq is free, fast, and works globally — including Pakistan. Please follow the updated setup instructions below.

---

## 🌟 Features

### ✅ **Complete Workflow Automation**

* **Stage 1:** Excel Import → Outline Generation
* **Stage 2:** Outline → Chapter Generation with Context Chaining
* **Stage 3:** Chapters → Final Book Compilation

### ✅ **Human-in-the-Loop Design**

* Editors can add notes before/after outline generation
* Chapter-by-chapter review and feedback system
* Conditional gating logic at every stage

### ✅ **Smart AI Integration**

* **Groq API + Llama 3.3 70B** for high-quality, ultra-fast content generation
* Context chaining between chapters
* Configurable temperature and token limits

### ✅ **Professional Output**

* Generates `.txt` files (mandatory)
* Optional `.docx` Word document generation
* Clean, formatted book structure

---

## 🏗️ System Architecture

```
📁 Book Generation System
├── 📊 config.py              # Configuration management
├── 🗄️ db.py                 # Supabase database operations
├── 🧠 llm.py                # Groq API integration (Llama 3.3 70B)
├── 📥 input_excel.py        # Excel file import
├── 🔔 notifications.py      # Email/Teams notifications
├── 📝 workflow_outline.py   # Outline generation
├── 📖 workflow_chapters.py  # Chapter generation
├── 📑 workflow_compile.py   # Book compilation
├── 🎯 main.py               # CLI controller
└── ⚙️ config.yaml           # Settings file
```

---

## 📋 Prerequisites

### **Software Requirements**

* Python 3.10+
* Supabase account
* **Groq API key** (free at [console.groq.com](https://console.groq.com))
* SMTP credentials (for email notifications, optional)
* MS Teams webhook URL (optional)

### **Python Dependencies**

```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### **1. Clone and Setup**

```bash
git clone https://github.com/21108130/Automated-Book-Generation-System.git
cd Automated-Book-Generation-System
pip install -r requirements.txt
```

### **2. Get Your Free Groq API Key**

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up / log in
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key — it starts with `gsk_`

> ✅ Groq is **100% free**, requires no billing setup, and works globally including Pakistan (14,400 requests/day on the free tier).

### **3. Configure Settings**

```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your credentials
```

### **4. Set Up Database**

Run these SQL commands in Supabase:

```sql
-- Create books table
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    notes_on_outline_before TEXT,
    outline TEXT,
    notes_on_outline_after TEXT,
    status_outline_notes TEXT CHECK (status_outline_notes IN ('yes','no','no_notes_needed')),
    final_review_notes TEXT,
    final_review_notes_status TEXT CHECK (final_review_notes_status IN ('yes','no','no_notes_needed')),
    book_output_status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create chapters table
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INT NOT NULL,
    chapter_title TEXT,
    content TEXT,
    summary TEXT,
    chapter_notes TEXT,
    chapter_notes_status TEXT CHECK (chapter_notes_status IN ('yes','no','no_notes_needed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (book_id, chapter_number)
);
```

### **5. Create Excel Input File**

Create `inputs/books.xlsx` with these columns:

* `title` (mandatory)
* `notes_on_outline_before` (required for outline generation)
* `status_outline_notes` (yes/no/no\_notes\_needed)

Example:

```
title,notes_on_outline_before,status_outline_notes
The Future of AI in Finance,Focus on risk management...,yes
Blockchain Revolution in Banking,Explore DeFi and smart contracts...,no_notes_needed
```

---

## ⚙️ Configuration

### **Environment Variables (Recommended)**

```bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
export GROQ_API_KEY="gsk_..."          # Groq API key (replaces GEMINI_API_KEY)
export GROQ_MODEL="llama-3.3-70b-versatile"
export SMTP_PASSWORD="your_smtp_password"
```

### **Config File (`config.yaml`)**

```yaml
supabase:
  url: ""  # Use env var SUPABASE_URL
  key: ""  # Use env var SUPABASE_KEY

groq:
  api_key: ""                      # Use env var GROQ_API_KEY
  model: "llama-3.3-70b-versatile" # Use env var GROQ_MODEL

notifications:
  email:
    enabled: false
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    use_tls: true
    username: "your-email@gmail.com"
    password: ""  # Use env var SMTP_PASSWORD
    from_address: "noreply@example.com"
    to_addresses:
      - "editor@example.com"

output:
  base_dir: "outputs"
  generate_docx: false

llm:
  temperature: 0.7
  max_tokens: 2000
```

---

## 📖 Usage

### **Complete Workflow**

```bash
# 1. Import books from Excel
python main.py import-from-excel --excel-path inputs/books.xlsx

# 2. Generate outlines
python main.py generate-outlines

# 3. Generate chapters
python main.py generate-chapters

# 4. Compile final books
python main.py compile-books
```

### **Individual Commands**

```bash
python main.py import-from-excel --excel-path <path>
python main.py generate-outlines
python main.py generate-chapters
python main.py compile-books
```

---

## 🔄 Workflow Logic

### **Outline Generation**

```
graph TD
    A[Excel Input] --> B{notes_on_outline_before exists?}
    B -->|Yes| C[Generate Outline with Groq / Llama 3.3]
    B -->|No| D[Pause - Missing Notes]
    C --> E{Check status_outline_notes}
    E -->|yes| F[Wait for Editor Notes]
    E -->|no_notes_needed| G[Proceed to Chapters]
    E -->|no/empty| H[Pause - Status Update Needed]
```

### **Chapter Generation**

```
graph TD
    A[Book Outline] --> B[Extract Chapter Titles]
    B --> C[For each chapter]
    C --> D{chapter_notes_status?}
    D -->|yes| E[Wait for Notes - Notify Editor]
    D -->|no_notes_needed| F[Generate Chapter via Groq]
    D -->|no/empty| G[Pause - Status Update]
    F --> H[Store Chapter + Summary]
    H --> I[Use Summary for Next Chapter]
```

### **Compilation**

```
graph TD
    A[All Chapters Ready] --> B{final_review_notes_status?}
    B -->|no_notes_needed| C[Compile Book]
    B -->|has notes| C
    B -->|no/empty| D[Pause - Needs Notes]
    C --> E[Generate .txt/.docx Files]
    E --> F[Update Status to 'ready']
```

---

## 📊 Database Schema

### **Books Table**

| Column | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key |
| title | TEXT | Book title |
| notes\_on\_outline\_before | TEXT | Notes before outline generation |
| outline | TEXT | Generated book outline |
| notes\_on\_outline\_after | TEXT | Editor notes after outline |
| status\_outline\_notes | ENUM | yes/no/no\_notes\_needed |
| final\_review\_notes | TEXT | Final editor notes |
| final\_review\_notes\_status | ENUM | yes/no/no\_notes\_needed |
| book\_output\_status | TEXT | Current book status |

### **Chapters Table**

| Column | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key |
| book\_id | UUID | Foreign key to books |
| chapter\_number | INT | Chapter sequence |
| chapter\_title | TEXT | Chapter title |
| content | TEXT | Generated chapter content |
| summary | TEXT | Chapter summary for context |
| chapter\_notes | TEXT | Editor notes for chapter |
| chapter\_notes\_status | ENUM | yes/no/no\_notes\_needed |

---

## 🔔 Notifications

The system can send notifications via:

* **Email** (SMTP)
* **Microsoft Teams** (Webhooks)

**Trigger Events:**

* Outline ready for review
* Waiting for chapter notes
* Final draft compiled
* Error or pause due to missing input

---

## 🧪 Testing

### **Test Scripts Included**

```bash
# Create sample Excel file
python create_sample_excel.py

# Test database connection
python -c "from book_gen.config import load_config; from book_gen.db import Database; cfg=load_config(); db=Database(cfg); print(f'Connected: {len(db.get_books())} books')"

# Test Groq API connection
python -c "
import requests
res = requests.post('https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': 'Bearer YOUR_GROQ_KEY', 'Content-Type': 'application/json'},
    json={'model': 'llama-3.3-70b-versatile', 'max_tokens': 10, 'messages': [{'role': 'user', 'content': 'Hello'}]}
)
print('Groq OK:', res.json()['choices'][0]['message']['content'])
"
```

### **Sample Output**

```
✅ System Status:
   • 3 Books Processed
   • 6 Total Chapters
   • 27,830 Characters Generated
   • 3 Output Files Created
```

---

## 🚀 Advanced Features

### **Context Chaining**

* Each chapter generation includes summaries of all previous chapters
* Maintains consistency and flow throughout the book
* Summaries stored in database for regeneration

### **Regeneration Support**

* Editors can add notes to any stage
* System can regenerate outlines/chapters with new notes
* All versions logged for audit trail

### **Modular Design**

* AI backend swappable — currently using Groq (Llama 3.3 70B)
* Configurable database backend
* Pluggable notification systems

---

## 📁 Project Structure

```
.
├── README.md
├── requirements.txt
├── config.yaml
├── config.yaml.example
├── main.py
├── create_sample_excel.py
├── inputs/
│   └── books.xlsx
├── outputs/
│   ├── book1.txt
│   ├── book2.txt
│   └── book3.txt
└── book_gen/
    ├── __init__.py
    ├── config.py
    ├── db.py
    ├── llm.py                # Groq API integration
    ├── input_excel.py
    ├── notifications.py
    ├── workflow_outline.py
    ├── workflow_chapters.py
    └── workflow_compile.py
```

---

## 🔧 Troubleshooting

### **Common Issues**

1. **"Config file not found"**
   ```bash
   cp config.yaml.example config.yaml
   ```

2. **Groq API errors**
   * Verify your API key starts with `gsk_`
   * Get a free key at [console.groq.com](https://console.groq.com)
   * Confirm model name is `llama-3.3-70b-versatile`
   * Check your daily rate limit (14,400 requests/day on free tier)

3. **Database connection errors**
   * Verify Supabase URL and key
   * Check if tables are created via `schema.sql`
   * Ensure network connectivity

4. **No output files**
   * Check if chapters were generated
   * Verify `final_review_notes_status` is set
   * Check `outputs/` folder permissions

5. **"RerunData fragment" error (Streamlit app)**
   * Upgrade Streamlit: `pip install --upgrade streamlit`
   * Or replace all `st.rerun()` calls with `st.rerun(scope="app")`

### **Debug Mode**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📈 Performance Metrics

**Test Results (Groq / Llama 3.3 70B):**

* Success Rate: 100% (3/3 books)
* Average Book Size: 9,277 characters
* Average Chapters per Book: 2.0
* Total Content Generated: 27,830 characters
* Output File Sizes: 5.6KB – 14.6KB
* Average generation speed: ~2–4 seconds per chapter (Groq is extremely fast)

---

## 🎯 Future Enhancements

* Web-based editor interface (Streamlit app — see `app.py`)
* PDF export support
* Version control system
* Multi-language support
* Advanced AI model switching (OpenAI, Anthropic, etc.)
* Web search API integration for research-backed books
* Source citation and fact-checking module

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.

---

## 🙏 Acknowledgments

* **Groq** for providing a free, ultra-fast LLM inference API
* **Meta / Llama 3.3 70B** for the underlying language model
* **Supabase** for the database backend
* **Python community** for excellent libraries

---

## 📞 Support

For issues and questions:

1. Check the Troubleshooting section above
2. Review the code documentation
3. Open an issue on GitHub

---

## webstite link
https://automated-book-generation-system-exr9fej3amj39rc4ly2xre.streamlit.app/
