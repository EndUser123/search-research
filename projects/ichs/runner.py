# __dev\iCHS\ichs\runner.py
from __future__ import annotations

import logging
import os
import shlex
import signal
import subprocess
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Union

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    """
    Normalized process execution result.

    Fields:
      - name: str             A human-readable command display (what was executed)
      - stdout: str           Captured standard output (possibly truncated)
      - stderr: str           Captured standard error (possibly truncated)
      - returncode: int       Process exit code
      - duration_sec: float   Wall time in seconds
      - start_ts: str         ISO UTC timestamp at process start
      - end_ts: str           ISO UTC timestamp at process end
      - timed_out: bool       True if the command timed out and was killed
      - pid: Optional[int]    Process ID if available
      - truncated: bool       True if either stdout/stderr was truncated to max_output_bytes
    """

    name: str
    stdout: str
    stderr: str
    returncode: int
    duration_sec: float
    start_ts: str
    end_ts: str
    timed_out: bool = False
    pid: int | None = None
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CommandType = Union[str, Sequence[str]]


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _is_windows() -> bool:
    return os.name == "nt"


def _safe_display_join(argv: Sequence[str]) -> str:
    """
    Build a human-readable display string for argv with platform-appropriate quoting.
    """
    if _is_windows():
        return subprocess.list2cmdline(list(argv))
    return " ".join(shlex.quote(x) for x in argv)


def _normalize_command(
    command: CommandType,
    shell: bool,
) -> tuple[str | list[str], str]:
    """
    Prepare the command for subprocess and a readable display name.

    Returns (cmd_for_subprocess, display_name).
    """
    if shell:
        if isinstance(command, str):
            # Already a shell string; use as-is for both invocation and display.
            return command, command
        # Sequence -> shell string. Use platform-appropriate quoting.
        argv = [str(x) for x in command]
        if _is_windows():
            cmd_str = subprocess.list2cmdline(argv)
            return cmd_str, cmd_str
        display = " ".join(shlex.quote(x) for x in argv)
        return display, display

    # shell=False
    if isinstance(command, str):
        # Split string into argv for subprocess
        argv = shlex.split(command, posix=not _is_windows())
        display = command
        return argv, display

    # Already a sequence
    argv = [str(x) for x in command]
    display = _safe_display_join(argv)
    return argv, display


def _decode(data: bytes | None, encoding: str, errors: str) -> str:
    if data is None:
        return ""
    try:
        return data.decode(encoding, errors=errors)
    except Exception:
        # Fallback to UTF-8 replace if provided encoding fails unexpectedly
        return data.decode("utf-8", errors="replace")


def _truncate_bytes(b: bytes, limit: int | None) -> tuple[bytes, bool]:
    if limit is None or limit <= 0:
        return b, False
    if len(b) <= limit:
        return b, False
    # Keep the head and indicate truncation
    return b[:limit], True


def _prepare_env(env: dict[str, str | None] | None) -> dict[str, str] | None:
    """
    Merge provided env with current environment. None values mean deletion.
    Returns a new mapping or None if env is None.
    """
    if env is None:
        return None
    merged = os.environ.copy()
    for k, v in env.items():
        k_str = str(k)
        if v is None:
            merged.pop(k_str, None)
        else:
            merged[k_str] = str(v)
    return merged


def _ensure_bytes_input(
    data: str | bytes | None, encoding: str, errors: str
) -> bytes | None:
    if data is None:
        return None
    if isinstance(data, bytes):
        return data
    return str(data).encode(encoding, errors=errors)


def _kill_process_tree_posix(proc: subprocess.Popen, grace_sec: float) -> str:
    """
    Try to terminate the whole process group (requires start_new_session=True at spawn).
    Returns a brief description of what was attempted.
    """
    desc = []
    try:
        if proc.pid is not None:
            # Send SIGTERM to the process group
            os.killpg(proc.pid, signal.SIGTERM)
            desc.append(f"killpg(SIGTERM pid={proc.pid})")
            # Give it a moment to exit
            try:
                proc.wait(timeout=max(0.0, grace_sec / 2))
            except subprocess.TimeoutExpired:
                pass
            # If still alive, escalate to SIGKILL
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                desc.append(f"killpg(SIGKILL pid={proc.pid})")
    except Exception as e:
        desc.append(f"killpg_failed({e.__class__.__name__})")
    # As a last resort, kill just the process
    if proc.poll() is None:
        try:
            proc.kill()
            desc.append("proc.kill()")
        except Exception as e:
            desc.append(f"proc.kill_failed({e.__class__.__name__})")
    return " -> ".join(desc)


def _kill_process_tree_windows(proc: subprocess.Popen, grace_sec: float) -> str:
    """
    Use taskkill to terminate a process tree reliably on Windows.
    Returns a brief description of what was attempted.
    """
    desc = []
    pid = proc.pid
    if pid is None:
        return "no_pid"
    # Try taskkill with /T for tree and /F for force
    try:
        res = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=max(1.0, grace_sec),
        )
        desc.append(f"taskkill(rc={res.returncode})")
    except Exception as e:
        desc.append(f"taskkill_failed({e.__class__.__name__})")
    # Fallback to proc.kill()
    if proc.poll() is None:
        try:
            proc.kill()
            desc.append("proc.kill()")
        except Exception as e:
            desc.append(f"proc.kill_failed({e.__class__.__name__})")
    return " -> ".join(desc)


def run_command(
    command: CommandType,
    *,
    timeout: float | None = None,
    cwd: str | Path | None = None,
    env: dict[str, str | None] | None = None,
    shell: bool = False,
    encoding: str = "utf-8",
    errors: str = "replace",
    max_output_bytes: int | None = 2_000_000,
    input: str | bytes | None = None,
    kill_tree_on_timeout: bool = True,
    kill_tree_grace_sec: float = 3.0,
) -> dict[str, Any]:
    """
    Execute a command and return a normalized result dict.

    Args:
      command: The command to run; string or argv sequence.
      timeout: Optional timeout in seconds (float).
      cwd: Working directory; str or Path.
      env: Environment overrides (merged onto os.environ if provided).
           If a value is None, the variable is removed from the environment.
      shell: Whether to execute via the system shell (default False).
      encoding: Text encoding used to decode stdout/stderr.
      errors: Decoding error strategy ('replace' recommended).
      max_output_bytes: If set, truncate stdout/stderr bytes to this many bytes.
      input: Optional data to send to process stdin (str or bytes).
             If str is provided, it is encoded with (encoding, errors).
      kill_tree_on_timeout: If True, attempt to terminate the process tree on timeout.
                            On POSIX, uses process groups; on Windows, uses taskkill.
      kill_tree_grace_sec: Grace period (seconds) before escalating to a harder kill.

    Returns:
      Dict[str, Any] with keys matching RunResult.to_dict()
    """
    if cwd is not None:
        cwd = str(Path(cwd).expanduser().resolve())

    proc_env = _prepare_env(env)

    cmd_for_subproc, display_name = _normalize_command(command, shell=shell)

    start_ts = _iso_now()
    t0 = time.monotonic()

    logger.debug(
        "Starting command: %s (shell=%s, cwd=%s, timeout=%s, kill_tree_on_timeout=%s)",
        display_name,
        shell,
        cwd,
        timeout,
        kill_tree_on_timeout,
    )

    # Start the process
    proc = None
    stdout_b: bytes = b""
    stderr_b: bytes = b""
    returncode: int = -1
    timed_out = False
    pid: int | None = None
    truncated = False

    popen_kwargs: dict[str, Any] = {
        "cwd": cwd,
        "env": proc_env,
        "shell": shell,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        # stdin PIPE only if caller provided input; avoids unnecessary handles
        "stdin": subprocess.PIPE if input is not None else None,
    }

    # For process-tree control on timeout: create a new process group/session.
    if kill_tree_on_timeout:
        if _is_windows():
            creationflags = 0
            # CREATE_NEW_PROCESS_GROUP isolates the child so taskkill /T finds the subtree.
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if creationflags:
                popen_kwargs["creationflags"] = creationflags
        else:
            # POSIX: start a new session so the child becomes a pg leader.
            popen_kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen(  # type: ignore[arg-type]
            cmd_for_subproc,
            **popen_kwargs,
        )
        pid = proc.pid
        try:
            stdout_b, stderr_b = proc.communicate(
                timeout=timeout,
                input=_ensure_bytes_input(input, encoding, errors),
            )
            returncode = proc.returncode
        except subprocess.TimeoutExpired as te:
            timed_out = True
            kill_desc = ""
            # Attempt to terminate the entire process tree, then gather output.
            try:
                if kill_tree_on_timeout:
                    if _is_windows():
                        kill_desc = _kill_process_tree_windows(
                            proc, kill_tree_grace_sec
                        )
                    else:
                        kill_desc = _kill_process_tree_posix(proc, kill_tree_grace_sec)
                else:
                    # Fall back to killing only the direct child
                    proc.kill()
                    kill_desc = "proc.kill()"
            except Exception as e:
                kill_desc = f"kill_failed({e.__class__.__name__})"
            # Attempt to collect remaining output
            try:
                stdout_b, stderr_b = proc.communicate(
                    timeout=max(1.0, kill_tree_grace_sec / 2)
                )
            except Exception:
                # If still failing, capture what we can
                stdout_b = te.output or b""
                stderr_b = te.stderr or b""
            # Common convention for timeout; prefer 124 if no returncode set
            returncode = proc.returncode if proc.returncode is not None else 124
            # Append a timeout note to stderr for visibility
            note = f"\n[ichs] Command timed out after {timeout} seconds and was terminated. actions={kill_desc}"
            stderr_b = (stderr_b or b"") + note.encode(encoding, errors="ignore")
        except Exception as e:
            # Unknown failure to run or communicate
            err = f"[ichs] Runner error: {e.__class__.__name__}: {e}"
            stderr_b = (stderr_b or b"") + err.encode(encoding, errors="ignore")
            returncode = proc.returncode if proc is not None else -1
    except FileNotFoundError as e:
        # Executable not found
        msg = f"[ichs] Executable not found while running: {display_name} -> {e}"
        logger.debug(msg)
        return RunResult(
            name=display_name,
            stdout="",
            stderr=msg,
            returncode=127,  # common "command not found"
            duration_sec=0.0,
            start_ts=start_ts,
            end_ts=_iso_now(),
            timed_out=False,
            pid=None,
            truncated=False,
        ).to_dict()
    except Exception as e:
        # Failure to spawn process
        msg = f"[ichs] Failed to start command: {display_name} -> {e.__class__.__name__}: {e}"
        logger.debug(msg)
        return RunResult(
            name=display_name,
            stdout="",
            stderr=msg,
            returncode=-1,
            duration_sec=0.0,
            start_ts=start_ts,
            end_ts=_iso_now(),
            timed_out=False,
            pid=None,
            truncated=False,
        ).to_dict()
    finally:
        # Ensure process object is not left running
        try:
            if proc is not None and proc.poll() is None:
                # Try a gentle termination of the direct child as a last resort
                proc.kill()
        except Exception:
            pass

    # Truncate if required (operate on bytes to avoid slicing in middle of codepoint)
    stdout_b, tr1 = _truncate_bytes(stdout_b or b"", max_output_bytes)
    stderr_b, tr2 = _truncate_bytes(stderr_b or b"", max_output_bytes)
    truncated = tr1 or tr2

    # Decode outputs
    out_s = _decode(stdout_b, encoding, errors)
    err_s = _decode(stderr_b, encoding, errors)

    duration = max(0.0, time.monotonic() - t0)
    end_ts = _iso_now()

    logger.debug(
        "Finished command: %s (rc=%s, pid=%s, duration=%.3fs, timed_out=%s, truncated=%s)",
        display_name,
        returncode,
        pid,
        duration,
        timed_out,
        truncated,
    )

    return RunResult(
        name=display_name,
        stdout=out_s,
        stderr=err_s,
        returncode=int(returncode if returncode is not None else -1),
        duration_sec=float(duration),
        start_ts=start_ts,
        end_ts=end_ts,
        timed_out=timed_out,
        pid=pid,
        truncated=truncated,
    ).to_dict()


__all__ = ["run_command", "RunResult"]
