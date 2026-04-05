"""
Multi-language subtitle management.

Handles downloading, storing, and querying subtitles in multiple languages.
"""
from __future__ import annotations

from typing import Literal

from rich.console import Console
from sqlite_utils import Database

from yt_fts.core.database import get_db_path

LanguageCode = Literal[
    "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi", "th", "vi", "id", "nl", "pl", "sv", "tr", "uk"
]

# Common language names mapping
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "tr": "Turkish",
    "uk": "Ukrainian",
}


class LanguageManager:
    """Manage multi-language subtitles."""

    def __init__(self) -> None:
        """
        Initialize the language manager.

        Sets up the console for output and the database connection
        for multi-language subtitle operations.
        """
        self.console = Console()
        self.db = Database(get_db_path())

    def list_available_languages(self, video_id: str) -> list[dict]:
        """
        List all available subtitle languages for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            List of dictionaries with language info
        """
        try:
            languages = self.db.execute(
                """
                SELECT language_code, language_name, is_generated, download_date
                FROM SubtitleLanguages
                WHERE video_id = ?
                ORDER BY language_code
                """,
                [video_id],
            ).fetchall()

            return [
                {
                    "code": row[0],
                    "name": row[1] or LANGUAGE_NAMES.get(row[0], row[0].upper()),
                    "is_generated": bool(row[2]),
                    "download_date": row[3],
                }
                for row in languages
            ]
        except Exception as e:
            self.console.print(f"[red]Error listing languages:[/red] {e}")
            return []

    def get_subtitle_language(self, video_id: str, language_code: str = "en") -> list[tuple]:
        """
        Get subtitles for a video in a specific language.

        Args:
            video_id: YouTube video ID
            language_code: Language code (default: "en")

        Returns:
            List of (start_time, stop_time, text) tuples
        """
        try:
            return self.db.execute(
                """
                SELECT start_time, stop_time, text
                FROM Subtitles
                WHERE video_id = ? AND language_code = ?
                ORDER BY start_time
                """,
                [video_id, language_code],
            ).fetchall()

        except Exception as e:
            self.console.print(f"[red]Error fetching subtitles:[/red] {e}")
            return []

    def save_subtitle_language(
        self,
        video_id: str,
        language_code: str,
        subtitles: list[tuple],
        is_generated: bool = False,
    ) -> None:
        """
        Save subtitles for a video in a specific language.

        Args:
            video_id: YouTube video ID
            language_code: Language code (e.g., "en", "es", "fr")
            subtitles: List of (start_time, stop_time, text) tuples
            is_generated: Whether subtitles are auto-generated (True) or manual (False)
        """
        from datetime import datetime

        try:
            # Save subtitles to Subtitles table
            for start_time, stop_time, text in subtitles:
                self.db["Subtitles"].insert(
                    {
                        "video_id": video_id,
                        "start_time": start_time,
                        "stop_time": stop_time,
                        "text": text,
                        "language_code": language_code,
                        "is_generated": 1 if is_generated else 0,
                    },
                    replace=True,  # Update if exists
                )

            # Update SubtitleLanguages metadata
            language_name = LANGUAGE_NAMES.get(language_code, language_code.upper())
            download_date = datetime.now().isoformat()

            self.db.execute(
                """
                INSERT OR REPLACE INTO SubtitleLanguages
                (video_id, language_code, language_name, is_generated, download_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                [video_id, language_code, language_name, 1 if is_generated else 0, download_date],
            )

            self.console.print(
                f"[green]✓[/green] Saved {len(subtitles)} subtitles "
                f"in [bold]{language_name}[/bold] ({language_code})"
            )

        except Exception as e:
            self.console.print(f"[red]Error saving subtitles:[/red] {e}")

    def delete_subtitle_language(self, video_id: str, language_code: str) -> None:
        """
        Delete subtitles for a video in a specific language.

        Args:
            video_id: YouTube video ID
            language_code: Language code to delete
        """
        try:
            # Delete from Subtitles table
            self.db.execute(
                "DELETE FROM Subtitles WHERE video_id = ? AND language_code = ?",
                [video_id, language_code],
            )

            # Delete from SubtitleLanguages table
            self.db.execute(
                "DELETE FROM SubtitleLanguages WHERE video_id = ? AND language_code = ?",
                [video_id, language_code],
            )

            language_name = LANGUAGE_NAMES.get(language_code, language_code.upper())
            self.console.print(
                f"[green]✓[/green] Deleted {language_name} ({language_code}) subtitles"
            )

        except Exception as e:
            self.console.print(f"[red]Error deleting subtitles:[/red] {e}")

    def get_all_language_codes(self) -> list[str]:
        """
        Get all language codes that have subtitles in the database.

        Returns:
            List of language codes
        """
        try:
            codes = self.db.execute(
                "SELECT DISTINCT language_code FROM SubtitleLanguages ORDER BY language_code"
            ).fetchall()

            return [row[0] for row in codes]
        except Exception:
            return []


def validate_language_code(language_code: str) -> bool:
    """
    Validate a language code.

    Args:
        language_code: Language code to validate (e.g., "en", "es", "fr")

    Returns:
        True if valid, False otherwise
    """
    # Basic validation: 2 letter ISO 639-1 code only
    import re

    return bool(re.match(r"^[a-z]{2}$", language_code.lower()))


def normalize_language_code(language_code: str) -> str:
    """
    Normalize a language code to lowercase.

    Args:
        language_code: Language code to normalize

    Returns:
        Normalized language code
    """
    return language_code.lower().strip()
