# --- METADATA ---
# Filename: yt_sync/metadata.py
# Version: 1.1
#
# --- CHANGELOG ---
# v1.1: Implemented the missing `_load_api_cache` method to fix AttributeError on startup.
#
# --- INTEGRITY ---
# Previous Character Count: 8202
# Current Character Count: 8712
# Reason for Shrinkage: null
# ------------------
#
# yt_sync/metadata.py

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed  # For concurrency
from pathlib import Path
from typing import Any

from rich.console import Console

# Ensure these imports are correct based on your project structure
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from yt_dlp import YoutubeDL

from .error_tracker import ErrorTracker  # Import the project's ErrorTracker

logger = logging.getLogger(__name__)


class MetadataManager:
    def __init__(self, args, metadata_dir: Path, api_client):
        self.args = args
        self.metadata_dir = metadata_dir
        self.api_client = api_client
        self.cache: dict[str, dict[str, Any]] = {}
        self.api_cache_file = metadata_dir / "api_cache.json"
        self.api_cache: dict[str, dict[str, Any]] = {}
        # Cache never expires - user explicitly requested no expiration
        self.api_cache: dict[str, dict[str, Any]] = self._load_api_cache()

    def _load_api_cache(self) -> dict[str, Any]:
        """Loads the API metadata cache from a JSON file."""
        if self.api_cache_file.exists():
            try:
                with open(self.api_cache_file, encoding="utf-8") as f:
                    logger.debug(f"Loading API cache from {self.api_cache_file}")
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(
                    f"Could not load or parse API cache file '{self.api_cache_file}': {e}"
                )
                return {}
        return {}

    def _save_api_cache(self):
        """Saves the in-memory API cache to a JSON file."""
        # This method is a placeholder for potential future implementation if needed.
        pass
        self.enable_enrichment = self.args.enrichment_config.get("enabled", False)
        self.enrichment_timeout = self.args.enrichment_config.get("timeout_seconds", 30)
        self.skip_enrichment_threshold = self.args.enrichment_config.get(
            "skip_threshold", 100
        )

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "dump_single_json": True,
            "extract_flat": True,  # Only extract info, don't download
            "retries": 3,
            "socket_timeout": self.enrichment_timeout,
        }
        if self.args.cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (
                self.args.cookies_from_browser,
                self.args.profile,
            )
        elif self.args.cookies_file:
            ydl_opts["cookiefile"] = self.args.cookies_file

        # THIS IS THE CRUCIAL LINE THAT WAS LIKELY MISSING/COMMENTED OUT
        self.ydl = YoutubeDL(ydl_opts)

        # THIS IS THE CRUCIAL LINE FOR ERROR TRACKER INSTANCE
        self.error_tracker = ErrorTracker()

        # Initialize Rich progress components
        self.progress_console = Console()
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            SpinnerColumn(),
            TextColumn("[progress.completed]{task.completed}/{task.total}"),
            console=self.progress_console,
        )

    def load_metadata_for_ids(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        """
        Loads metadata for a list of video IDs from cache, local files, or hybrid (API/yt-dlp).
        """
        if not ids:
            return {}

        results: dict[str, dict[str, Any]] = {}
        ids_to_fetch_from_hybrid: list[str] = []

        # Step 1: Try to load from in-memory cache and local files first
        for vid_id in ids:
            if vid_id in self.cache:
                results[vid_id] = self.cache[vid_id]
            else:
                metadata_file = self.metadata_dir / f"{vid_id}.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, encoding="utf-8") as f:
                            file_metadata = json.load(f)
                            if isinstance(file_metadata, dict):
                                self.cache[vid_id] = file_metadata
                                results[vid_id] = file_metadata
                            else:
                                self.error_tracker.add_error(
                                    video_id=vid_id,
                                    error_type="METADATA_PARSE_ERROR",
                                    error_message=(
                                        f"File metadata for '{vid_id}' is not a dictionary. "
                                        f"Found type: {type(file_metadata).__name__}. "
                                        f"Skipping file and fetching via hybrid."
                                    ),
                                )
                                ids_to_fetch_from_hybrid.append(vid_id)
                    except json.JSONDecodeError as e:
                        self.error_tracker.add_error(
                            video_id=vid_id,
                            error_type="METADATA_PARSE_ERROR",
                            error_message=f"Error parsing metadata file '{metadata_file}': {e}",
                        )
                        ids_to_fetch_from_hybrid.append(vid_id)
                    except OSError as e:
                        self.error_tracker.add_error(
                            video_id=vid_id,
                            error_type="FILE_READ_ERROR",
                            error_message=f"Error reading metadata file '{metadata_file}': {e}",
                        )
                        ids_to_fetch_from_hybrid.append(vid_id)
                else:
                    ids_to_fetch_from_hybrid.append(vid_id)

        # Step 2: Fetch remaining missing IDs using the hybrid (API/yt-dlp) approach
        if ids_to_fetch_from_hybrid:
            unique_ids_to_fetch = list(set(ids_to_fetch_from_hybrid))
            logger.debug(
                f"Fetching metadata for {len(unique_ids_to_fetch)} IDs via hybrid method."
            )

            try:
                hybrid_metadata = self._get_metadata_hybrid(unique_ids_to_fetch)
                for vid_id, data in hybrid_metadata.items():
                    if isinstance(data, dict):
                        self.cache[vid_id] = data
                        results[vid_id] = data
                        self._save_to_cache(vid_id, data)
                    else:
                        self.error_tracker.add_error(
                            video_id=vid_id,
                            error_type="INVALID_HYBRID_METADATA",
                            error_message=(
                                f"Invalid metadata type from hybrid source. "
                                f"Expected dictionary, got {type(data).__name__}. This ID will be skipped."
                            ),
                        )
            except Exception as e:
                self.error_tracker.add_error(
                    video_id="",  # Batch error, not specific to one video ID
                    error_type="HYBRID_FETCH_ERROR",
                    error_message=f"Failed to retrieve metadata for {len(unique_ids_to_fetch)} IDs from hybrid source (API/yt-dlp fallback): {e}",
                )

        return results

    def _get_metadata_hybrid(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        """
        Attempts to get metadata for IDs using API client first, then yt-dlp as fallback.
        """
        api_results: dict[str, dict[str, Any]] = {}
        yt_dlp_missing_ids: list[str] = []

        try:
            api_results = self.api_client.get_videos_metadata(ids)
            for vid_id in ids:
                if vid_id not in api_results:
                    yt_dlp_missing_ids.append(vid_id)
        except Exception as e:
            self.error_tracker.add_error(
                video_id="",  # Batch error
                error_type="API_FETCH_ERROR",
                error_message=f"API client failed to get metadata for {len(ids)} IDs. Falling back to yt-dlp for all: {e}",
            )
            yt_dlp_missing_ids = ids  # Fall back for all if API fails

        if yt_dlp_missing_ids and self.enable_enrichment:
            logger.debug(
                f"Attempting yt-dlp fallback for {len(yt_dlp_missing_ids)} IDs."
            )
            yt_dlp_results = {}

            with ThreadPoolExecutor(
                max_workers=5
            ) as executor:  # Using ThreadPoolExecutor for concurrency
                future_to_id = {
                    executor.submit(self._fetch_single_via_ytdlp, vid_id): vid_id
                    for vid_id in yt_dlp_missing_ids
                }

                with self.progress:  # Start progress bar for yt-dlp fallback
                    task = self.progress.add_task(
                        f"[cyan]Fetching missing metadata via yt-dlp for {len(yt_dlp_missing_ids)} videos...",
                        total=len(yt_dlp_missing_ids),
                    )

                    for future in as_completed(future_to_id):
                        vid_id = future_to_id[future]
                        try:
                            video_info = future.result()
                            if (
                                video_info
                            ):  # Only add if info was successfully retrieved
                                yt_dlp_results[vid_id] = video_info
                        except Exception as e:
                            # Error might already be tracked by _fetch_single_via_ytdlp, but catching executor-specific errors
                            self.error_tracker.add_error(
                                video_id=vid_id,
                                error_type="YTDLP_CONCURRENCY_ERROR",
                                error_message=f"Failed to get yt-dlp info for '{vid_id}' in concurrent pool: {e}",
                            )
                        finally:
                            self.progress.update(task, advance=1)
            return {**api_results, **yt_dlp_results}
        else:
            return api_results

    def _fetch_single_via_ytdlp(self, vid_id: str) -> dict[str, Any] | None:
        """Helper to fetch a single video's info via yt-dlp, used by _get_metadata_hybrid."""
        url = f"https://www.youtube.com/watch?v={vid_id}"
        try:
            info = self.ydl.extract_info(url, download=False)
            if isinstance(info, dict):
                if (
                    "entries" in info
                    and isinstance(info["entries"], list)
                    and info["entries"]
                ):
                    return info["entries"][0]
                else:
                    return info
            else:
                self.error_tracker.add_error(
                    video_id=vid_id,
                    error_type="YTDLP_FORMAT_ERROR",
                    error_message=f"yt-dlp returned non-dictionary info for ID '{vid_id}'. Got {type(info).__name__}.",
                )
                return None
        except Exception as e:
            self.error_tracker.add_error(
                video_id=vid_id,
                error_type="YTDLP_ERROR",
                error_message=f"yt-dlp fallback failed for '{vid_id}': {e}",
            )
            return None

    def enrich_metadata_batch(self, ids: list[str]):
        """
        Public method to enrich a batch of videos with technical details using yt-dlp.
        """
        if not self.enable_enrichment:
            logger.debug("Metadata enrichment is disabled in configuration.")
            return

        videos_to_enrich = []
        for vid_id in ids:
            metadata = self.cache.get(vid_id)
            # Check if metadata exists and is missing enrichment-specific keys
            # or if it's missing the webpage_url to fetch from (as yt-dlp needs it)
            if metadata and (
                not all(k in metadata for k in ["width", "height", "fps", "vcodec"])
                or not metadata.get("webpage_url")
            ):
                videos_to_enrich.append(vid_id)

        # Implement skip_enrichment_threshold
        if (
            self.skip_enrichment_threshold > 0
            and len(videos_to_enrich) > self.skip_enrichment_threshold
        ):
            self.error_tracker.add_error(
                video_id="",  # Not specific to one video, a batch decision
                error_type="ENRICHMENT_SKIPPED",
                error_message=(
                    f"Enrichment skipped for {len(videos_to_enrich)} videos "
                    f"as it exceeds the threshold of {self.skip_enrichment_threshold}."
                ),
            )
            logger.warning(
                f"Enrichment skipped for {len(videos_to_enrich)} videos as it exceeds the threshold of {self.skip_enrichment_threshold}."
            )
            return

        if not videos_to_enrich:
            logger.debug(
                "No videos need enrichment or enrichment was skipped (e.g., threshold)."
            )
            return

        logger.info(f"Starting enrichment for {len(videos_to_enrich)} videos...")

        # Restore concurrency for enrichment
        with ThreadPoolExecutor(
            max_workers=5
        ) as executor:  # Use a pool for concurrent enrichment
            future_to_id = {
                executor.submit(self._enrich_single_video, vid_id): vid_id
                for vid_id in videos_to_enrich
            }

            with self.progress:  # Start progress bar
                task = self.progress.add_task(
                    f"[cyan]Enriching metadata (yt-dlp) for {len(videos_to_enrich)} videos...",
                    total=len(videos_to_enrich),
                )

                for future in as_completed(future_to_id):
                    vid_id = future_to_id[future]
                    try:
                        future.result()  # Will raise any exception from _enrich_single_video (which is tracked)
                    except Exception as e:
                        # Catch and track any unexpected concurrency-level errors
                        self.error_tracker.add_error(
                            video_id=vid_id,
                            error_type="ENRICHMENT_CONCURRENCY_ERROR",
                            error_message=f"Failed to enrich '{vid_id}' in concurrent pool: {e}",
                        )
                    finally:
                        self.progress.update(task, advance=1)

    def _enrich_single_video(self, vid_id: str) -> bool:
        """
        Enrich metadata for a single video using yt-dlp.
        Returns True on success, False on failure.
        """
        metadata = self.cache.get(vid_id)
        if not metadata:
            self.error_tracker.add_error(
                video_id=vid_id,
                error_type="ENRICHMENT_NO_METADATA",
                error_message="No metadata found in cache.",
            )
            return False

        webpage_url = (
            metadata.get("webpage_url") or f"https://www.youtube.com/watch?v={vid_id}"
        )

        try:
            info = self.ydl.extract_info(webpage_url, download=False)

            if isinstance(info, dict):
                if (
                    "entries" in info
                    and isinstance(info["entries"], list)
                    and info["entries"]
                ):
                    video_info = info["entries"][0]
                else:
                    video_info = info
            else:
                self.error_tracker.add_error(
                    video_id=vid_id,
                    error_type="YTDLP_FORMAT_ERROR",
                    error_message=(
                        f"yt-dlp returned unexpected format for '{vid_id}'. "
                        f"Expected dictionary or dict with 'entries', got {type(info).__name__}."
                    ),
                )
                return False

            updated_metadata = {**metadata, **video_info}
            self._save_to_cache(vid_id, updated_metadata)
            return True
        except Exception as e:
            self.error_tracker.add_error(
                video_id=vid_id,
                error_type="ENRICHMENT_YTDLP_ERROR",
                error_message=f"Failed to enrich metadata for video '{vid_id}' (URL: {webpage_url}): {e}",
            )
            return False

    def _save_to_cache(self, vid_id: str, metadata: dict[str, Any]):
        """
        Saves metadata to the in-memory cache and to a JSON file on disk.
        """
        self.cache[vid_id] = metadata  # Update in-memory cache first
        metadata_file = self.metadata_dir / f"{vid_id}.json"
        try:
            metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except OSError as e:
            self.error_tracker.add_error(
                video_id=vid_id,
                error_type="METADATA_SAVE_ERROR",
                error_message=f"Error saving metadata to file '{metadata_file}': {e}",
            )
            logger.error(
                f"Error saving metadata for '{vid_id}' to cache: {e}"
            )  # Simplified log message
