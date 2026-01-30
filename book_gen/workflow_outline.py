from __future__ import annotations

from typing import List

from .config import AppConfig
from .db import Book, Database
from .llm import LLMClient
from .notifications import Notifier


class OutlineWorkflow:
    def __init__(self, cfg: AppConfig, db: Database, llm: LLMClient, notifier: Notifier) -> None:
        self.cfg = cfg
        self.db = db
        self.llm = llm
        self.notifier = notifier

    def run(self) -> None:
        books = self.db.get_books_for_outline_generation()
        for book in books:
            try:
                self._process_book(book)
            except Exception as exc:  # noqa: BLE001
                # Print error so it's visible in CLI, and also send notification.
                print(f"[ERROR] Outline stage failed for book '{book.title}': {exc}")
                self.notifier.notify_error("outline_stage", f"Book '{book.title}': {exc}")

    def _process_book(self, book: Book) -> None:
        # Logic: Only generate outlines if notes_on_outline_before exists.
        if not book.notes_on_outline_before:
            # Pause: missing required notes
            self.db.update_book_status(book.id, book_output_status="paused_missing_outline_notes")
            self.notifier.notify_error(
                "outline_stage",
                f"Cannot generate outline for '{book.title}' because notes_on_outline_before is empty.",
            )
            return

        outline = self.llm.generate_outline(
            title=book.title,
            notes_before=book.notes_on_outline_before,
            notes_after=book.notes_on_outline_after,
        )

        self.db.update_book_outline(book.id, outline)
        self.db.log_outline_version(
            book_id=book.id,
            outline=outline,
            notes_on_outline_before=book.notes_on_outline_before,
            notes_on_outline_after=book.notes_on_outline_after,
        )

        # After outline: check status_outline_notes
        status = (book.status_outline_notes or "").strip().lower()
        if status == "yes":
            # Wait for notes from editor
            self.db.update_book_status(book.id, book_output_status="waiting_outline_notes")
            self.notifier.notify_outline_ready(book.title)
        elif status == "no_notes_needed":
            # Proceed (chapters will be generated when chapter workflow is run)
            self.db.update_book_status(book.id, book_output_status="ready_for_chapters")
            self.notifier.notify_outline_ready(book.title)
        else:
            # "no" or empty -> pause
            self.db.update_book_status(book.id, book_output_status="paused_outline_status")
            self.notifier.notify_error(
                "outline_stage",
                f"Outline generated for '{book.title}', but status_outline_notes is '{book.status_outline_notes}'.",
            )