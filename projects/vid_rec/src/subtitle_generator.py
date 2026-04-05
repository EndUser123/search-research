# --- METADATA ---
# Filename: src/subtitle_generator.py
# Version: 2.1
#
# --- CHANGELOG ---
# v2.1: Added progress_callback to provide real-time transcription progress.
# v2.0: Implemented singleton model loading and progress callbacks (ADR-008).
# v1.1: Converted to structlog (ADR-007).
# v1.0: Initial creation with subtitle generation logic.
#
# --- INTEGRITY ---
# Initial Character Count: 1827
# Previous Character Count: 3371
# Current Character Count: 3680
# Reason for Change: Added progress_callback functionality and metadata.
# ------------------

import math
import threading
from pathlib import Path
from typing import Callable, Optional

import structlog
from faster_whisper import WhisperModel
from faster_whisper.utils import format_timestamp

log = structlog.get_logger()


class StopRequestedError(Exception):
    """Custom exception to signal that a stop has been requested."""

    pass


log = structlog.get_logger()

# Global model instance to ensure it's loaded only once.
_model: Optional[WhisperModel] = None


def load_model(model_name: str = "medium"):
    """
    Loads the faster-whisper model into a global instance.
    This function is idempotent; it will not reload the model.
    """
    global _model
    if _model is not None:
        log.info("Subtitle model already loaded.")
        return

    # Check for local model path to avoid download issues
    local_model_path = Path.cwd() / "models" / model_name
    if local_model_path.exists():
        try:
            log.info(
                "Loading subtitle model from local path...",
                model_path=str(local_model_path),
                device="cuda",
            )
            _model = WhisperModel(
                str(local_model_path), device="cuda", compute_type="float16"
            )
            log.info("Subtitle model loaded successfully from local path with CUDA.")
        except Exception as cuda_error:
            log.warning(
                "Failed to load local model with CUDA. Falling back to CPU mode.",
                error=cuda_error,
                exc_info=True,
            )
            try:
                log.info(
                    "Loading subtitle model from local path on CPU...",
                    model_path=str(local_model_path),
                    device="cpu",
                )
                _model = WhisperModel(
                    str(local_model_path), device="cpu", compute_type="int8"
                )
                log.info("Subtitle model loaded successfully from local path on CPU.")
            except Exception as cpu_error:
                log.error(
                    "Failed to load faster-whisper model from local path even on CPU.",
                    error=cpu_error,
                    exc_info=True,
                )
                raise
    else:
        try:
            log.info(
                "Loading subtitle model into memory...", model=model_name, device="cuda"
            )
            _model = WhisperModel(model_name, device="cuda", compute_type="float16")
            log.info("Subtitle model loaded successfully.")
        except Exception as cuda_error:
            log.warning(
                "Failed to load model with CUDA. Falling back to CPU mode, which will be slower.",
                error=cuda_error,
                exc_info=True,
            )
            try:
                log.info(
                    "Loading subtitle model on CPU...", model=model_name, device="cpu"
                )
                _model = WhisperModel(model_name, device="cpu", compute_type="int8")
                log.info("Subtitle model loaded successfully on CPU.")
            except Exception as cpu_error:
                log.error(
                    "Failed to load faster-whisper model even on CPU.",
                    error=cpu_error,
                    exc_info=True,
                )
                raise


def generate_subtitles_for_file(
    video_path: str,
    output_dir: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    forced_language: Optional[str] = None,
    stop_event: Optional[threading.Event] = None,
) -> Path:
    """
    Generates subtitles for a video file using the pre-loaded model.
    Invokes a callback with progress updates.
    """
    if _model is None:
        raise RuntimeError("Subtitle model is not loaded. Call load_model() first.")

    output_path = Path(output_dir) / f"{Path(video_path).stem}.srt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        segments, info = _model.transcribe(
            video_path,
            language=forced_language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        total_duration = math.ceil(info.duration)
        if progress_callback:
            # Wrap the original progress_callback to include stop event check
            def wrapped_progress_callback(current: int, total: int):
                if stop_event and stop_event.is_set():
                    raise StopRequestedError("Subtitle generation stopped by user.")
                progress_callback(current, total)

            wrapped_progress_callback(0, total_duration)

        with open(output_path, "w", encoding="utf-8") as srt_file:
            segment_count = 0
            for segment in segments:
                if stop_event and stop_event.is_set():
                    raise StopRequestedError("Subtitle generation stopped by user.")
                segment_count += 1
                start_time = format_timestamp(
                    segment.start, always_include_hours=True, decimal_marker=","
                )
                end_time = format_timestamp(
                    segment.end, always_include_hours=True, decimal_marker=","
                )
                text = segment.text.strip().replace("-->", "->")
                srt_entry = f"{segment_count}\n{start_time} --> {end_time}\n{text}\n\n"
                srt_file.write(srt_entry)

                if progress_callback:
                    wrapped_progress_callback(math.ceil(segment.end), total_duration)

        if progress_callback:
            wrapped_progress_callback(total_duration, total_duration)

        log.info(
            "Subtitle generation complete.",
            file=Path(video_path).name,
            output=str(output_path),
        )
        return output_path

    except StopRequestedError:
        log.warning("Subtitle generation stopped by user.", file=Path(video_path).name)
        raise  # Re-raise to propagate the stop signal
    except Exception as e:
        log.error(
            "An error occurred during subtitle generation",
            file=Path(video_path).name,
            error=e,
        )
        raise
