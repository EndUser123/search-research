# --- INTEGRITY ---
# Previous Character Count: 6223
# Current Character Count: 4920
# Syntax Check: PASS
# Logic Validation: [Redundant console setup removed.]
# Reason for Change: [To centralize console management within the logger module and remove dead code.]
# ------------------
# --- METADATA ---
# Filename: src/utils.py
# Version: 1.2
#
# --- CHANGELOG ---
# v1.2: Removed obsolete logging helpers and converted to structlog (ADR-007).
# v1.1: Refactored logging to use rich.logging.RichHandler with custom theme.
# v1.0: Initial creation with helper functions and IPC logic.
# ------------------

import shutil
import subprocess
import threading
from pathlib import Path

import structlog

log = structlog.get_logger()


def format_token_count(count: int) -> str:
    """Formats a token count into a human-readable string like '8k' or '125k'."""
    if count < 1000:
        return str(count)
    return f"{count // 1000}k"


# Utility to recursively delete __pycache__ directories
def clean_pycache(root_path: Path) -> tuple[list[Path], list[Path]]:
    """
    Recursively finds and deletes __pycache__ directories.
    Returns a tuple of (deleted_paths, failed_paths).
    """
    deleted_paths = []
    failed_paths = []
    pycache_dirs = list(root_path.rglob("__pycache__"))

    for path in pycache_dirs:
        if path.is_dir():
            try:
                shutil.rmtree(path)
                deleted_paths.append(path)
            except OSError as e:
                log.error("Error deleting directory", path=path, error=e)
                failed_paths.append(path)
    return deleted_paths, failed_paths


# --- Windows IPC Imports (Optional) ---
try:
    import pywintypes  # type: ignore
    import win32file  # type: ignore
    import win32pipe  # type: ignore
    import win32security  # type: ignore
except ImportError:
    pywintypes = None
    win32file = None
    win32pipe = None
    win32security = None

# A flag to indicate if the Windows-specific IPC is available
IS_WINDOWS_IPC_AVAILABLE = all((pywintypes, win32file, win32pipe, win32security))


# --- General Helper Functions (Unchanged) ---
def detect_nvidia_gpu() -> tuple[str, str]:
    """
    Checks for the presence of an NVIDIA GPU using nvidia-smi.
    """
    try:
        subprocess.run(["nvidia-smi"], capture_output=True, check=True, timeout=5)
        return "hevc_nvenc", "p6"
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return "libx265", "slow"


def calculate_pixel_count(width: int, height: int) -> str:
    if not all((width, height)):
        return "N/A"
    return f"{width * height / 1_000_000:.2f} MP ({width}x{height})"


def get_dynamic_crf(
    bitrate_kbps: int, width: int, height: int, framerate_str: str
) -> int:
    try:
        if framerate_str and "/" in framerate_str:
            num, den = map(int, framerate_str.split("/"))
            framerate = num / den if den != 0 else 30.0
        else:
            framerate = float(framerate_str) if framerate_str else 30.0
    except (ValueError, TypeError):
        framerate = 30.0
    if not all((bitrate_kbps, width, height, framerate)):
        return 24
    bitrate_bps = bitrate_kbps * 1000
    pixels = width * height
    bpp = bitrate_bps / (pixels * framerate)
    if bpp > 0.1:
        return 22
    elif bpp > 0.05:
        return 24
    else:
        return 26


def is_hdr_video(video_stream: dict) -> bool:
    pix_fmt = video_stream.get("pix_fmt")
    color_space = video_stream.get("color_space")
    color_transfer = video_stream.get("color_transfer")

    # More robust HDR detection
    is_10_bit = "10" in pix_fmt if pix_fmt else False
    is_bt2020 = color_space == "bt2020nc"
    is_pq = color_transfer == "smpte2084"
    is_hlg = color_transfer == "arib-std-b67"  # HLG (Hybrid Log-Gamma)

    return is_10_bit and is_bt2020 and (is_pq or is_hlg)


def get_video_files(source_directory: Path) -> list[Path]:
    """
    Recursively find all video files in the given directory.
    If the path is a single file, it returns a list containing only that file.
    """
    if not source_directory.exists():
        return []

    if source_directory.is_file():
        return [source_directory]

    video_extensions = {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".3gp",
        ".ts",
        ".mts",
        ".m2ts",
        ".vob",
        ".mpg",
        ".mpeg",
        ".f4v",
        ".asf",
    }

    video_files = []
    for ext in video_extensions:
        video_files.extend(source_directory.rglob(f"*{ext}"))
    return sorted(video_files)


# --- Shared IPC and Progress Handling Code (Unchanged) ---
class ProgressHandler:
    def __init__(self):
        self.elapsed_seconds = 0
        self.lock = threading.Lock()

    def update_progress(self, new_seconds):
        with self.lock:
            self.elapsed_seconds = new_seconds

    def get_progress(self):
        with self.lock:
            return self.elapsed_seconds


def named_pipe_listener(pipe_name, progress_handler, stop_event):
    if not IS_WINDOWS_IPC_AVAILABLE:
        log.warning("pywin32 not found, named pipe listener will not run.")
        return

    assert win32security is not None
    assert win32pipe is not None
    assert win32file is not None
    assert pywintypes is not None

    pipe = None
    try:
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.bInheritHandle = 1
        pipe = win32pipe.CreateNamedPipe(
            pipe_name,
            win32pipe.PIPE_ACCESS_INBOUND,
            win32pipe.PIPE_TYPE_MESSAGE
            | win32pipe.PIPE_READMODE_MESSAGE
            | win32pipe.PIPE_WAIT,
            1,
            65536,
            65536,
            0,
            sa,
        )
        win32pipe.ConnectNamedPipe(pipe, None)
        while not stop_event.is_set():
            try:
                _, data = win32file.ReadFile(pipe, 4096)
                if data:
                    if isinstance(data, bytes):
                        progress_text = data.decode("utf-8", errors="ignore")
                    else:
                        progress_text = data
                    latest_time_in_ms = -1
                    for line in progress_text.strip().split("\n"):
                        if "out_time_ms=" in line:
                            latest_time_in_ms = int(line.strip().split("=")[1])
                    if latest_time_in_ms != -1:
                        progress_handler.update_progress(
                            round(latest_time_in_ms / 1_000_000, 2)
                        )
                else:
                    break
            except pywintypes.error as e:
                if e.winerror in [232, 109]:
                    break
                else:
                    raise e
    finally:
        if pipe:
            try:
                win32file.CloseHandle(pipe)
            except pywintypes.error:
                pass
