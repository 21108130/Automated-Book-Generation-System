from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from .db import Database


REQUIRED_COLUMNS = ["title", "notes_on_outline_before", "status_outline_notes"]


def import_books_from_excel(db: Database, excel_path: str) -> List[dict]:
    """Read Excel and upsert books into Supabase.

    Expected columns (sheet 0):
      - title (mandatory)
      - notes_on_outline_before (required for outline generation)
      - status_outline_notes (yes | no | no_notes_needed)
    """
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    df = pd.read_excel(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in Excel: {missing}")

    upserted: List[dict] = []
    for _, row in df.iterrows():
        record = {
            "title": str(row["title"]).strip() if not pd.isna(row["title"]) else None,
            "notes_on_outline_before": None
            if pd.isna(row["notes_on_outline_before"])
            else str(row["notes_on_outline_before"]).strip(),
            "status_outline_notes": None
            if pd.isna(row["status_outline_notes"])
            else str(row["status_outline_notes"]).strip(),
        }
        if not record["title"]:
            continue
        upserted.append(db.upsert_book_from_row(record))

    return upserted
