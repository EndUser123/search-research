# yt_sync/filtering.py

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class VideoFilterer:
    """Applies a rich set of user-defined filter rules to a set of videos."""

    def __init__(self, channel_filters: dict[str, Any]):
        self.skip = channel_filters.get("skip", False)
        self.rules = {
            k: v for k, v in channel_filters.items() if k not in ["skip", "__comment__"]
        }

    def apply_filters(
        self, ids_to_check: set[str], metadata_dict: dict[str, dict[str, Any]]
    ) -> set[str]:
        """Filters a set of video IDs based on the loaded rules."""
        if not self.rules:
            return ids_to_check

        logger.info(
            f"Applying {len(self.rules)} filter rule(s) to {len(ids_to_check)} videos..."
        )

        passed_videos = set()

        for vid_id in ids_to_check:
            metadata = metadata_dict.get(vid_id)
            if not metadata:
                continue

            if self._video_passes_all_rules(metadata):
                passed_videos.add(vid_id)

        return passed_videos

    def _video_passes_all_rules(self, metadata: dict[str, Any]) -> bool:
        """Checks if a single video's metadata passes all defined filter rules."""
        # A video is rejected if it fails ANY rule.
        # Each check function returns True on FAILURE.
        if self._check_text_fail(
            metadata.get("title", ""),
            self.rules.get("require_title"),
            self.rules.get("reject_title"),
        ):
            return False
        if self._check_text_fail(
            metadata.get("description", ""),
            self.rules.get("require_description"),
            self.rules.get("reject_description"),
        ):
            return False
        if self._check_tags_fail(
            metadata.get("tags", []),
            self.rules.get("require_tags"),
            self.rules.get("reject_tags"),
        ):
            return False
        if self._check_numeric_fail(
            metadata.get("duration"),
            self.rules.get("min_duration"),
            self.rules.get("max_duration"),
        ):
            return False
        if self._check_numeric_fail(
            metadata.get("view_count"),
            self.rules.get("min_views"),
            self.rules.get("max_views"),
        ):
            return False
        if self._check_numeric_fail(
            metadata.get("like_count"),
            self.rules.get("min_likes"),
            self.rules.get("max_likes"),
        ):
            return False
        if self._check_date_fail(
            metadata.get("upload_date"),
            self.rules.get("after_date"),
            self.rules.get("before_date"),
        ):
            return False
        if self._check_live_status_fail(
            metadata, self.rules.get("require_live"), self.rules.get("reject_live")
        ):
            return False
        if self._check_category_fail(
            metadata.get("categories", []),
            self.rules.get("require_category"),
            self.rules.get("reject_category"),
        ):
            return False

        return True  # Survived all checks

    def _check_text_fail(
        self, text: str, required: list[str] | None, rejected: list[str] | None
    ) -> bool:
        """Returns True if the text filter fails."""
        text_lower = text.lower()
        if required and not any(req.lower() in text_lower for req in required):
            logger.debug(
                f"Filter fail (require_title/desc): '{required[0]}...' not in '{text[:50]}...'"
            )
            return True
        if rejected and any(rej.lower() in text_lower for rej in rejected):
            logger.debug(
                f"Filter fail (reject_title/desc): Found '{rejected[0]}...' in '{text[:50]}...'"
            )
            return True
        return False

    def _check_tags_fail(
        self,
        tags: list[str],
        required: list[str] | None,
        rejected: list[str] | None,
    ) -> bool:
        """Returns True if the tags filter fails."""
        if not tags and required:
            logger.debug(
                f"Filter fail (require_tags): No tags present, but required: {required}"
            )
            return True
        tags_lower = {tag.lower() for tag in tags}
        if required and not any(req.lower() in tags_lower for req in required):
            logger.debug(
                f"Filter fail (require_tags): None of {required} in tags {tags}"
            )
            return True
        if rejected and any(rej.lower() in tags_lower for rej in rejected):
            logger.debug(
                f"Filter fail (reject_tags): Found one of {rejected} in tags {tags}"
            )
            return True
        return False

    def _check_numeric_fail(
        self, value: int | None, min_val: int | None, max_val: int | None
    ) -> bool:
        """Returns True if the numeric filter fails."""
        if value is None:
            return False  # Cannot evaluate, so it passes
        if min_val is not None and value < min_val:
            logger.debug(f"Filter fail (min): {value} < {min_val}")
            return True
        if max_val is not None and value > max_val:
            logger.debug(f"Filter fail (max): {value} > {max_val}")
            return True
        return False

    def _check_date_fail(
        self,
        upload_date_str: str | None,
        after_date: str | None,
        before_date: str | None,
    ) -> bool:
        """Returns True if the date filter fails."""
        if not upload_date_str:
            return False  # Cannot evaluate, so it passes

        try:
            # yt-dlp format is 'YYYYMMDD'
            upload_date = datetime.strptime(upload_date_str, "%Y%m%d")
            if after_date and upload_date <= datetime.strptime(after_date, "%Y%m%d"):
                return True  # Fails because it's not after the date
            if before_date and upload_date >= datetime.strptime(before_date, "%Y%m%d"):
                return True  # Fails because it's not before the date
        except (ValueError, TypeError):
            return False  # Passes if dates are malformed
        return False

    def _check_live_status_fail(
        self,
        metadata: dict[str, Any],
        require_live: bool | None,
        reject_live: bool | None,
    ) -> bool:
        """Returns True if the live status filter fails."""
        is_live = metadata.get("is_live", False) or metadata.get("was_live", False)
        if require_live is True and not is_live:
            return True  # Fails because it's not a live video
        if reject_live is True and is_live:
            return True  # Fails because it is a live video
        return False

    def _check_category_fail(
        self, categories: list[str], required: str | None, rejected: str | None
    ) -> bool:
        """Returns True if the category filter fails."""
        if not categories and required:
            return True  # Fails if category is required but none exist

        cat_lower = {cat.lower() for cat in categories}
        if required and required.lower() not in cat_lower:
            return True  # Fails because required category is missing
        if rejected and rejected.lower() in cat_lower:
            return True  # Fails because category is rejected
        return False
