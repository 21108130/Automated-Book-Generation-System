from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional

import requests

from .config import AppConfig


class Notifier:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    # --- Public helpers ---
    def notify_outline_ready(self, book_title: str) -> None:
        subject = f"Outline ready for review: {book_title}"
        body = f"The outline for '{book_title}' is ready and awaiting editor review."
        self._send_all(subject, body)

    def notify_waiting_chapter_notes(self, book_title: str, chapter_number: int) -> None:
        subject = f"Waiting for notes on chapter {chapter_number}: {book_title}"
        body = (
            f"Chapter {chapter_number} for '{book_title}' is pending editor notes. "
            "Update chapter_notes and chapter_notes_status in Supabase."
        )
        self._send_all(subject, body)

    def notify_final_compiled(self, book_title: str, output_path: str) -> None:
        subject = f"Final draft compiled: {book_title}"
        body = f"The final draft for '{book_title}' has been compiled. File: {output_path}"
        self._send_all(subject, body)

    def notify_error(self, context: str, error_message: str) -> None:
        subject = f"Book generation error in {context}"
        body = f"An error occurred in {context}:\n\n{error_message}"
        self._send_all(subject, body)

    # --- Internal helpers ---
    def _send_all(self, subject: str, body: str) -> None:
        if self.cfg.email.enabled:
            try:
                self._send_email(subject, body)
            except Exception:
                # For this trial system we swallow notification failures
                pass
        if self.cfg.teams.enabled:
            try:
                self._send_teams(subject, body)
            except Exception:
                pass

    def _send_email(self, subject: str, body: str) -> None:
        c = self.cfg.email
        if not c.to_addresses:
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = c.from_address or c.username
        msg["To"] = ", ".join(c.to_addresses)
        msg.set_content(body)

        with smtplib.SMTP(c.smtp_host, c.smtp_port, timeout=30) as server:
            if c.use_tls:
                server.starttls()
            if c.username and c.password:
                server.login(c.username, c.password)
            server.send_message(msg)

    def _send_teams(self, subject: str, body: str) -> None:
        c = self.cfg.teams
        if not c.webhook_url:
            return

        payload = {
            "text": f"**{subject}**\n\n{body}",
        }
        requests.post(c.webhook_url, json=payload, timeout=30)
