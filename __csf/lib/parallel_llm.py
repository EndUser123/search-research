"""
Parallel LLM CLI execution module.

Provides async concurrent execution of multiple CLI tools (qwen, gemini, codex/gh)
using asyncio for true parallelism, not sequential execution.

Also provides API-based execution for GLM models (glm-4.7-flash, glm-4.7-flashx).
"""
from __future__ import annotations

import asyncio
import glob
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def sanitize_error(error_msg: str) -> str:
    """Remove sensitive information from error messages (SEC-001 fix)."""
    if not error_msg:
        return error_msg

    # Remove API keys (common patterns)
    error_msg = re.sub(
        r'(Bearer|api_key|token|key|authorization)[\s:=]+[A-Za-z0-9\-_]{20,}',
        r'\1***REDACTED***',
        error_msg,
        flags=re.IGNORECASE
    )

    # Remove file paths (keep filename only)
    error_msg = re.sub(r'[A-Z]:\\[^\\]+\\([^\\]+)', r'...\\\1', error_msg)
    error_msg = re.sub(r'/[^/]+/([^/]+)', r'.../\1', error_msg)

    # Remove query content if present (truncate long error messages)
    if len(error_msg) > 500:
        error_msg = error_msg[:500] + "...[truncated]"

    return error_msg


def _save_cli_output(command: str, stdout_text: str, stderr_text: str) -> None:
    """Save CLI output to timestamped JSON file for recovery.

    Each CLI response is saved to __csf/temp/cli_results/ with timestamp.
    If output is not valid JSON, wraps it in an error structure.

    Args:
        command: Command string that was executed
        stdout_text: Raw stdout from CLI
        stderr_text: Raw stderr from CLI
    """
    try:
        # Get repo root (P:/) for temp directory
        repo_root = Path("P:/")
        temp_dir = repo_root / "__csf" / "temp" / "cli_results"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract CLI name from command for filename
        # Handle both string commands and list commands (list when using subprocess_exec on Windows)
        if isinstance(command, list):
            # List command: first element is the executable (e.g., ["node", "path/to/script.js", ...])
            cli_name = command[0].replace("/", "_").replace("\\", "_").replace('"', '').replace("'", "")
        else:
            # String command: split to get first part
            cmd_parts = command.split()
            cli_name = cmd_parts[0].replace("/", "_").replace("\\", "_").replace('"', '').replace("'", "")

        # Add timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        json_file = temp_dir / f"{cli_name}_{timestamp}.json"

        # Try to save as valid JSON, wrap if invalid
        try:
            # Validate JSON before saving
            json.loads(stdout_text)
            # Valid JSON - save raw output
            json_file.write_text(stdout_text, encoding="utf-8")
        except (json.JSONDecodeError, ValueError):
            # Invalid JSON - save as structured error with raw output
            wrapper = json.dumps({
                "raw_output": stdout_text[:10000],  # First 10KB
                "parse_error": "Invalid JSON - output may be truncated or corrupted",
                "cli": cli_name,
                "timestamp": timestamp,
                "stderr_preview": stderr_text[:500] if stderr_text else ""
            }, indent=2)
            json_file.write_text(wrapper, encoding="utf-8")

    except Exception:
        # Fail silently - don't break CLI execution if file save fails
        pass


async def _retry_request(
    coro_factory,
    max_retries: int = 3,
    base_delay: float = 1.0,
    verbose: bool = False,
) -> dict[str, Any]:
    """Retry an async coroutine with exponential backoff.

    Retries on transient failures like rate limiting (429), server errors (5xx),
    network timeouts, and connection issues.

    Args:
        coro_factory: Callable that returns a fresh coroutine (to allow retries)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (exponential backoff: 1s, 2s, 4s...)
        verbose: Show retry progress

    Returns:
        Dict with 'output' and optional 'error' keys
    """
    import asyncio

    for attempt in range(max_retries):
        # Create fresh coroutine on each attempt (fix: cannot reuse awaited coroutine)
        coro = coro_factory() if callable(coro_factory) else coro_factory
        result = await coro
        if not result.get('error'):
            return result

        # Check if error is retriable
        error = result.get('error', '')
        is_retriable = any(
            code in error.lower()
            for code in ['http 429', 'http 502', 'http 503', 'http 504', 'timeout', 'connection', 'temporarily unavailable']
        )

        if not is_retriable or attempt == max_retries - 1:
            return result

        delay = base_delay * (2 ** attempt)
        if verbose:
            print(f'[RETRY] Attempt {attempt + 1}/{max_retries} after {delay:.1f}s: {error[:60]}...', flush=True)
        await asyncio.sleep(delay)

    return result


async def run_single_command(
    command: str | list[str],
    input_text: str | None = None,
    timeout: int = 120,
    verbose: bool = False,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    """Run a single CLI command asynchronously.

    Args:
        command: Command string OR list of arguments to execute
        input_text: Text to pipe to stdin (for prompt input)
        timeout: Maximum seconds to wait
        verbose: Show execution progress

    Returns:
        Dict with 'output' and optional 'error' keys
    """
    import time

    # Handle both string commands and list arguments
    if isinstance(command, list):
        cmd_list = command
        cmd_name = command[0] if command else "unknown"
    else:
        cmd_list = command.split()
        cmd_name = command.split()[0] if command else "unknown"

    if verbose:
        print(f"[{cmd_name}] Spawned subprocess", flush=True)
        start = time.time()

    try:
        if sys.platform == "win32":
            # On Windows: use shell for string commands (npm global commands in PATH)
            # Use exec for list commands (avoids cmd.exe quote parsing issues)
            if isinstance(command, list):
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdin=asyncio.subprocess.PIPE if input_text else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdin=asyncio.subprocess.PIPE if input_text else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
        else:
            # On Unix, always split string commands
            proc = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdin=asyncio.subprocess.PIPE if input_text else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

        # Detect shell pipes AFTER proc creation - if "|" in command, the shell handles
        # the pipe (echo X | cmd), not Python's stdin. But we need the proc first to
        # access proc.stdin, so check here before writing.
        has_shell_pipe = not isinstance(command, list) and "|" in command

        if input_text and not has_shell_pipe:
            proc.stdin.write(input_text.encode("utf-8"))
            proc.stdin.close()

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
            stdout_text = stdout.decode("utf-8", errors="ignore") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="ignore") if stderr else ""

            # Save CLI output to timestamped JSON file for recovery
            _save_cli_output(command, stdout_text, stderr_text)

            if verbose:
                elapsed = time.time() - start
                print(f"[{cmd_name}] Completed in {elapsed:.1f}s", flush=True)

            # Check for errors in stderr even on success (codex outputs errors to stderr with exit 0)
            if stderr_text and stderr_text.strip():
                return {"output": stdout_text, "error": stderr_text}
            if proc.returncode == 0:
                return {"output": stdout_text, "error": None}
            else:
                return {"output": stdout_text, "error": stderr_text or f"Exit code {proc.returncode}"}

        except asyncio.TimeoutError:
            if verbose:
                print(f"[{command.split()[0]}] TIMEOUT after {timeout}s - terminating", flush=True)

            try:
                if hasattr(proc, 'terminate'):
                    proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
            except Exception:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass

            return {"output": "", "error": f"Timeout after {timeout}s"}

        except Exception as e:
            return {"output": "", "error": str(e)}

    except Exception as e:
        return {"output": "", "error": str(e)}



def _is_quota_error(error: str) -> bool:
    """Check if error is a quota/rate-limit error that should trigger fallback."""
    quota_signals = ["429", "no capacity", "rate limit", "quota", "limit exceeded", "temporarily unavailable", "terminalquotaerror"]
    return any(signal in error.lower() for signal in quota_signals)


def _check_gemini_quota_file() -> bool:
    """Check if a recent gemini-client-error-*.json file contains a quota signal.

    Gemini-cli traps quota errors in a JSON file in the system temp directory
    rather than reporting them via stderr. This function finds and inspects
    the most recent such file to detect quota exhaustion.

    Returns:
        True if a recent error file contains a quota signal, False otherwise.
    """
    import glob
    import time

    temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp")))
    pattern = str(temp_dir / "gemini-client-error-*.json")

    try:
        files = sorted(glob.glob(pattern), key=lambda p: Path(p).stat().st_mtime, reverse=True)
    except (OSError, ValueError):
        return False

    if not files:
        return False

    try:
        newest = Path(files[0])
        # Skip files older than 4 hours (quota exhaustion persists for hours; this
        # window is wide enough to catch active quotas but narrow enough to avoid
        # stale files from previous sessions)
        if time.time() - newest.stat().st_mtime > 14400:
            return False

        data = json.loads(newest.read_text(encoding="utf-8"))
        error_msg = str(data.get("error", {}).get("message", ""))
        return _is_quota_error(error_msg)
    except (OSError, json.JSONDecodeError, KeyError, IndexError):
        return False
async def run_parallel_commands(
    commands: list[tuple[str, list[str]]],
    timeout: int = 120,
    input_text: str | None = None,
    verbose: bool = False,
    fallback_commands: dict[str, list[tuple[str, list[str]]]] | None = None,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    """Run multiple CLI commands in parallel using asyncio.gather.

    This is the key function that enables CONCURRENT execution:
    - All commands start at the same time (not sequential)
    - asyncio.gather waits for ALL to complete
    - Total time = max(single_command_time), not sum(single_command_times)

    Args:
        commands: List of (name, [command_parts]) tuples
        timeout: Max seconds to wait for ALL commands
        input_text: Text to pipe to stdin for all commands
        verbose: Show parallel execution progress
        fallback_commands: Optional dict mapping name -> (fallback_name, fallback_cmd_args) for quota errors

    Returns:
        Dict mapping name -> {output, error} results
    """
    import time
    tasks = []
    names = []

    # Build task list with metadata for fallback support
    async def run_with_fallback(name: str, cmd_args, cmd_input, fallback_chain=None):
        """Run a command with fallback chain on quota error.

        fallback_chain: list of (fallback_name, fallback_cmd_args) tuples.
        Tries each in order until one succeeds without a quota error.
        """
        result = await run_single_command(cmd_args, input_text=cmd_input, timeout=timeout, verbose=verbose, cwd=cwd)

        if not fallback_chain:
            return name, result

        # Check if we should retry with fallback
        # Note: gemini-cli traps quota errors in a JSON file, not stderr, so we also
        # check the temp JSON file when stderr-based detection misses but we have
        # an error with empty output (the gemini quota signature).
        is_quota = _is_quota_error(result.get("error", ""))
        is_gemini_quota = (
            not is_quota
            and result.get("error")
            and not result.get("output")
            and _check_gemini_quota_file()
        )

        if not (is_quota or is_gemini_quota):
            return name, result

        # Try each fallback in the chain
        for fallback_name, fallback_cmd_args in fallback_chain:
            if verbose:
                print(f"[{name}] Quota error detected, falling back to {fallback_name}...", flush=True)
            result = await run_single_command(fallback_cmd_args, input_text=cmd_input, timeout=timeout, verbose=verbose, cwd=cwd)

            # Check if this fallback also hit quota
            fb_quota = _is_quota_error(result.get("error", ""))
            fb_gemini_quota = (
                not fb_quota
                and result.get("error")
                and not result.get("output")
                and _check_gemini_quota_file()
            )

            if not (fb_quota or fb_gemini_quota):
                # Success - this fallback worked
                result["_used_fallback"] = True
                return name, result

            # This fallback also failed quota - try next in chain
            if verbose:
                print(f"[{name}] Fallback {fallback_name} also hit quota, trying next...", flush=True)

        # All fallbacks exhausted - return the last result
        result["_used_fallback"] = True
        return name, result

    for name, cmd_args in commands:
        # cmd_args may be a list or a pre-built command string
        if isinstance(cmd_args, list):
            # Pass list directly to avoid cmd.exe quote parsing issues on Windows
            cmd_input = None  # Lists don't use stdin piping for -p style commands
        else:
            # Commands with -p flag (vibe) or codex exec embed query directly (no stdin)
            # Use " -p " to avoid false matches in model names like "minimax-coding-plan"
            uses_prompt_arg = " -p " in f" {cmd_args} " or cmd_args.startswith("codex exec")
            # Commands with shell pipes (echo X | gemini) handle stdin internally via shell
            # Don't pass input_text as it would conflict with the shell pipe
            has_shell_pipe = "|" in cmd_args
            cmd_input = None if (uses_prompt_arg or has_shell_pipe) else input_text

        # Get fallback command if available
        fallback = fallback_commands.get(name) if fallback_commands else None

        if verbose:
            cmd_display = cmd_args if isinstance(cmd_args, list) else cmd_args
            print(f"[{name}] Starting: {cmd_display}", flush=True)

        task = asyncio.create_task(
            run_with_fallback(name, cmd_args, cmd_input, fallback),
            name=name,
        )
        tasks.append(task)
        names.append(name)

    # Run all tasks concurrently - this is where parallelism happens
    # Use as_completed to return results as each CLI finishes (not when slowest finishes)
    if verbose:
        print(f"[PARALLEL] Running {len(tasks)} CLIs concurrently...", flush=True)
    start_time = time.time()

    # Collect results as they complete, not when all complete
    output = {}
    completed_count = 0

    # Helper to pair name with result (unpack nested tuple from run_with_fallback)
    async def fetch_and_name(name: str, coro):
        _, result = await coro
        return name, result

    # Create named coroutines for as_completed
    named_coros = [fetch_and_name(n, t) for n, t in zip(names, tasks)]

    for coro in asyncio.as_completed(named_coros):
        name, result = await coro
        output[name] = result if not isinstance(result, Exception) else {"output": "", "error": str(result)}
        completed_count += 1
        if verbose:
            print(f"[PARALLEL] {completed_count}/{len(tasks)} CLIs completed", flush=True)

    elapsed = time.time() - start_time
    if verbose:
        print(f"[PARALLEL] All {len(tasks)} CLIs completed in {elapsed:.1f}s", flush=True)

    return output


async def run_glm_api(
    model: str,
    query: str,
    api_key: str,
    session: "aiohttp.ClientSession | None" = None,
    timeout: int = 120,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run a GLM model via Z.ai API.

    Args:
        model: Model name (e.g., "glm-4.7-flash", "glm-4.7-flashx")
        query: Prompt text
        api_key: Z.ai API key
        session: Optional shared aiohttp ClientSession for connection pooling
        timeout: Maximum seconds to wait
        verbose: Show execution progress

    Returns:
        Dict with 'output' and optional 'error' keys
    """
    import time
    import json

    if verbose:
        print(f"[GLM-{model}] Starting API request", flush=True)
        start = time.time()

    url = "https://api.z.ai/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "max_tokens": 4096,
        "temperature": 1.0,
    }

    try:
        import aiohttp

        # Use shared session if provided, create temporary one otherwise
        if session is not None:
            async with session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    if verbose:
                        elapsed = time.time() - start
                        print(f"[GLM-{model}] Completed in {elapsed:.1f}s", flush=True)

                    return {"output": content, "error": None}
                else:
                    error_text = await response.text()
                    return {"output": "", "error": sanitize_error(f"HTTP {response.status}: {error_text}")}
        else:
            # Fallback: create temporary session (for backward compatibility)
            async with aiohttp.ClientSession() as temp_session:
                async with temp_session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                        if verbose:
                            elapsed = time.time() - start
                            print(f"[GLM-{model}] Completed in {elapsed:.1f}s", flush=True)

                        return {"output": content, "error": None}
                    else:
                        error_text = await response.text()
                        return {"output": "", "error": sanitize_error(f"HTTP {response.status}: {error_text}")}

    except ImportError:
        return {"output": "", "error": "aiohttp not installed - run: pip install aiohttp"}
    except Exception as e:
        return {"output": "", "error": sanitize_error(str(e))}


async def run_parallel_glm(
    queries: list[tuple[str, str]],  # (model_name, query) tuples
    api_key: str,
    timeout: int = 120,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run multiple GLM models in parallel via API.

    Uses a shared ClientSession for connection pooling - all requests share
    the same connection pool, reducing SSL handshake overhead.

    Args:
        queries: List of (model_name, query) tuples
        api_key: Z.ai API key
        timeout: Max seconds to wait for ALL requests
        verbose: Show parallel execution progress

    Returns:
        Dict mapping model_name -> {output, error} results
    """
    import time
    import aiohttp

    # Create a shared session for connection pooling
    # This significantly improves performance when making multiple requests
    async with aiohttp.ClientSession() as session:
        tasks = []
        model_names = []

        for model_name, query in queries:
            if verbose:
                print(f"[GLM-{model_name}] Queuing API request", flush=True)

            # Create a retry wrapper for this API call
            async def api_call_with_retry():
                return await _retry_request(
                    lambda: run_glm_api(model_name, query, api_key, session=session, timeout=timeout, verbose=verbose),
                    max_retries=3,
                    base_delay=1.0,
                    verbose=verbose,
                )
            
            task = asyncio.create_task(api_call_with_retry())
            tasks.append(task)
            model_names.append(model_name)

        # Run all tasks concurrently
        if verbose:
            print(f"[PARALLEL] Running {len(tasks)} GLM API requests concurrently...", flush=True)
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        if verbose:
            print(f"[PARALLEL] All {len(tasks)} GLM API requests completed in {elapsed:.1f}s", flush=True)

        # Build results dict
        output = {}
        for name, result in zip(model_names, results):
            if isinstance(result, Exception):
                output[name] = {"output": "", "error": str(result)}
            else:
                output[name] = result

        return output


def calc_timeout(context_size_kb: int) -> int:
    """Calculate timeout based on context size and LLM response times (PERF-005 fix).

    Uses P99 response time for slowest CLI (gemini: 320s P99) plus
    safety margin and context processing overhead.

    Args:
        context_size_kb: Context size in kilobytes

    Returns:
        Timeout in seconds
    """
    # Base timeout: P99 response time for slowest CLI with 2x safety margin
    # P99 gemini ~320s, multiply by 2 for edge cases = 640s baseline
    base_timeout = 640  # ~10.7 minutes for worst-case LLM response

    # Add context processing overhead: 1s per MB for read/parse/copy
    context_overhead = max(1, (context_size_kb // 1024))

    # Add subprocess spawn overhead: 1s for 5 CLIs (PowerShell startup on Windows)
    spawn_overhead = 1

    return base_timeout + context_overhead + spawn_overhead
