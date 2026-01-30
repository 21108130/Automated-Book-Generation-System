# final_status.py
from book_gen.config import load_config
from book_gen.db import Database

cfg = load_config()
db = Database(cfg)
books = db.get_books()

print('🏁 FINAL WORKFLOW STATUS REPORT')
print('=' * 60)

total_chapters = 0
total_content_chars = 0

for b in books:
    chapters = db.get_chapters_for_book(b.id)
    chapter_count = len(chapters)
    content_chars = sum(len(ch.get('content', '')) for ch in chapters)
    
    total_chapters += chapter_count
    total_content_chars += content_chars
    
    print(f'\n📘 {b.title}')
    print(f'   ├─ Outline: {len(b.outline or ""):,} chars')
    print(f'   ├─ Chapters: {chapter_count}')
    print(f'   ├─ Total content: {content_chars:,} chars')
    print(f'   └─ Output status: {b.book_output_status or "pending"}')

print(f'\n{"=" * 60}')
print(f'📈 SYSTEM TOTALS:')
print(f'   • Books processed: {len(books)}')
print(f'   • Total chapters: {total_chapters}')
print(f'   • Total content: {total_content_chars:,} characters')
print(f'   • Average per book: {total_chapters/len(books):.1f} chapters')
print(f'   • Average length: {total_content_chars/len(books):,.0f} chars/book')