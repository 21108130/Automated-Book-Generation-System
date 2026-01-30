from __future__ import annotations

from typing import List

from google import genai
from google.genai import types as genai_types

from .config import AppConfig


class LLMClient:
    """LLM adapter using Gemini via the new google-genai SDK."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.client = genai.Client(api_key=cfg.gemini.api_key)  # Changed from cfg.openai

    def generate_outline(self, title: str, notes_before: str, notes_after: str | None = None) -> str:
        """Generate a structured outline for the book."""
        notes_section = f"Editor notes before outline: {notes_before}\n" if notes_before else ""
        if notes_after:
            notes_section += f"Editor notes after previous outline: {notes_after}\n"

        prompt = (
            "You are an expert book editor. Generate a clear, numbered outline "
            "for a non-fiction style book. Use the editor notes to shape the "
            "structure, level of depth, and perspective. Return plain text.\n\n"
            f"Book title: {title}\n\n"
            f"{notes_section}"
        )

        resp = self.client.models.generate_content(
            model=self.cfg.gemini.model,  # Changed from cfg.openai
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=self.cfg.llm.temperature,
                max_output_tokens=self.cfg.llm.max_tokens,
            ),
        )
        return resp.text or ""

    def generate_chapter(
        self,
        title: str,
        outline: str,
        chapter_title: str,
        chapter_number: int,
        previous_summaries: List[str],
        chapter_notes: str | None = None,
    ) -> str:
        """Generate chapter text based on context and notes."""
        summaries_text = "\n".join(
            f"Chapter {i+1} summary: {s}" for i, s in enumerate(previous_summaries)
        )
        notes_text = f"\n\nSpecific notes for this chapter: {chapter_notes}" if chapter_notes else ""

        user_prompt = (
            "Using the following book context, write the full prose for the "
            f"chapter {chapter_number}: '{chapter_title}'.\n\n"
            f"Book title: {title}\n\n"
            f"Full outline:\n{outline}\n\n"
            f"Summaries of previous chapters (for continuity):\n{summaries_text or 'No previous chapters.'}"
            f"{notes_text}\n\n"
            "Write in a consistent style. Return only the chapter text."
        )

        resp = self.client.models.generate_content(
            model=self.cfg.gemini.model,  # Changed from cfg.openai
            contents=user_prompt,
            config=genai_types.GenerateContentConfig(
                temperature=self.cfg.llm.temperature,
                max_output_tokens=self.cfg.llm.max_tokens,
            ),
        )
        return resp.text or ""

    def summarize_chapter(self, chapter_text: str) -> str:
        """Summarize a single chapter for context chaining."""
        prompt = "Summarize the following chapter in 3-5 bullet points:\n\n" + chapter_text
        resp = self.client.models.generate_content(
            model=self.cfg.gemini.model,  # Changed from cfg.openai
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=400,
            ),
        )
        return resp.text or ""