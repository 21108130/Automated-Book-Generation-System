from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from .config import AppConfig


@dataclass
class Book:
    id: str
    title: str
    notes_on_outline_before: Optional[str]
    outline: Optional[str]
    notes_on_outline_after: Optional[str]
    status_outline_notes: Optional[str]
    final_review_notes: Optional[str]
    final_review_notes_status: Optional[str]
    book_output_status: Optional[str]


class Database:
    def __init__(self, cfg: AppConfig) -> None:
        self.client: Client = create_client(cfg.supabase.url, cfg.supabase.key)

    # --- Books ---
    def upsert_book_from_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert book using title as natural key from Excel row."""
        title = row.get("title")
        if not title:
            raise ValueError("Row missing required 'title'")

        payload = {
            "title": title,
            "notes_on_outline_before": row.get("notes_on_outline_before"),
            "status_outline_notes": row.get("status_outline_notes"),
        }

        # Manual upsert: check if a book with this title exists, then update or insert.
        existing = (
            self.client.table("books")
            .select("id")
            .eq("title", title)
            .limit(1)
            .execute()
        ).data

        if existing:
            book_id = existing[0]["id"]
            self.client.table("books").update(payload).eq("id", book_id).execute()
        else:
            self.client.table("books").insert(payload).execute()

        res = (
            self.client.table("books")
            .select("*")
            .eq("title", title)
            .limit(1)
            .execute()
        )
        return res.data[0]

    def get_books_for_outline_generation(self) -> List[Book]:
        res = (
            self.client.table("books")
            .select("*")
            .is_("outline", "null")
            .not_.is_("notes_on_outline_before", "null")
            .execute()
        )
        return [self._row_to_book(r) for r in res.data]

    def get_books_for_chapter_generation(self) -> List[Book]:
        """Books that have an outline and are not yet marked as ready output.

        Gating on chapter-level notes happens in the workflow, but we only
        consider books that at least have an outline present.
        """
        res = (
            self.client.table("books")
            .select("*")
            .not_.is_("outline", "null")
            .execute()
        )
        return [self._row_to_book(r) for r in res.data]

    def get_books_for_compilation(self) -> List[Book]:
        """Return all books; compilation workflow will apply gating rules.

        This keeps DB logic simple and lets the workflow enforce
        final_review_notes_status / book_output_status constraints.
        """
        res = self.client.table("books").select("*").execute()
        return [self._row_to_book(r) for r in res.data]

    def update_book_outline(
        self,
        book_id: str,
        outline: str,
    ) -> None:
        self.client.table("books").update({"outline": outline}).eq("id", book_id).execute()

    def log_outline_version(
        self,
        book_id: str,
        outline: str,
        notes_on_outline_before: Optional[str] = None,
        notes_on_outline_after: Optional[str] = None,
    ) -> None:
        """Insert a row in outline_versions for audit / regeneration history."""
        payload = {
            "book_id": book_id,
            "outline": outline,
            "notes_on_outline_before": notes_on_outline_before,
            "notes_on_outline_after": notes_on_outline_after,
        }
        # Ignore failures if table not present
        try:
            self.client.table("outline_versions").insert(payload).execute()
        except Exception:
            pass

    def get_books(self) -> List[Book]:
        res = self.client.table("books").select("*").execute()
        return [self._row_to_book(r) for r in res.data]

    def update_book_status(
        self,
        book_id: str,
        **fields: Any,
    ) -> None:
        if not fields:
            return
        self.client.table("books").update(fields).eq("id", book_id).execute()

    # --- Chapters ---
    def get_chapters_for_book(self, book_id: str) -> List[Dict[str, Any]]:
        res = (
            self.client.table("chapters")
            .select("*")
            .eq("book_id", book_id)
            .order("chapter_number", desc=False)
            .execute()
        )
        return res.data

    def get_chapters_missing_content(self, book_id: str) -> List[Dict[str, Any]]:
        """Fetch chapters without content (for regeneration or first generation)."""
        res = (
            self.client.table("chapters")
            .select("*")
            .eq("book_id", book_id)
            .is_("content", "null")
            .order("chapter_number", desc=False)
            .execute()
        )
        return res.data

    def upsert_chapter(
        self,
        book_id: str,
        chapter_number: int,
        chapter_title: str,
        content: str,
        summary: str,
    ) -> Dict[str, Any]:
        payload = {
            "book_id": book_id,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "content": content,
            "summary": summary,
        }
        self.client.table("chapters").upsert(
            payload,
            on_conflict="book_id,chapter_number",
        ).execute()
        res = (
            self.client.table("chapters")
            .select("*")
            .eq("book_id", book_id)
            .eq("chapter_number", chapter_number)
            .limit(1)
            .execute()
        )
        return res.data[0]

    def update_chapter_fields(
        self,
        chapter_id: str,
        **fields: Any,
    ) -> None:
        if not fields:
            return
        self.client.table("chapters").update(fields).eq("id", chapter_id).execute()

    # --- Helpers ---
    @staticmethod
    def _row_to_book(row: Dict[str, Any]) -> Book:
        return Book(
            id=row["id"],
            title=row.get("title"),
            notes_on_outline_before=row.get("notes_on_outline_before"),
            outline=row.get("outline"),
            notes_on_outline_after=row.get("notes_on_outline_after"),
            status_outline_notes=row.get("status_outline_notes"),
            final_review_notes=row.get("final_review_notes"),
            final_review_notes_status=row.get("final_review_notes_status"),
            book_output_status=row.get("book_output_status"),
        )
