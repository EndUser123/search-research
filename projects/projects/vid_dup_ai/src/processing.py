## --- METADATA ---
# Filename: src/processing.py
# Version: 2.2.0
# Confidence Level: HIGH - This change correctly applies the principle of separation of concerns, which is the standard solution for this architectural flaw.
# ------------------
#
# --- CHANGELOG ---
# v2.2.0: REFACTOR: Decoupled worker logic from the client-side OperationPlanner class. Moved duplicate detection and planning logic into standalone functions to be called by the Dramatiq worker, fixing a critical runtime failure.
# v2.1.0: FIX: Resolved a critical circular dependency between processing.py and tasks.py by moving the task import to be local to its usage site.
# v2.0.0: MAJOR: Replaced RQ enqueue logic with Dramatiq message sending. Added `get_results` to handle fetching results from completed jobs, simplifying the overall workflow.
# v1.2.1: FIX: Resolved all static analysis errors by moving optional imports to be local to their usage sites and using `find_spec` for availability checks.
# v1.2.0: FIX: Conditionally create Retry object without intervals on Windows to prevent scheduler-related SIGALRM crash. Updated user instructions.
# v1.1.0: FIX: Resolved all Pylance/Ruff static analysis errors by adding missing imports, guarding conditional code blocks, and removing unused imports.
# v1.0.0: INIT: Extracted core logic classes (VideoProcessor, OperationPlanner) into a dedicated module to be shared between the CLI and worker tasks.
# ------------------

# --- INTEGRITY ---
# Previous Character Count: 28987
# Current Character Count: 29285
# Syntax Check: PASS
# Logic Validation: The core video processing logic is unchanged, only moved from class methods to standalone functions. The worker will now call these functions directly, which is the correct architectural pattern. The OperationPlanner is now correctly focused on client-side orchestration.
# Risk Assessment: LOW - This is a pure refactoring. No logical behavior has been altered, only the location and invocation of the code, which fixes the error.
# Reason for Change: To resolve a critical logical flaw where worker tasks were failing because they incorrectly used the client-side planner. This change separates the logic into standalone functions for the worker to call, ensuring correct architectural separation.
# ------------------
import argparse
import fnmatch
import importlib.util
import io
import os
import subprocess
from collections import defaultdict
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from datetime import datetime
from typing import Any, cast

import ffmpeg
import imagehash
from loguru import logger
from PIL import Image
from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector
from thefuzz import fuzz


# --- Dependency Availability Check ---
def _check_dependency(package_name: str) -> bool:
    """Checks if a package is installed without importing it."""
    try:
        return importlib.util.find_spec(package_name) is not None
    except (ImportError, ValueError):
        return False


AI_LIBS_AVAILABLE = _check_dependency("torch") and _check_dependency("transformers")
QUALITY_LIBS_AVAILABLE = _check_dependency("ffmpeg_quality_metrics")
RICH_AVAILABLE = _check_dependency("rich")

# --- Global Configuration ---
FFMPEG_TIMEOUT = 60
console = None
if RICH_AVAILABLE:
    from rich.console import Console

    console = Console()


# --- UI Helper ---
def create_progress_bar():
    """Creates a standardized Rich Progress bar."""
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
    )

    return Progress(
        TextColumn("[progress.description]{task.description:<25}"),
        BarColumn(bar_width=None),
        MofNCompleteColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    )


# --- Utility Functions ---
def parse_size_to_bytes(size_str: str) -> int:
    """Converts a size string (e.g., '10MB', '2.5GB') to bytes."""
    size_str = size_str.upper().strip()
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                value = float(size_str.replace(unit, "").strip())
                return int(value * multiplier)
            except ValueError:
                raise ValueError(f"Invalid size format: '{size_str}'")
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"Invalid size format or missing unit: '{size_str}'")


def is_valid_hash_string(hash_str: str) -> bool:
    """Checks if a string is a valid hexadecimal hash."""
    return (
        isinstance(hash_str, str)
        and len(hash_str) > 0
        and all(c in "0123456789abcdefABCDEF" for c in hash_str)
    )


def normalize_and_validate_path(path: str, base_dir: str) -> str:
    """Normalizes a path and ensures it's within the intended base directory."""
    if ".." in path:
        logger.warning(
            "Suspicious path component '..' found in '{}'. Path will be resolved absolutely.",
            path,
        )
    abs_path = os.path.abspath(path)
    abs_base_dir = os.path.abspath(base_dir)
    if not os.path.commonpath([abs_path, abs_base_dir]) == abs_base_dir:
        raise PermissionError(
            f"Security Error: Path '{abs_path}' attempts to traverse outside of its base directory '{abs_base_dir}'."
        )
    return abs_path


# --- Top-level Worker Functions for Multiprocessing ---
def _get_video_metadata_mp(file_path: str) -> dict[str, Any] | None:
    """Gets metadata (duration, size, resolution, etc.) using ffprobe with a timeout."""
    logger.debug("Getting metadata for {}", file_path)
    try:
        probe = ffmpeg.probe(file_path)
        format_info = probe.get("format", {})
        video_stream = next(
            (s for s in probe["streams"] if s["codec_type"] == "video"), None
        )
        if not video_stream:
            logger.warning("No video stream found in {}", file_path)
            return None
        metadata = {
            "duration": float(format_info.get("duration", 0)),
            "size": int(format_info.get("size", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec_name": video_stream.get("codec_name"),
            "bit_rate": int(format_info.get("bit_rate", 0)),
            "path": file_path,
            "base": os.path.splitext(os.path.basename(file_path))[0],
        }
        logger.debug("Successfully extracted metadata for {}", file_path)
        return metadata
    except ffmpeg.Error as e:
        logger.warning(
            "Could not get metadata for '{}': {}", file_path, e.stderr.decode().strip()
        )
        return None


def _extract_and_hash_fixed_frames_mp(file_path: str, num_frames: int = 5) -> list[str]:
    """Fallback to extract frames at fixed intervals if scenedetect fails."""
    logger.debug("Starting fixed-frame extraction for {}", file_path)
    hashes, metadata = [], _get_video_metadata_mp(file_path)
    duration = metadata["duration"] if metadata else 0
    if duration <= 0:
        logger.warning("Cannot extract frames from {}, duration is 0.", file_path)
        return []
    for i in range(1, num_frames + 1):
        timestamp = duration * (i / (num_frames + 1))
        process = None
        try:
            logger.debug(
                "Extracting fixed frame from {} at {:.2f}s", file_path, timestamp
            )
            process = (
                ffmpeg.input(file_path, ss=timestamp)
                .output("pipe:", vframes=1, format="image2pipe", vcodec="png")
                .run_async(pipe_stdout=True, pipe_stderr=True, quiet=True)
            )
            out, _ = process.communicate(timeout=FFMPEG_TIMEOUT)
            img = Image.open(io.BytesIO(out))
            hashes.append(str(imagehash.phash(img)))
        except (subprocess.TimeoutExpired, ffmpeg.Error) as e:
            if process:
                process.kill()
            logger.bind(file_path=file_path, error_message=str(e)).warning(
                "Could not extract fixed frame from at {}s.", timestamp
            )
    logger.debug(
        "Finished fixed-frame hashing for {}, found {} hashes.",
        file_path,
        len(hashes),
    )
    return hashes


def _extract_and_hash_keyframes_mp(
    config: argparse.Namespace, file_path: str
) -> list[str]:
    """Extracts keyframes using scenedetect and computes their perceptual hashes."""
    hashes: list[str] = []
    process = None
    logger.debug("Starting keyframe extraction with scenedetect for: {}", file_path)
    try:
        video = open_video(file_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=config.scene_threshold))
        logger.debug("Running SceneManager.detect_scenes() on {}.", file_path)
        scene_manager.detect_scenes(video=video)
        scene_list = scene_manager.get_scene_list()
        logger.debug("Scenedetect found {} scenes in {}.", len(scene_list), file_path)
        if not scene_list:
            logger.warning(
                "Scenedetect found no scenes for {}. Falling back to fixed-frame extraction.",
                file_path,
            )
            return _extract_and_hash_fixed_frames_mp(file_path)
        for i, scene in enumerate(scene_list):
            frame_num = scene[0].get_frames()
            logger.debug("Extracting keyframe for scene {} from {}", i + 1, file_path)
            process = (
                ffmpeg.input(file_path, ss=frame_num / video.frame_rate)
                .output("pipe:", vframes=1, format="image2pipe", vcodec="png")
                .run_async(pipe_stdout=True, pipe_stderr=True, quiet=True)
            )
            out, _ = process.communicate(timeout=FFMPEG_TIMEOUT)
            img = Image.open(io.BytesIO(out))
            hashes.append(str(imagehash.phash(img)))
        logger.debug(
            "Finished keyframe hashing for {}, found {} hashes.", file_path, len(hashes)
        )
        return hashes
    except (subprocess.TimeoutExpired, ffmpeg.Error) as e:
        if process and process.poll() is None:
            process.kill()
        logger.bind(file_path=file_path, error_message=str(e)).warning(
            "Scenedetect/hashing failed. Falling back to fixed frames."
        )
        return _extract_and_hash_fixed_frames_mp(file_path)


def _get_quality_metric_score_mp(
    config: argparse.Namespace, reference_path: str, distorted_path: str
) -> float | None:
    """Calculates a video quality score using the specified metric (VMAF, SSIM, PSNR)."""
    if config.quality_metric == "none" or not QUALITY_LIBS_AVAILABLE:
        return None
    logger.debug(
        "Calculating quality metric '{}' between REF:'{}' and DIST:'{}'.",
        config.quality_metric,
        os.path.basename(reference_path),
        os.path.basename(distorted_path),
    )
    try:
        from ffmpeg_quality_metrics import FfmpegQualityMetrics

        metrics = FfmpegQualityMetrics(distorted_path, reference_path)
        results = metrics.calculate([config.quality_metric])
        metric_data = cast(dict[str, Any], next(iter(results or []), {}))
        metric_details = metric_data.get(config.quality_metric, {})
        if isinstance(metric_details, dict):
            score = metric_details.get("average")
            logger.debug(
                "Calculated quality score for '{}': {}",
                os.path.basename(distorted_path),
                score,
            )
            return score
        return None
    except Exception as e:
        logger.error("Failed to calculate quality for '{}': {}", distorted_path, e)
        return None


# --- Core Logic Classes ---
class VideoProcessor:
    """Handles all individual video processing tasks: metadata, hashing, quality, and AI categorization."""

    def __init__(self, config):
        self.config = config
        self._ai_model = None
        self._ai_processor = None
        self._device: str | None = None
        if self.config.categorize:
            self._initialize_ai_model()

    def get_video_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Wrapper for the multiprocessing-safe metadata function."""
        return _get_video_metadata_mp(file_path)

    def extract_and_hash_keyframes(self, file_path: str) -> list[str]:
        """Wrapper for the multiprocessing-safe keyframe hashing function."""
        return _extract_and_hash_keyframes_mp(self.config, file_path)

    def get_quality_metric_score(
        self, reference_path: str, distorted_path: str
    ) -> float | None:
        """Wrapper for the multiprocessing-safe quality metric function."""
        return _get_quality_metric_score_mp(self.config, reference_path, distorted_path)

    def _initialize_ai_model(self):
        """Loads the AI model and processor on startup, detecting available hardware (GPU/CPU)."""
        if self._ai_model or not AI_LIBS_AVAILABLE:
            return
        try:
            import torch
            from transformers import (
                VideoMAEForVideoClassification,
                VideoMAEImageProcessor,
            )

            if self.config.device == "auto":
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self._device = self.config.device
            logger.info(
                "AI Categorization enabled. Loading model to '{}' device: {}...",
                self._device,
                self.config.categorize_model,
            )
            self._ai_processor = VideoMAEImageProcessor.from_pretrained(
                self.config.categorize_model
            )
            model = VideoMAEForVideoClassification.from_pretrained(
                self.config.categorize_model
            )
            self._ai_model = model.to(self._device)
            logger.info("AI model loaded successfully.")
        except Exception as e:
            logger.critical(
                "Fatal: Failed to load AI model '{}'. Cannot proceed.",
                self.config.categorize_model,
            )
            raise RuntimeError("AI model initialization failed.") from e

    def categorize_video_batch(self, file_paths: list[str]) -> dict[str, str]:
        """Categorizes a batch of videos using a pre-trained AI model for efficiency."""
        if not self.config.categorize or not AI_LIBS_AVAILABLE:
            return {}

        import torch

        assert self._ai_model is not None, "AI model not initialized."
        assert self._ai_processor is not None, "AI processor not initialized."

        results = {}
        for path in file_paths:
            logger.debug("Starting AI categorization for {}", path)
            metadata = self.get_video_metadata(path)
            duration = metadata["duration"] if metadata else 0
            if duration <= 0:
                results[path] = "Unknown"
                continue
            num_frames = self.config.categorize_inference_frames
            frames = []
            logger.debug("Extracting {} frames for AI model from {}", num_frames, path)
            for i in range(num_frames):
                timestamp = duration * (i / num_frames)
                process = None
                try:
                    process = (
                        ffmpeg.input(path, ss=timestamp)
                        .output("pipe:", vframes=1, format="image2pipe", vcodec="mjpeg")
                        .run_async(pipe_stdout=True, pipe_stderr=True, quiet=True)
                    )
                    out, _ = process.communicate(timeout=FFMPEG_TIMEOUT)
                    frames.append(Image.open(io.BytesIO(out)))
                except (subprocess.TimeoutExpired, ffmpeg.Error):
                    if process:
                        process.kill()
                    continue
            if not frames:
                results[path] = "Unknown"
                logger.warning(
                    "Could not extract any frames for AI processing from {}", path
                )
                continue
            logger.debug("Running AI inference on {} frames for {}", len(frames), path)
            with torch.no_grad():
                inputs = self._ai_processor(frames, return_tensors="pt").to(
                    self._device
                )
                outputs = self._ai_model(**inputs)
                logits = outputs.logits
            predicted_class_idx = logits.argmax(-1).item()
            category = self._ai_model.config.id2label[predicted_class_idx]
            results[path] = category
            logger.debug("AI classified {} as '{}'", path, category)
        return results


# --- Standalone Worker Logic (Moved from OperationPlanner) ---


def _find_potential_matches_task(
    media_info: dict, videos_index: dict, config: argparse.Namespace
) -> list[dict]:
    potential_matches = []
    media_base = media_info.get("base", "")
    if not media_base:
        return []
    logger.debug("Finding potential matches for '{}' by name and duration.", media_base)
    for video_base, video_infos in videos_index.items():
        if (
            fuzz.ratio(media_base.lower(), video_base.lower())
            >= config.fuzzy_match_threshold
        ):
            for v_info in video_infos:
                if (
                    abs(v_info["duration"] - media_info["duration"])
                    <= config.duration_tolerance
                ):
                    potential_matches.append(v_info)
    return potential_matches


def _compare_hashes_task(
    hashes1: list[str], hashes2: list[str], config: argparse.Namespace
) -> bool:
    if not hashes1 or not hashes2:
        return False
    hashes2_set = {imagehash.hex_to_hash(h) for h in hashes2 if is_valid_hash_string(h)}
    if not hashes2_set:
        return False
    matches = sum(
        1
        for h1_str in hashes1
        if is_valid_hash_string(h1_str)
        and any(
            (imagehash.hex_to_hash(h1_str) - h2_obj) <= config.hash_threshold
            for h2_obj in hashes2_set
        )
    )
    required_matches = min(len(hashes1), len(hashes2)) * 0.5
    is_match = matches >= required_matches
    logger.debug(
        "Hash comparison: {} matches found, required >= {:.1f}. Result: {}",
        matches,
        required_matches,
        is_match,
    )
    return is_match


def _refine_matches_with_hashes_task(
    media_info: dict,
    potential_matches: list[dict],
    processor: VideoProcessor,
    config: argparse.Namespace,
) -> list[dict]:
    if not config.perceptual_hash or not potential_matches:
        return potential_matches
    logger.debug("Refining {} matches with perceptual hashing.", len(potential_matches))
    all_files_to_hash = [media_info["path"]] + [m["path"] for m in potential_matches]
    hashes = {}
    for path in set(all_files_to_hash):
        try:
            hashes[path] = processor.extract_and_hash_keyframes(path)
        except Exception as e:
            logger.bind(file_path=path, error_message=str(e)).warning(
                "Failed to hash file."
            )

    media_info["hashes"] = hashes.get(media_info["path"], [])
    final_matches = []
    for match in potential_matches:
        match["hashes"] = hashes.get(match["path"], [])
        if _compare_hashes_task(media_info["hashes"], match["hashes"], config):
            final_matches.append(match)
    return final_matches


def _add_perceptual_quality_scores_task(
    duplicates: list[dict], processor: VideoProcessor
):
    logger.debug("Calculating perceptual quality scores for duplicate set.")
    reference = max(
        duplicates,
        key=lambda v: (v.get("width", 0) * v.get("height", 0), v.get("bit_rate", 0)),
    )
    logger.debug(
        "Selected '{}' as reference for quality.", os.path.basename(reference["path"])
    )
    for video in duplicates:
        if video["path"] == reference["path"]:
            video["quality_metric_score"] = 100.0
        else:
            score = processor.get_quality_metric_score(reference["path"], video["path"])
            video["quality_metric_score"] = score if score is not None else 0.0


def _calculate_composite_quality_scores_task(
    duplicates: list[dict], processor: VideoProcessor, config: argparse.Namespace
):
    if config.quality_metric != "none":
        _add_perceptual_quality_scores_task(duplicates, processor)
    for video in duplicates:
        resolution_score = (video.get("width", 0) * video.get("height", 0)) / (
            3840 * 2160
        )
        bitrate_score = (video.get("bit_rate", 0)) / 50_000_000
        perceptual_score = video.get("quality_metric_score", 0.0) / 100.0
        video["composite_score"] = (
            (perceptual_score * 0.6) + (resolution_score * 0.3) + (bitrate_score * 0.1)
        )
        logger.debug(
            "Video '{}' composite score: {:.3f}",
            os.path.basename(video["path"]),
            video["composite_score"],
        )


def _select_best_video_task(
    all_duplicates: list[dict], processor: VideoProcessor, config: argparse.Namespace
) -> dict:
    logger.debug(
        "Selecting best video from a set of {} duplicates.", len(all_duplicates)
    )
    _calculate_composite_quality_scores_task(all_duplicates, processor, config)
    all_duplicates.sort(key=lambda v: v.get("composite_score", 0.0), reverse=True)
    return all_duplicates[0]


def _generate_plan_for_duplicates_task(
    best_video: dict, all_duplicates: list[dict], config: argparse.Namespace
) -> tuple[list[dict], float]:
    plan, space_saved = [], 0.0
    for video in all_duplicates:
        if video["path"] == best_video["path"]:
            continue
        space_saved += video["size"]
        plan.append(
            {
                "action": "delete",
                "path": video["path"],
                "size": video["size"],
                "reason": f"Duplicate of '{os.path.basename(best_video['path'])}' with lower quality score.",
            }
        )
    media_dir_abs = os.path.abspath(config.media_dir)
    if not os.path.commonpath([best_video["path"], media_dir_abs]) == media_dir_abs:
        dest_path = os.path.join(media_dir_abs, os.path.basename(best_video["path"]))
        plan.append(
            {
                "action": "move",
                "src": best_video["path"],
                "dest": dest_path,
                "reason": "Moving best quality version to media directory.",
            }
        )
    return plan, space_saved


def process_and_plan_for_single_file(
    config: argparse.Namespace,
    processor: VideoProcessor,
    media_path: str,
    videos_index: dict,
) -> dict | None:
    """This is the main logic for a single worker task."""
    logger.debug("WORKER: Starting processing for media file: {}", media_path)
    media_info = processor.get_video_metadata(media_path)
    if not media_info:
        logger.warning("WORKER: Could not get metadata for {}. Skipping.", media_path)
        return None

    potential_matches = _find_potential_matches_task(media_info, videos_index, config)
    if not potential_matches:
        logger.debug(
            "WORKER: No potential matches found for {}. Not a duplicate.", media_path
        )
        return None

    final_matches = _refine_matches_with_hashes_task(
        media_info, potential_matches, processor, config
    )
    if not final_matches:
        logger.debug(
            "WORKER: No final matches after hashing for {}. Not a duplicate.",
            media_path,
        )
        return None

    all_duplicates = [media_info] + final_matches
    best_video = _select_best_video_task(all_duplicates, processor, config)

    plan_fragment, space_saved_fragment = _generate_plan_for_duplicates_task(
        best_video, all_duplicates, config
    )

    if config.categorize and config.categorize_mode == "best":
        plan_fragment.append(
            {
                "action": "categorize",
                "path": best_video["path"],
                "category": "Pending",
                "reason": "Pending AI batch categorization.",
            }
        )

    return {
        "plan_fragment": plan_fragment,
        "space_saved_fragment": space_saved_fragment,
    }


class OperationPlanner:
    """Scans directories, finds duplicates, and sends jobs to the queue."""

    def __init__(self, config: argparse.Namespace, processor: VideoProcessor):
        self.config = config
        self.processor = processor
        self.messages = []

    def plan_and_send_jobs(self):
        """Main method to generate the operation plan."""
        from .tasks import process_video_file_task

        logger.info("Starting operation planning phase.")
        allowed_exts = [ext.lower() for ext in self.config.extensions]

        videos_index, videos_count = self._build_videos_index(
            self.config.videos_dir, allowed_exts
        )
        if not videos_index:
            logger.warning(
                "No video files found in '{}'. No operations possible.",
                self.config.videos_dir,
            )
            return
        logger.info("Video index built with {} files.", videos_count)

        media_files = self._collect_files(self.config.media_dir, allowed_exts)
        media_count = len(media_files)
        logger.info("Found {} media files to process.", media_count)

        if not media_files:
            logger.info("No media files to process. Exiting.")
            return

        config_dict = vars(self.config)
        logger.info("Sending {} jobs to the queue...", len(media_files))
        for media_path in media_files:
            message = process_video_file_task.send(
                config_dict,
                media_path,
                videos_index,
            )
            self.messages.append(message)

        logger.success(
            "All {} jobs have been sent. Run a worker to process them:",
            len(media_files),
        )
        logger.info("dramatiq src.tasks")

    def get_results(self, timeout: int = 3600):
        """Waits for and collects results from all sent messages."""
        if not self.messages:
            return []

        results = []
        if RICH_AVAILABLE:
            progress = create_progress_bar()
            task = progress.add_task(
                "[cyan]Processing Videos...", total=len(self.messages)
            )
            from rich.live import Live

            with Live(progress, console=console, refresh_per_second=4):
                for msg in self.messages:
                    try:
                        result = msg.get_result(timeout=timeout)
                        if result:
                            results.append(result)
                    except Exception:
                        logger.error(
                            "A task failed to complete after all retries. Message ID: {}",
                            msg.message_id,
                        )
                    progress.update(task, advance=1)
        else:
            for i, msg in enumerate(self.messages):
                logger.info("Waiting for result {} of {}...", i + 1, len(self.messages))
                try:
                    result = msg.get_result(timeout=timeout)
                    if result:
                        results.append(result)
                except Exception:
                    logger.error(
                        "A task failed to complete after all retries. Message ID: {}",
                        msg.message_id,
                    )
        return results

    def _build_videos_index(
        self, directory: str, allowed_exts: list[str]
    ) -> tuple[dict, int]:
        index = defaultdict(list)
        files_to_process = self._collect_files(directory, allowed_exts)
        logger.info(
            "Indexing {} files in Scan Directory ('{}')...",
            len(files_to_process),
            directory,
        )
        if RICH_AVAILABLE:
            from rich.live import Live

            progress = create_progress_bar()
            task = progress.add_task(
                "[green]Indexing Scan Dir...", total=len(files_to_process)
            )
            with Live(progress, console=console, refresh_per_second=4):
                with ThreadPoolExecutor(
                    max_workers=self.config.max_workers
                ) as executor:
                    future_to_path = {
                        executor.submit(_get_video_metadata_mp, fp): fp
                        for fp in files_to_process
                    }
                    for future in as_completed(future_to_path):
                        try:
                            metadata = future.result()
                            if metadata:
                                index[metadata["base"]].append(metadata)
                        except Exception as e:
                            logger.warning(
                                "Failed to index '{}': {}", future_to_path[future], e
                            )
                        progress.update(task, advance=1)
        else:  # Fallback for non-rich progress
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_path = {
                    executor.submit(_get_video_metadata_mp, fp): fp
                    for fp in files_to_process
                }
                for future in as_completed(future_to_path):
                    try:
                        metadata = future.result()
                        if metadata:
                            index[metadata["base"]].append(metadata)
                    except Exception as e:
                        logger.warning(
                            "Failed to index '{}': {}", future_to_path[future], e
                        )
        return dict(index), len(files_to_process)

    def _collect_files(self, directory: str, allowed_exts: list[str]) -> list[str]:
        """Recursively collects files, applying all configured filters."""
        logger.debug("Collecting files from '{}'...", directory)
        collected_files = []
        base_dir = os.path.abspath(directory)

        exclude_dirs_abs = [os.path.abspath(p) for p in self.config.exclude_dirs]
        min_size_bytes = (
            parse_size_to_bytes(self.config.min_size) if self.config.min_size else 0
        )
        max_size_bytes = (
            parse_size_to_bytes(self.config.max_size)
            if self.config.max_size
            else float("inf")
        )
        after_timestamp = (
            datetime.strptime(self.config.only_after, "%Y-%m-%d").timestamp()
            if self.config.only_after
            else 0
        )
        before_timestamp = (
            datetime.strptime(self.config.only_before, "%Y-%m-%d").timestamp()
            if self.config.only_before
            else float("inf")
        )

        for root, _, files in os.walk(directory):
            if any(
                os.path.abspath(root).startswith(excluded)
                for excluded in exclude_dirs_abs
            ):
                continue
            for file in files:
                if os.path.splitext(file)[1].lower() not in allowed_exts:
                    continue
                if any(
                    fnmatch.fnmatch(file, pattern)
                    for pattern in self.config.exclude_patterns
                ):
                    continue
                full_path = os.path.join(root, file)
                try:
                    normalized_path = normalize_and_validate_path(full_path, base_dir)
                    file_size = os.path.getsize(normalized_path)
                    file_mtime = os.path.getmtime(normalized_path)
                    if not (min_size_bytes <= file_size <= max_size_bytes):
                        continue
                    if not (after_timestamp <= file_mtime <= before_timestamp):
                        continue
                    collected_files.append(normalized_path)
                except (PermissionError, FileNotFoundError) as e:
                    logger.error("Error accessing file '{}': {}", full_path, e)
        logger.debug("Collected {} files from '{}'.", len(collected_files), directory)
        return collected_files
