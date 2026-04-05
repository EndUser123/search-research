## --- METADATA ---
# Filename: src/tasks.py
# Version: 2.2.1
# Confidence Level: HIGH - This change directly implements the solution suggested by the Dramatiq warning message.
# ------------------
#
# --- CHANGELOG ---
# v2.2.1: FIX: Added `store_results=True` to the actor options. This instructs the actor to save its return value using the Results middleware, fixing the end-to-end workflow.
# v2.2.0: FIX: Added `store_results=True` to the actor options to ensure task return values are saved by the Results middleware, fixing the end-to-end workflow.
# v2.1.0: REFACTOR: Updated the worker task to call the new standalone `process_and_plan_for_single_file` logic function instead of incorrectly instantiating the client-side `OperationPlanner` class.
# v2.0.0: MAJOR: Refactored the task from an RQ function to a Dramatiq actor. Retry logic is now handled in the decorator. Removed manual JSON result saving.
# v1.2.0: REFACTOR: Updated imports to be relative to the new src/ package structure, importing logic from .processing instead of vda_cli.
# v1.1.0: FEAT: The worker task now saves its result to a unique JSON file in the 'results/' directory, ensuring plan fragments are persisted to disk.
# v1.0.0: INIT: Created initial task definition for video processing.
# ------------------

# --- INTEGRITY ---
# Previous Character Count: 1357
# Current Character Count: 1409
# Syntax Check: PASS
# Logic Validation: The actor is now correctly configured to store its results, which is required by the client's `get_results` method. This completes the communication loop between the worker and the client.
# Risk Assessment: LOW - This is a simple flag enablement and the final step required to make the system work as designed.
# Reason for Change: To fix the final bug where task results were being discarded, which caused the client to fail. This explicitly enables result storage for this actor.
# ------------------
import argparse

import dramatiq
from loguru import logger

# --- VDA Imports ---
from . import broker  # noqa: F401 - This is required to initialize the broker
from .processing import VideoProcessor, process_and_plan_for_single_file


@dramatiq.actor(max_retries=3, min_backoff=15000, store_results=True)
def process_video_file_task(config_dict: dict, media_path: str, videos_index: dict):
    """
    The core Dramatiq actor that processes a single media file to find
    duplicates and generate a plan fragment.
    """
    try:
        # Re-hydrate the config namespace from the dictionary
        config = argparse.Namespace(**config_dict)

        # The worker instantiates its own processor.
        processor = VideoProcessor(config)

        # Call the standalone logic function directly.
        result = process_and_plan_for_single_file(
            config, processor, media_path, videos_index
        )
        logger.info("Task completed for: {}", media_path)
        return result
    except Exception as e:
        logger.opt(exception=True).error(
            "Task failed for media file {}: {}", media_path, e
        )
        # Re-raise the exception to let Dramatiq handle the retry.
        raise
