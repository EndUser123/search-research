"""
Media Type Configuration Loader

This module loads media type classification rules from config.toml
and provides functions for classifying media files.
"""

import tomllib
from pathlib import Path
from typing import Any

from loguru import logger

# Import the new ConfigLoader
from .config_loader import ConfigLoader


class MediaTypeConfig:
    """Configuration for media type classification."""

    def __init__(self, config_path: str | None = None):
        # Use the new ConfigLoader to load the config
        # The base_path for ConfigLoader should be the project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[
            3
        ]  # Go up from src/download/config/ to project root
        loader = ConfigLoader(project_root)
        self.config = loader.get_config()

        self.classification_rules: dict[str, Any] = {}
        self._load_classification_rules()  # Renamed from _load_config to avoid confusion

    # Removed _find_config_file as it's now handled by ConfigLoader

    def _load_classification_rules(self) -> None:  # Renamed from _load_config
        """Load media classification rules from the loaded config."""
        if not self.config:  # If config is empty (e.g., file not found)
            logger.warning("Config not loaded, using default media classifications")
            self._load_default_config()
            return

        try:
            # Extract media classification rules
            self.classification_rules = self.config.get("media_classification", {})
            logger.debug("Loaded media classification config from ConfigLoader")

        except Exception as e:
            logger.error(f"Error processing loaded config: {e}")
            self._load_default_config()

    def _find_config_file(self) -> str:
        """Find the config.toml file in the project root."""
        # Start from current file and go up to find project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[
            3
        ]  # Go up from src/download/config/ to project root

        config_file = project_root / "config.toml"
        if config_file.exists():
            return str(config_file)

        # Fallback: look in current working directory
        cwd_config = Path.cwd() / "config.toml"
        if cwd_config.exists():
            return str(cwd_config)

        logger.warning(f"config.toml not found. Checked: {config_file}, {cwd_config}")
        return str(config_file)  # Return path anyway for error messages

    def _load_config(self) -> None:
        """Load configuration from TOML file."""
        if not tomllib:
            logger.warning(
                "TOML library not available, using default media classifications"
            )
            self._load_default_config()
            return

        try:
            with open(self.config_path, "rb") as f:
                self.config = tomllib.load(f)

            # Extract media classification rules
            self.classification_rules = self.config.get("media_classification", {})
            logger.debug(f"Loaded media classification config from {self.config_path}")

        except FileNotFoundError:
            logger.warning(
                f"Config file not found at {self.config_path}, using default classifications"
            )
            self._load_default_config()
        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {e}")
            self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default media classification rules as fallback."""
        self.classification_rules = {
            "video": {
                "extensions": [
                    "mp4",
                    "avi",
                    "mkv",
                    "mov",
                    "wmv",
                    "flv",
                    "webm",
                    "m4v",
                    "3gp",
                ],
                "telegram_types": ["MessageMediaDocument"],
                "keywords": ["video", "movie", "film", "clip"],
            },
            "image": {
                "extensions": [
                    "jpg",
                    "jpeg",
                    "png",
                    "gif",
                    "bmp",
                    "webp",
                    "tiff",
                    "svg",
                ],
                "telegram_types": ["MessageMediaPhoto", "MessageMediaWebPage"],
                "keywords": ["image", "photo", "picture", "screenshot", "pic"],
            },
            "text": {
                "extensions": [
                    "txt",
                    "pdf",
                    "doc",
                    "docx",
                    "rtf",
                    "md",
                    "html",
                    "xml",
                    "json",
                    "csv",
                ],
                "telegram_types": [],
                "keywords": ["document", "text", "manual", "guide", "readme", "report"],
            },
            "audio": {
                "extensions": [
                    "mp3",
                    "wav",
                    "flac",
                    "aac",
                    "ogg",
                    "wma",
                    "m4a",
                    "opus",
                ],
                "telegram_types": ["MessageMediaDocument"],
                "keywords": ["audio", "music", "song", "sound", "voice", "podcast"],
            },
            "archive": {
                "extensions": ["zip", "rar", "7z", "tar", "gz", "bz2", "exe", "msi"],
                "telegram_types": ["MessageMediaDocument"],
                "keywords": ["archive", "backup", "compressed", "installer", "setup"],
            },
            "other": {"extensions": [], "telegram_types": [], "keywords": []},
            "defaults": {
                "priority_order": [
                    "video",
                    "image",
                    "audio",
                    "text",
                    "archive",
                    "other",
                ],
                "strict_mode": False,
                "use_telegram_types": True,
                "use_keywords": True,
                "case_sensitive": False,
            },
        }
        logger.debug("Using default media classification rules")

    def get_classification_rules(self) -> dict[str, Any]:
        """Get all media classification rules."""
        return self.classification_rules

    def get_category_rules(self, category: str) -> dict[str, Any]:
        """Get rules for a specific media category."""
        return self.classification_rules.get(category, {})

    def get_defaults(self) -> dict[str, Any]:
        """Get default classification settings."""
        return self.classification_rules.get(
            "defaults",
            {
                "priority_order": [
                    "video",
                    "image",
                    "audio",
                    "text",
                    "archive",
                    "other",
                ],
                "strict_mode": False,
                "use_telegram_types": True,
                "use_keywords": True,
                "case_sensitive": False,
            },
        )

    def get_extensions_for_category(self, category: str) -> list[str]:
        """Get file extensions for a specific category."""
        rules = self.get_category_rules(category)
        extensions = rules.get("extensions", [])

        # Apply case sensitivity setting
        defaults = self.get_defaults()
        if not defaults.get("case_sensitive", False):
            extensions = [ext.lower() for ext in extensions]

        return extensions

    def get_telegram_types_for_category(self, category: str) -> list[str]:
        """Get Telegram media types for a specific category."""
        rules = self.get_category_rules(category)
        return rules.get("telegram_types", [])

    def get_keywords_for_category(self, category: str) -> list[str]:
        """Get keywords for a specific category."""
        rules = self.get_category_rules(category)
        keywords = rules.get("keywords", [])

        # Apply case sensitivity setting
        defaults = self.get_defaults()
        if not defaults.get("case_sensitive", False):
            keywords = [kw.lower() for kw in keywords]

        return keywords

    def classify_media(
        self, media_type: str | None = None, filename: str | None = None
    ) -> str:
        """
        Classify media based on configured rules.

        Args:
            media_type: Telegram media type string
            filename: Filename for classification

        Returns:
            Classification category string
        """
        if not media_type and not filename:
            return "other"

        defaults = self.get_defaults()
        priority_order = defaults.get(
            "priority_order", ["video", "image", "audio", "text", "archive", "other"]
        )
        use_telegram_types = defaults.get("use_telegram_types", True)
        use_keywords = defaults.get("use_keywords", True)
        case_sensitive = defaults.get("case_sensitive", False)

        # Normalize inputs for case sensitivity
        if not case_sensitive:
            filename_lower = filename.lower() if filename else ""
        else:
            filename_lower = filename or ""

        # Extract file extension
        file_ext = ""
        if filename_lower and "." in filename_lower:
            file_ext = filename_lower.split(".")[-1]

        # First pass: Check file extensions (highest priority)
        if file_ext:
            for category in priority_order:
                if category == "other":
                    continue
                extensions = self.get_extensions_for_category(category)
                if file_ext in extensions:
                    return category

        # Second pass: Check filename keywords
        if use_keywords and filename_lower:
            for category in priority_order:
                if category == "other":
                    continue
                keywords = self.get_keywords_for_category(category)
                for keyword in keywords:
                    if keyword in filename_lower:
                        return category

        # Third pass: Check Telegram media type (lowest priority for documents)
        if use_telegram_types and media_type:
            for category in priority_order:
                if category == "other":
                    continue
                telegram_types = self.get_telegram_types_for_category(category)
                if media_type in telegram_types:
                    # Special handling for MessageMediaDocument - don't auto-classify as video
                    if (
                        media_type == "MessageMediaDocument"
                        and category == "video"
                        and not file_ext
                    ):
                        continue  # Skip document->video classification without file extension
                    return category

        # Default to 'other' if no matches found
        return "other"

    def should_download_media_type(
        self, media_type: str, filename: str, filter_type: str
    ) -> bool:
        """
        Check if media should be downloaded based on type filter.

        Args:
            media_type: Telegram media type string
            filename: Filename for classification
            filter_type: Filter to apply ('all', 'video', 'image', 'text', 'audio', 'archive', 'other')

        Returns:
            True if media should be downloaded
        """
        if filter_type == "all":
            return True

        classified_type = self.classify_media(media_type, filename)
        return classified_type == filter_type


# Global configuration instance
_media_config = None


def get_media_config() -> MediaTypeConfig:
    """Get the global media configuration instance."""
    global _media_config
    if _media_config is None:
        _media_config = MediaTypeConfig()
    return _media_config


def classify_media_type(
    media_type: str | None = None, filename: str | None = None
) -> str:
    """Classify media type using global configuration."""
    config = get_media_config()
    return config.classify_media(media_type, filename)


def should_download_media_type(
    media_type: str, filename: str, filter_type: str
) -> bool:
    """Check if media should be downloaded using global configuration."""
    config = get_media_config()
    return config.should_download_media_type(media_type, filename, filter_type)


def reload_config():
    """Reload the media type configuration."""
    global _media_config
    _media_config = None
    get_media_config()
