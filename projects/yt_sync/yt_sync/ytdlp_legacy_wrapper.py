# yt_sync/ytdlp_legacy_wrapper.py

import logging
import shlex
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

YTDLP_EXECUTABLE = "yt-dlp.exe"
SPOOFED_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def find_ytdlp_executable() -> str | None:
    """Finds yt-dlp executable in project directory or system PATH."""
    project_dir = Path(__file__).parent.parent
    local_path = project_dir / YTDLP_EXECUTABLE
    if local_path.is_file():
        return str(local_path)

    import shutil

    system_path = shutil.which("yt-dlp")
    if system_path:
        return system_path

    logger.error(f"Could not find '{YTDLP_EXECUTABLE}'.")
    return None


def build_command(
    args: object,
    extra_cmd_args: list[str],
    url: str | None = None,
    per_call_config: dict | None = None,
) -> list[str] | None:
    """Constructs a full yt-dlp command list."""
    executable = find_ytdlp_executable()
    if not executable:
        return None

    cmd = [executable, "--ignore-config", "--no-warnings"]

    if getattr(args, "yt_verbose", False):
        cmd.append("--verbose")

    # Authentication
    auth_config = getattr(args, "auth_config", {})
    if auth_config.get("cookies_file"):
        cmd.extend(["--cookies", str(auth_config["cookies_file"])])
        for key, value in auth_config.get("http_headers", {}).items():
            cmd.extend(["--add-header", f"{key}: {value}"])
    elif getattr(args, "cookies_from_browser", None):
        cookie_arg = args.cookies_from_browser
        if getattr(args, "profile", None):
            cookie_arg += f":{args.profile}"
        cmd.extend(["--cookies-from-browser", cookie_arg])

    if "user-agent" not in " ".join(cmd).lower():
        cmd.extend(["--user-agent", SPOOFED_USER_AGENT])

    # --- THE FIX: Re-implement per_call_config logic ---
    per_call_config = per_call_config or {}
    throttling_config = getattr(args, "throttling_config", {})
    if throttling_config.get("ratelimit"):
        cmd.extend(["--limit-rate", str(throttling_config["ratelimit"])])
    if throttling_config.get("sleep_interval_requests"):
        cmd.extend(
            ["--sleep-requests", str(throttling_config["sleep_interval_requests"])]
        )
    if not per_call_config.get("disable_sleep_interval") and throttling_config.get(
        "sleep_interval"
    ):
        cmd.extend(["--sleep-interval", str(throttling_config["sleep_interval"])])

    cmd.extend(extra_cmd_args)
    if url:
        cmd.append(url)

    return cmd


def run_ytdlp_subprocess(command: list[str]) -> subprocess.CompletedProcess:
    """Executes a prepared yt-dlp command list via subprocess."""
    logger.debug(
        f"Running yt-dlp command: {' '.join(shlex.quote(str(arg)) for arg in command)}"
    )
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
        if result.stderr:
            logger.debug(f"yt-dlp stderr:\n{result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp command timed out after 30 minutes")
        return subprocess.CompletedProcess(
            args=command, returncode=124, stdout="", stderr="Process timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error running yt-dlp subprocess: {e}")
        return subprocess.CompletedProcess(
            args=command, returncode=1, stdout="", stderr=str(e)
        )
