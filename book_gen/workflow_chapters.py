from __future__ import annotations

from typing import List

from .config import AppConfig
from .db import Book, Database
from .llm import LLMClient
from .notifications import Notifier


class ChapterWorkflow:
    def __init__(self, cfg: AppConfig, db: Database, llm: LLMClient, notifier: Notifier) -> None:
        self.cfg = cfg
        self.db = db
        self.llm = llm
        self.notifier = notifier

    def run(self) -> None:
        books: List[Book] = self.db.get_books_for_chapter_generation()
        for book in books:
            try:
                self._process_book(book)
            except Exception as exc:  # noqa: BLE001
                self.notifier.notify_error("chapter_stage", f"Book '{book.title}': {exc}")

    def _process_book(self, book: Book) -> None:
        # Fetch existing chapters for context chaining
        chapters = self.db.get_chapters_for_book(book.id)
        summaries = [c.get("summary") or "" for c in chapters if c.get("summary")]

        # If no chapters exist yet, derive chapter titles from outline
        if not chapters:
            outline_lines = (book.outline or "").splitlines()
            chapter_titles: List[str] = []
            for ln in outline_lines:
                stripped = ln.strip()
                if not stripped:
                    continue
                # Primary heuristic: lines starting with digit or '-' are chapter-like
                if stripped[0].isdigit() or stripped.startswith("-"):
                    cleaned = stripped.lstrip("- ")
                    if ". " in cleaned:
                        cleaned = cleaned.split(". ", 1)[1]
                    chapter_titles.append(cleaned)

            # Fallback: if we failed to detect chapter-like lines, treat the whole
            # outline as a single chapter so that the pipeline still produces output.
            if not chapter_titles:
                chapter_titles = [book.title]

            for idx, title in enumerate(chapter_titles, start=1):
                self._generate_or_regenerate_chapter(
                    book=book,
                    chapter_number=idx,
                    chapter_title=title,
                    existing_chapters=chapters,
                    previous_summaries=summaries[: idx - 1],
                )
        else:
            # Regeneration path: look at chapters that are missing content or have notes
            for ch in chapters:
                chapter_notes_status = (ch.get("chapter_notes_status") or "").strip().lower()
                if chapter_notes_status == "yes":
                    # Wait for notes - notify and skip
                    self.notifier.notify_waiting_chapter_notes(book.title, ch["chapter_number"])
                    continue
                if chapter_notes_status in {"", "no"}:
                    # Pause, do not proceed
                    continue

                # no_notes_needed or explicitly ready: (re)generate chapter
                self._generate_or_regenerate_chapter(
                    book=book,
                    chapter_number=ch["chapter_number"],
                    chapter_title=ch.get("chapter_title") or f"Chapter {ch['chapter_number']}",
                    existing_chapters=chapters,
                    previous_summaries=[
                        c.get("summary") or ""
                        for c in chapters
                        if c["chapter_number"] < ch["chapter_number"] and c.get("summary")
                    ],
                    existing_chapter_row=ch,
                )

    def _generate_or_regenerate_chapter(
        self,
        book: Book,
        chapter_number: int,
        chapter_title: str,
        existing_chapters: List[dict],
        previous_summaries: List[str],
        existing_chapter_row: dict | None = None,
    ) -> None:
        chapter_notes = None
        chapter_notes_status = None
        if existing_chapter_row:
            chapter_notes = existing_chapter_row.get("chapter_notes")
            chapter_notes_status = (existing_chapter_row.get("chapter_notes_status") or "").strip().lower()

        # Gating rules
        if chapter_notes_status == "yes":
            self.notifier.notify_waiting_chapter_notes(book.title, chapter_number)
            return
        if chapter_notes_status in {"", "no"}:
            # Pause until explicitly updated
            return

        text = self.llm.generate_chapter(
            title=book.title,
            outline=book.outline or "",
            chapter_title=chapter_title,
            chapter_number=chapter_number,
            previous_summaries=previous_summaries,
            chapter_notes=chapter_notes,
        )
        summary = self.llm.summarize_chapter(text)

        self.db.upsert_chapter(
            book_id=book.id,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            content=text,
            summary=summary,
        )