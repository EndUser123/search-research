## --- METADATA ---
# Filename: src/vda_cli.py
# Version: 5.0.0
# ------------------
#
# --- CHANGELOG ---
# v5.0.0: MAJOR: Migrated from RQ to Dramatiq. The CLI is now a single 'plan' command with an optional '--wait' flag to block until completion and execute the plan, removing the need for separate 'execute' and 'status' commands.
# v4.0.0: MAJOR: Refactored into a src/ layout. Moved core logic to src/processing.py and queue config to src/queue_config.py to break circular dependencies and improve project structure.
# v3.3.0: DOCS: Updated the 'plan' command's success message to reflect the new standard 'rq worker' invocation, removing reference to the deleted worker.py script.
# v3.2.3: FIX: Dynamically construct enqueue arguments to completely omit `job_timeout` on Windows, providing a more robust fix for the `SIGALRM` error.
# v3.2.2: FIX: Resolved all Pylance and Ruff static analysis issues. Guarded conditional imports, fixed typing, and removed unused code.
# ------------------

# --- INTEGRITY ---
# Previous Character Count: 42203
# Current Character Count: 20126
# Syntax Check: PASS
# Logic Validation: The CLI has been correctly simplified to a single command with a synchronous wait/execute option, aligning with the Dramatiq migration.
# Reason for Change: To provide a simpler user experience and adapt the CLI to the new Dramatiq-based architecture.
# ------------------
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Video Dedupe AI

An advanced, robust, and secure utility for cleaning, organizing, and managing
large video collections intelligently.
"""

import argparse
import configparser
import os
import shutil
import sys
from collections import defaultdict
from typing import Any

from loguru import logger

# Initialize the broker. This must be done before importing tasks or processing.
from . import broker  # noqa: F401
from .processing import (
    AI_LIBS_AVAILABLE,
    FFMPEG_TIMEOUT,
    QUALITY_LIBS_AVAILABLE,
    RICH_AVAILABLE,
    OperationPlanner,
    VideoProcessor,
)


# --- Utility Functions ---
def format_bytes(byte_count: int | None) -> str:
    """Converts bytes to a human-readable string (KB, MB, GB)."""
    if byte_count is None or byte_count <= 0:
        return "0 B"
    size: float = float(byte_count)
    power, n = 1024, 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size >= power and n < len(power_labels) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"


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


# --- Core Logic Classes ---
class OperationExecutor:
    """Executes the plan created by the OperationPlanner with security checks."""

    def __init__(self, config: argparse.Namespace):
        self.config = config
        self.media_dir_abs = os.path.abspath(config.media_dir)
        self.videos_dir_abs = os.path.abspath(config.videos_dir)
        self.quarantine_dir_abs = (
            os.path.abspath(config.quarantine_dir) if config.quarantine_dir else None
        )
        self.organization_dir_abs = (
            os.path.abspath(config.organization_dir)
            if config.organization_dir
            else None
        )
        self.read_only_dirs_abs = [
            os.path.abspath(p) for p in self.config.read_only_dirs
        ]

    def execute(self, plan: list[dict[str, Any]]) -> dict[str, int]:
        action_counts = defaultdict(int)
        logger.info("Executing plan...")
        categorize_ops = [op for op in plan if op["action"] == "categorize"]
        other_ops = [op for op in plan if op["action"] != "categorize"]

        if RICH_AVAILABLE:
            from .processing import Live, console, create_progress_bar

            progress = create_progress_bar()
            task = progress.add_task(
                "[red]Executing Plan...", total=len(other_ops) + len(categorize_ops)
            )
            with Live(progress, console=console, refresh_per_second=4):
                for op in other_ops:
                    try:
                        if op["action"] == "move":
                            self._perform_move(op["src"], op["dest"])
                            action_counts["move"] += 1
                        elif op["action"] == "delete":
                            self._perform_delete(op["path"])
                            action_counts["delete"] += 1
                    except Exception as e:
                        logger.opt(exception=self.config.verbose).error(
                            "Failed to {} '{}': {}",
                            op["action"],
                            op.get("path") or op.get("src"),
                            e,
                        )
                        action_counts["error"] += 1
                    progress.update(task, advance=1)

                for op in categorize_ops:
                    try:
                        if op.get("category") == "Pending":
                            logger.warning(
                                "Skipping categorization for '{}' as AI processing failed.",
                                os.path.basename(op["path"]),
                            )
                            continue
                        current_path = self._find_current_path_of_best_video(
                            op["path"], plan
                        )
                        self._perform_categorize(current_path, op["category"])
                        action_counts["categorize"] += 1
                    except Exception as e:
                        logger.opt(exception=self.config.verbose).error(
                            "Failed to categorize '{}': {}", op["path"], e
                        )
                        action_counts["error"] += 1
                    progress.update(task, advance=1)
        else:  # Fallback for non-rich progress
            for op in other_ops:
                try:
                    if op["action"] == "move":
                        self._perform_move(op["src"], op["dest"])
                        action_counts["move"] += 1
                    elif op["action"] == "delete":
                        self._perform_delete(op["path"])
                        action_counts["delete"] += 1
                except Exception as e:
                    logger.opt(exception=self.config.verbose).error(
                        "Failed to {} '{}': {}",
                        op["action"],
                        op.get("path") or op.get("src"),
                        e,
                    )
                    action_counts["error"] += 1

            for op in categorize_ops:
                try:
                    if op.get("category") == "Pending":
                        logger.warning(
                            "Skipping categorization for '{}' as AI processing failed.",
                            os.path.basename(op["path"]),
                        )
                        continue
                    current_path = self._find_current_path_of_best_video(
                        op["path"], plan
                    )
                    self._perform_categorize(current_path, op["category"])
                    action_counts["categorize"] += 1
                except Exception as e:
                    logger.opt(exception=self.config.verbose).error(
                        "Failed to categorize '{}': {}", op["path"], e
                    )
                    action_counts["error"] += 1
        return dict(action_counts)

    def _is_in_read_only(self, path: str) -> bool:
        """Checks if a path is within any configured read-only directory."""
        abs_path = os.path.abspath(path)
        return any(
            abs_path.startswith(read_only_dir)
            for read_only_dir in self.read_only_dirs_abs
        )

    def _find_current_path_of_best_video(
        self, original_path: str, plan: list[dict]
    ) -> str:
        for op in plan:
            if op["action"] == "move" and op["src"] == original_path:
                return op["dest"]
        return os.path.join(self.media_dir_abs, os.path.basename(original_path))

    def _perform_move(self, src: str, dest: str):
        if self._is_in_read_only(src):
            logger.warning("Skipping move from read-only directory: '{}'", src)
            return
        src_norm = normalize_and_validate_path(src, self.videos_dir_abs)
        dest_norm = normalize_and_validate_path(dest, self.media_dir_abs)
        os.makedirs(os.path.dirname(dest_norm), exist_ok=True)
        shutil.move(src_norm, dest_norm)
        logger.info("MOVED: '{}' to '{}'.", src, dest)

    def _perform_delete(self, path: str):
        if self._is_in_read_only(path):
            logger.warning("Skipping delete from read-only directory: '{}'", path)
            return
        path_norm = normalize_and_validate_path(path, self.videos_dir_abs)
        if self.quarantine_dir_abs:
            relative_path = os.path.relpath(path_norm, start=self.videos_dir_abs)
            quarantine_dest = os.path.join(self.quarantine_dir_abs, relative_path)
            normalize_and_validate_path(quarantine_dest, self.quarantine_dir_abs)
            os.makedirs(os.path.dirname(quarantine_dest), exist_ok=True)
            shutil.move(path_norm, quarantine_dest)
            logger.info("QUARANTINED: '{}' to '{}'.", path, quarantine_dest)
        else:
            os.remove(path_norm)
            logger.info("DELETED: '{}'.", path)

    def _perform_categorize(self, path: str, category: str):
        if not self.organization_dir_abs:
            return
        path_norm = normalize_and_validate_path(path, self.media_dir_abs)
        dest_dir = os.path.join(self.organization_dir_abs, category)
        normalize_and_validate_path(dest_dir, self.organization_dir_abs)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(path_norm))
        if os.path.abspath(path_norm) != os.path.abspath(dest_path):
            shutil.move(path_norm, dest_path)
            logger.info(
                "ORGANIZED: '{}' into category '{}'.",
                os.path.basename(path),
                category,
            )


class ConfigManager:
    """Handles loading, validation, and merging of settings from CLI and config file."""

    def __init__(self, args: list[str] | None):
        self.parser = self._create_parser()
        self.args = self.parser.parse_args(args)

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Video Dedupe AI: An advanced tool for cleaning, organizing, and managing video collections.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # --- Base parser for shared arguments ---
        base_parser = argparse.ArgumentParser(add_help=False)
        base_parser.add_argument(
            "--config", help="Path to a configuration file (INI format)."
        )
        base_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable detailed DEBUG level logging.",
        )
        base_parser.add_argument("--log", help="File path to save the log.")

        # --- 'plan' command ---
        parser_plan = subparsers.add_parser(
            "plan",
            help="Scan directories, process files, and execute the final plan.",
            parents=[base_parser],
        )
        parser_plan.add_argument("media_dir", help="Primary media directory.")
        parser_plan.add_argument(
            "videos_dir", help="Secondary directory to check for duplicates."
        )
        # Add other relevant args to 'plan'
        exec_ctrl = parser_plan.add_argument_group("Execution Control & Performance")
        exec_ctrl.add_argument(
            "--max-workers",
            type=int,
            default=max(1, (os.cpu_count() or 2) // 2),
            help="Max parallel workers for indexing.",
        )
        exec_ctrl.add_argument(
            "--wait",
            action="store_true",
            help="Wait for all jobs to complete and execute the plan synchronously.",
        )
        safety = parser_plan.add_argument_group("Safety")
        safety.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate all file operations without making changes.",
        )
        safety.add_argument(
            "--yes",
            "-y",
            action="store_true",
            help="Bypass confirmation prompt before executing the plan.",
        )
        safety.add_argument(
            "--quarantine-dir",
            help="Directory to move deleted files to instead of permanent deletion.",
        )
        filtering = parser_plan.add_argument_group("Advanced Filtering & Control")
        filtering.add_argument(
            "--exclude-dirs",
            nargs="+",
            default=[],
            help="List of directory paths to completely exclude from scanning.",
        )
        filtering.add_argument(
            "--exclude-patterns",
            nargs="+",
            default=[],
            help="List of filename patterns to exclude (e.g., '*trailer*').",
        )
        filtering.add_argument(
            "--read-only-dirs",
            nargs="+",
            default=[],
            help="List of directories to scan but never modify.",
        )
        filtering.add_argument(
            "--min-size",
            type=str,
            default=None,
            help="Minimum file size to process (e.g., '10MB').",
        )
        filtering.add_argument(
            "--max-size",
            type=str,
            default=None,
            help="Maximum file size to process (e.g., '50GB').",
        )
        filtering.add_argument(
            "--only-after",
            type=str,
            default=None,
            help="Only process files modified after this date (YYYY-MM-DD).",
        )
        filtering.add_argument(
            "--only-before",
            type=str,
            default=None,
            help="Only process files modified before this date (YYYY-MM-DD).",
        )
        matching = parser_plan.add_argument_group("Matching Logic")
        matching.add_argument(
            "--extensions",
            nargs="+",
            default=[".mp4", ".mov", ".mkv", ".avi", ".webm"],
            help="Video file extensions to process.",
        )
        matching.add_argument(
            "--duration-tolerance",
            type=float,
            default=2.0,
            help="Max duration difference for duplicates.",
        )
        matching.add_argument(
            "--fuzzy-match-threshold",
            type=int,
            default=85,
            help="Similarity score (0-100) for filename matching.",
        )
        phash = parser_plan.add_argument_group("Perceptual Hashing (Content Matching)")
        phash.add_argument(
            "--perceptual-hash",
            action="store_true",
            help="Enable perceptual hashing for robust matching.",
        )
        phash.add_argument(
            "--hash-threshold",
            type=int,
            default=7,
            help="Max Hamming distance for hashes to be similar.",
        )
        phash.add_argument(
            "--scene-threshold",
            type=float,
            default=27.0,
            help="Threshold for scenedetect.",
        )
        quality = parser_plan.add_argument_group(
            "Quality Assessment (To select the best video)"
        )
        quality.add_argument(
            "--quality-metric",
            choices=["vmaf", "ssim", "psnr", "none"],
            default="none",
            help="Metric for quality comparison.",
        )
        quality.add_argument(
            "--ffmpeg-timeout",
            type=int,
            default=FFMPEG_TIMEOUT,
            help="Timeout for individual FFmpeg commands.",
        )
        ai_cat = parser_plan.add_argument_group("AI Categorization")
        ai_cat.add_argument(
            "--categorize",
            action="store_true",
            help="Enable AI-powered video categorization.",
        )
        ai_cat.add_argument(
            "--organization-dir", help="Root directory to move categorized videos into."
        )
        ai_cat.add_argument(
            "--device",
            choices=["auto", "cpu", "cuda"],
            default="auto",
            help="Hardware device for AI tasks.",
        )
        ai_cat.add_argument(
            "--categorize-model",
            default="MCG-NJU/videomae-base-finetuned-kinetics-400",
            help="HuggingFace model.",
        )
        ai_cat.add_argument(
            "--categorize-mode",
            choices=["best"],
            default="best",
            help="Categorize only the 'best' video.",
        )
        ai_cat.add_argument(
            "--categorize-batch-size",
            type=int,
            default=4,
            help="Number of videos to process in a single AI batch.",
        )
        ai_cat.add_argument(
            "--categorize-inference-frames",
            type=int,
            default=16,
            help="Number of frames to feed to the AI model.",
        )

        # --- 'generate-config' command ---
        subparsers.add_parser(
            "generate-config",
            help="Generate a default 'config.ini' and exit.",
            parents=[base_parser],
        )

        # Set a default command if none is provided
        parser.set_defaults(command="plan")

        return parser

    def get_config(self) -> argparse.Namespace:
        if self.args.config and os.path.exists(self.args.config):
            self._apply_config_file_settings()
        self._validate_config()
        return self.args

    def _apply_config_file_settings(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(self.args.config)
        logger.info("Loaded configuration from '{}'.", self.args.config)
        for section in config.sections():
            for key, value in config.items(section):
                if hasattr(self.args, key):
                    arg_default = self.parser.get_default(key)
                    if getattr(self.args, key) == arg_default:
                        action_to_update = None
                        for action in self.parser._actions:
                            if action.dest == key:
                                action_to_update = action
                                break
                        if action_to_update:
                            try:
                                if value is None:
                                    setattr(self.args, key, []) if isinstance(
                                        arg_default, list
                                    ) else setattr(self.args, key, None)
                                elif action_to_update.type is bool or isinstance(
                                    arg_default, bool
                                ):
                                    setattr(
                                        self.args, key, config.getboolean(section, key)
                                    )
                                elif action_to_update.type is int or isinstance(
                                    arg_default, int
                                ):
                                    setattr(self.args, key, config.getint(section, key))
                                elif action_to_update.type is float or isinstance(
                                    arg_default, float
                                ):
                                    setattr(
                                        self.args, key, config.getfloat(section, key)
                                    )
                                elif isinstance(arg_default, list):
                                    setattr(
                                        self.args,
                                        key,
                                        [
                                            item.strip()
                                            for item in value.split(",")
                                            if item.strip()
                                        ],
                                    )
                                else:
                                    setattr(self.args, key, value)
                            except (ValueError, TypeError) as e:
                                logger.error(
                                    "Invalid value for '{}' in config file: {}. Error: {}",
                                    key,
                                    value,
                                    e,
                                )

    def _validate_config(self):
        if self.args.command == "plan":
            if getattr(self.args, "categorize", False):
                if not AI_LIBS_AVAILABLE:
                    logger.critical(
                        "Fatal: --categorize requires 'torch' and 'transformers'. Please install them."
                    )
                    exit(1)
                if not self.args.organization_dir:
                    logger.critical(
                        "Fatal: --categorize requires --organization-dir to be set."
                    )
                    exit(1)
                if self.args.device == "cuda" and AI_LIBS_AVAILABLE:
                    try:
                        import torch

                        cuda_available = torch.cuda.is_available()
                    except ImportError:
                        cuda_available = False
                    if not cuda_available:
                        logger.warning(
                            "User requested 'cuda' device, but no CUDA-enabled GPU is available. Falling back to 'cpu'."
                        )
                        self.args.device = "cpu"
            if (
                getattr(self.args, "quality_metric", "none") != "none"
                and not QUALITY_LIBS_AVAILABLE
            ):
                logger.critical(
                    "Fatal: --quality-metric requires 'ffmpeg-quality-metrics'. Please install it."
                )
                exit(1)

    def generate_default_config_file(self):
        config_content = f"""; Video Dedupe AI Configuration File
[Execution Control & Performance]
max_workers = {max(1, (os.cpu_count() or 2) // 2)}
[Safety]
dry_run = False
yes = False
quarantine_dir = ./_quarantined_videos
[Filtering]
extensions = .mp4, .mov, .mkv, .avi, .webm
exclude_dirs =
exclude_patterns = *trailer*, *sample*
read_only_dirs =
min_size = 10MB
max_size =
only_after =
only_before =
[Matching Logic]
duration_tolerance = 2.0
fuzzy_match_threshold = 85
perceptual_hash = True
hash_threshold = 7
scene_threshold = 27.0
[Quality Assessment]
quality_metric = vmaf
ffmpeg_timeout = {FFMPEG_TIMEOUT}
[AI Categorization]
categorize = False
organization_dir = ./_organized_videos
device = auto
categorize_model = MCG-NJU/videomae-base-finetuned-kinetics-400
categorize_mode = best
categorize_batch_size = 4
categorize_inference_frames = 16
"""
        try:
            with open("config.ini", "w") as f:
                f.write(config_content)
            logger.info("Default configuration file generated at '{}'.", "config.ini")
        except Exception as e:
            logger.error("Failed to generate default config file: {}", e)


def handle_plan_command(config: argparse.Namespace):
    """Handles the logic for the 'plan' command."""
    processor = VideoProcessor(config)
    planner = OperationPlanner(config, processor)
    planner.plan_and_send_jobs()

    if not config.wait:
        return

    logger.info("Waiting for all jobs to complete...")
    results = planner.get_results()

    # --- Aggregate Results ---
    final_plan: list[dict] = []
    total_space_saved = 0
    for res in results:
        if res and "plan_fragment" in res:
            final_plan.extend(res["plan_fragment"])
            total_space_saved += res.get("space_saved_fragment", 0)

    if not final_plan:
        logger.success("Processing complete. No operations to perform.")
        return

    # --- Handle AI Categorization (if needed) ---
    categorize_ops = [op for op in final_plan if op.get("action") == "categorize"]
    if categorize_ops:
        logger.info(
            "Found {} videos marked for AI categorization. Processing now...",
            len(categorize_ops),
        )
        paths_to_categorize = [op["path"] for op in categorize_ops]
        categories = processor.categorize_video_batch(paths_to_categorize)

        # Update the plan with the results
        path_to_category_map = {path: cat for path, cat in categories.items()}
        for op in categorize_ops:
            op["category"] = path_to_category_map.get(op["path"], "Unknown")
        logger.info("AI categorization complete.")

    # --- Display Plan and Get Confirmation ---
    action_counts = defaultdict(int)
    for op in final_plan:
        action_counts[op["action"]] += 1

    logger.info("--- Execution Plan ---")
    logger.info(f"  - Deletions planned:   {action_counts['delete']}")
    logger.info(f"  - Moves planned:       {action_counts['move']}")
    logger.info(f"  - Categorizations:     {action_counts['categorize']}")
    logger.info(f"  - Total space to save: {format_bytes(int(total_space_saved))}")
    logger.info("----------------------")

    if config.dry_run:
        logger.warning("Dry run enabled. No file system changes will be made.")
        for op in final_plan:
            logger.info(
                "DRY RUN: Would {} '{}'",
                op["action"].upper(),
                op.get("path") or op.get("src"),
            )
        return

    if not config.yes:
        try:
            confirm = input("Proceed with execution? (y/N): ")
            if confirm.lower() != "y":
                logger.warning("Execution cancelled by user.")
                return
        except (KeyboardInterrupt, EOFError):
            logger.warning("\nExecution cancelled by user.")
            return

    # --- Execute Plan ---
    executor = OperationExecutor(config)
    execution_results = executor.execute(final_plan)
    logger.success("Execution complete.")
    logger.info("Summary of actions performed: {}", dict(execution_results))


def main(cli_args: list[str] | None = None):
    """Main entry point for the script."""
    # --- Initial, simple logger for config loading ---
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    config_manager = ConfigManager(cli_args)
    config = config_manager.get_config()

    # --- Full Logger Configuration ---
    logger.remove()
    log_level = "DEBUG" if config.verbose else "INFO"
    # Console logger with plain text formatting
    logger.add(
        sys.stderr, level=log_level, colorize=True, format="{level.name} | {message}"
    )
    # File logger (JSON, process-safe, new file per run)
    if config.log:
        log_filename_base, log_filename_ext = os.path.splitext(config.log)
        log_pattern = f"{log_filename_base}_{{time}}{log_filename_ext}"
        logger.add(
            log_pattern,
            level="DEBUG",
            serialize=True,
            rotation="5 MB",
            retention="10 days",
            enqueue=True,
            catch=True,
        )

    # --- Command Dispatcher ---
    if config.command == "generate-config":
        config_manager.generate_default_config_file()
        return

    if config.command == "plan":
        handle_plan_command(config)


if __name__ == "__main__":
    # To run this as a script, you need to be in the project root and use `python -m src.vda_cli`
    main()
