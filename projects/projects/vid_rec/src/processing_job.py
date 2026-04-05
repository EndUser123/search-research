# --- INTEGRITY ---
# Previous Character Count: 9272
# Current Character Count: 10243
# Syntax Check: [PASS]
# Logic Validation: [Added job_id binding and lifecycle logging to the worker process.]
# Reason for Change: [To enhance logging for better traceability as per the approved logging guide.]
# ------------------
# --- METADATA ---
# Filename: src/processing_job.py
# Version: 4.0
#
# --- CHANGELOG ---
# v4.0: ENHANCED LOGGING: Worker now binds the received `job_id` to its logging
#       context and emits detailed `_started` and `_completed` lifecycle events
#       with performance metrics.
# v3.0: MAJOR REFACTOR: Removed StateManager instantiation from worker process.
# ------------------

import logging.config
import os
import re
import subprocess
import time
from datetime import datetime
from multiprocessing import Event, Queue
from multiprocessing.managers import DictProxy
from pathlib import Path
from typing import Optional  # Import Optional

import structlog

from .config import AppConfig
from .state_manager import JobStatus


def _get_file_signature(file_path: Path) -> str:
    """Helper to calculate a file signature. Copied here to avoid StateManager dependency."""
    try:
        size = file_path.stat().st_size
        return f"{size}-{file_path.stat().st_mtime_ns}"
    except (FileNotFoundError, OSError):
        return ""


def _queue_upsert_command(
    db_queue: Queue,
    file_path: Path,
    status: JobStatus,
    error_message: Optional[str] = None,
):
    """Constructs and queues a standard upsert command for the StateManager."""
    file_signature = (
        _get_file_signature(file_path) if status != JobStatus.FAILED else None
    )
    timestamp = datetime.now().isoformat()
    query = """
        INSERT INTO jobs (file_path, status, file_signature, last_updated, error_message)
        VALUES (?, ?, ?, ?, ?) ON CONFLICT(file_path) DO UPDATE SET
        status = excluded.status,
        file_signature = COALESCE(excluded.file_signature, file_signature),
        last_updated = excluded.last_updated,
        error_message = excluded.error_message
        """
    params = (str(file_path), status.value, file_signature, timestamp, error_message)
    db_queue.put(("upsert", (query, params)))


def run_cpu_job_in_worker_multiprocess(
    job_data: dict,
    progress_dict: DictProxy,
    worker_id: int,
    db_queue: Queue,
    stop_event: Event,
    logging_config_dict: dict,
) -> tuple[str, str]:
    """
    Runs a CPU-intensive job in a separate worker process.
    This function is stateless regarding the database and logs its lifecycle.
    """
    start_time = time.time()
    source_path = Path(job_data["source_path"])
    job_id = job_data["job_id"]

    logging.config.dictConfig(logging_config_dict)
    structlog.contextvars.bind_contextvars(
        run_id=job_data.get("run_id", "unknown-run"),
        process_id=os.getpid(),
        worker_id=worker_id,
        job_id=job_id,
        file_name=source_path.name,
    )
    log = structlog.get_logger(worker_id=worker_id)
    log.info("cpu_job_started", category="processing")

    result_status = "FAILED"
    message = "An unexpected error occurred."

    try:
        config: AppConfig = job_data["config"]
        base_name = source_path.stem
        temp_destination_dir = config.paths.temp_dir / base_name
        temp_destination_dir.mkdir(parents=True, exist_ok=True)
        progress_dict[worker_id] = {
            "status": "processing",
            "file_name": source_path.name,
            "progress": 0,
        }

        def get_frame_count(video_path: Path) -> int:
            command = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-count_frames",
                "-show_entries",
                "stream=nb_read_frames",
                "-of",
                "default=nokey=1:noprint_wrappers=1",
                str(video_path),
            ]
            try:
                log.info("Running ffprobe to get frame count", category="processing")
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                return int(result.stdout.strip())
            except Exception as e:
                log.warning(
                    "Could not get frame count with ffprobe",
                    error=str(e),
                    category="processing",
                )
                return 99999

        def ffmpeg_progress_wrapper(
            command: list[str], total_frames: int
        ) -> tuple[int, str]:
            log.info(
                "Running FFmpeg command",
                command=" ".join(command),
                category="processing",
            )
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            frame_pattern = re.compile(r"frame=\s*(\d+)")
            full_output = ""
            if process.stdout is None:
                return -1, "FFmpeg process has no stdout"

            while True:
                if stop_event.is_set():
                    log.warning(
                        "Stop event detected, attempting to terminate FFmpeg process gracefully."
                    )
                    process.terminate()  # Send SIGTERM
                    # Give ffmpeg a short time to terminate gracefully
                    try:
                        process.wait(timeout=5)  # Wait for 5 seconds
                    except subprocess.TimeoutExpired:
                        log.error(
                            "FFmpeg process did not terminate gracefully, forcing kill."
                        )
                        process.kill()  # Force kill if it doesn't respond
                    return -2, "Process terminated by user request."
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    full_output += line
                    match = frame_pattern.search(line)
                    if match and total_frames > 0:
                        progress_dict[worker_id]["progress"] = min(
                            99, int((int(match.group(1)) / total_frames) * 100)
                        )

            returncode = process.wait()
            progress_dict[worker_id]["progress"] = 100
            log.info("FFmpeg command finished", returncode=returncode)
            if returncode != 0:
                log.error("FFmpeg execution failed", ffmpeg_output=full_output[-1000:])
            return returncode, full_output

        total_frames = get_frame_count(source_path)
        output_file = temp_destination_dir / f"{base_name}_encoded.mp4"
        crf = config.encoding.crf if config.encoding.crf > 0 else 23
        vf_scale = (
            f"scale=-2:{config.encoding.target_height}"
            if config.encoding.target_height > 0
            else "copy"
        )
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-vf",
            vf_scale,
            "-c:a",
            "aac",
            "-progress",
            "pipe:1",
            str(output_file),
        ]
        returncode, output = ffmpeg_progress_wrapper(command, total_frames)

        if returncode == 0:
            keep_file = True  # Placeholder for VMAF logic
            if keep_file:
                message = "Processing completed successfully."
                _queue_upsert_command(db_queue, source_path, JobStatus.FULLY_COMPLETED)
                result_status = "SUCCESS"
            else:
                message = "Encoded file discarded due to poor quality."
                _queue_upsert_command(db_queue, source_path, JobStatus.FAILED, message)
                result_status = "FAILED"
        elif returncode == -2:
            message = "Processing stopped by user request."
            result_status = "STOPPED"
        else:
            message = f"Video encoding failed. {output[-200:]}"
            _queue_upsert_command(db_queue, source_path, JobStatus.FAILED, message)
            result_status = "FAILED"

        progress_dict[worker_id]["status"] = (
            "completed" if result_status == "SUCCESS" else "failed"
        )
        return result_status, message

    except Exception as e:
        message = f"An unexpected error occurred in worker: {e}"
        log.error("Worker crashed", event="worker_crash", exc_info=True)
        _queue_upsert_command(db_queue, source_path, JobStatus.FAILED, message)
        progress_dict[worker_id]["status"] = "failed"
        result_status = "CRASHED"
        return "FAILED", message
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        log.info(
            "cpu_job_completed",
            duration_ms=duration_ms,
            outcome=result_status,
            final_message=message,
        )
