#!/usr/bin/env python3
"""Blind adversarial review using agentic external LLMs.

All reviewers are fully agentic — they can read files, grep, and verify claims
against source code. No document content is passed in the prompt; each reviewer
gets a file path and explores on its own.

Default reviewers (session model is auto-skipped):
  - agy (Google Antigravity, free, auto model selection)
  - opencode run -m minimax-coding-plan/MiniMax-M3
  - opencode run -m mistral/mistral-medium-latest
  - opencode run -m zai/glm-5.2
  - opencode free tier: deepseek-v4-flash-free, hy3-free, mimo-v2.5-free,
    nemotron-3-ultra-free, north-mini-code-free

OpenCode Go models (paid, opt-in via --go flag):
  - glm-5.2, glm-5.1, kimi-k2.7-code, kimi-k2.6
  - MiniMax-M3, MiniMax-M2.7
  - qwen3.7-max, qwen3.7-plus, qwen3.6-plus
  - deepseek-v4-pro, deepseek-v4-flash
  - mimo-v2.5, mimo-v2.5-pro

Extra reviewers via CLI or env var:
  --reviewer opencode-go/minimax-m3
  RED_TEAM_EXTRA_REVIEWERS=openrouter/qwen/qwen3.5,huggingface/MiniMaxAI/MiniMax-M3

Note: mmx (MiniMax CLI) is MiniMax's API capability wrapper (text, search,
vision, image, video, speech, music) designed to be called BY agents — not a
competing agent runtime. It doesn't run the tool-call loop itself. opencode
IS the agent loop for MiniMax, Mistral, and GLM, providing Bash/Read/Grep/Glob
to every model. agy has its own separate agent loop.

Usage:
  python red_team_blind_review.py <document_path>
  python red_team_blind_review.py <document_path> --go
  python red_team_blind_review.py <document_path> --reviewer opencode-go/qwen3.7-max
  python red_team_blind_review.py <document_path> --reviewer opencode/hy3-free
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Marker/deadline tracking for reaper backstop
sys.path.insert(0, str(Path(__file__).parent))
import red_team_markers as markers


# --- Config ---

AGY_BINARY = os.environ.get("AGY_BINARY", "agy")
OPENCODE_BINARY = os.environ.get("OPENCODE_BINARY", "opencode")
AGY_TIMEOUT = int(os.environ.get("RED_TEAM_AGY_TIMEOUT", "180"))

OPENCODE_TIMEOUT = int(os.environ.get("RED_TEAM_OPENCODE_TIMEOUT", "180"))
WORKDIR = os.environ.get("RED_TEAM_WORKDIR", "P:/")

DEFAULT_OPENCODE_MODELS = [
    "minimax-coding-plan/MiniMax-M3",
    "mistral/mistral-medium-latest",
    "zai/glm-5.2",
    "opencode/deepseek-v4-flash-free",
    "opencode/hy3-free",
    "opencode/mimo-v2.5-free",
    "opencode/nemotron-3-ultra-free",
    "opencode/north-mini-code-free",
]

# OpenCode Go models (paid subscription, ~$10/mo)
# Empty until user explicitly approves specific Go models.
# Use --reviewer opencode-go/<model-id> to add Go models on demand.
OPENCODE_GO_MODELS = []  # add approved Go models here


# Keywords used to match session model to reviewers for auto-skip.
# Matches on substring (case-insensitive) against the full model ID.
MODEL_KEYWORDS = {
    "minimax": ["minimax-m3", "minimax-m2", "minimax"],
    "mistral": ["mistral-medium", "mistral-large", "magistral"],
    "glm": ["glm-5", "glm-4", "glm"],
    "deepseek": ["deepseek"],
    "qwen": ["qwen"],
    "hy3": ["hy3"],
    "gemini": ["gemini"],
    "gpt": ["gpt-5", "gpt-4"],
    "claude": ["claude", "sonnet", "opus", "haiku", "fable"],
}

REVIEW_PROMPT_TEMPLATE = """You are performing an adversarial review of a technical document.

Read the document at: {doc_path}

Find problems: factual errors, contradictions, unsupported claims, wrong API conventions, arbitrary numbers, dead citations, implementation risks.

IMPORTANT: You have file tools. For any claim that references source code (file:line, function names, code behavior), VERIFY IT by reading the actual code. Grep for the function, read the file, confirm the claim is accurate.

For each issue found, provide:
1. Quote the exact text from the document
2. State what is wrong or questionable
3. Rate severity: CRITICAL / MEDIUM / LOW
4. If you verified against code, cite what you found

Return findings as a JSON array:
```json
[
  {{
    "issue": "Short title",
    "severity": "CRITICAL|MEDIUM|LOW",
    "quote": "Exact text from document",
    "problem": "What is wrong",
    "why_it_matters": "Impact assessment",
    "verified_against_code": true|false,
    "verification_detail": "What you found in the code (if checked)"
  }}
]
```

If no issues found, return []. Be adversarial, not polite. The session model ({session_model}) wrote this document — you are not it. Find what it missed."""


# --- Session model detection ---


def detect_session_model() -> str:
    """Detect the current session model to skip it from reviewers."""
    # Check env var first
    model = os.environ.get("OPENCODE_MODEL", "").strip()
    if model:
        return model

    # Try opencode config
    config_path = Path.home() / ".config" / "opencode" / "opencode.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            model = config.get("model", "")
            if model:
                return model
        except (json.JSONDecodeError, OSError):
            pass

    return "glm-5.2"  # sensible default


def should_skip_reviewer(model_id: str, session_model: str) -> bool:
    """Check if a reviewer model matches the session model (should be skipped)."""
    model_lower = model_id.lower()
    session_lower = session_model.lower()

    # Direct substring match
    if session_lower in model_lower or model_lower in session_lower:
        return True

    # Keyword-based matching
    for _, keywords in MODEL_KEYWORDS.items():
        for kw in keywords:
            if kw in model_lower and kw in session_lower:
                return True

    return False


# --- Reviewers ---


def run_agy(doc_path: str, session_model: str) -> dict:
    """Run agy (Google Antigravity CLI) as an agentic reviewer."""
    prompt = REVIEW_PROMPT_TEMPLATE.format(doc_path=doc_path, session_model=session_model)

    # Resolve binary to full path on Windows
    agy_path = AGY_BINARY
    if os.name == "nt" and "\\" not in AGY_BINARY and "/" not in AGY_BINARY:
        import shutil

        resolved = shutil.which(AGY_BINARY)
        if resolved:
            agy_path = resolved

    try:
        result = subprocess.run(
            [
                agy_path,
                "-p",
                prompt,
                "--dangerously-skip-permissions",
                "--print-timeout",
                f"{AGY_TIMEOUT}s",
            ],
            capture_output=True,
            text=True,
            timeout=AGY_TIMEOUT + 30,
        )
        if result.returncode != 0:
            return {
                "reviewer": "agy",
                "error": f"exit {result.returncode}: {(result.stderr or '')[:200]}",
            }
        text = (result.stdout or "").strip()
        if not text:
            return {"reviewer": "agy", "error": "empty stdout (possible quota/auth issue)"}
        return {"reviewer": "agy", "raw_response": text}
    except subprocess.TimeoutExpired:
        return {"reviewer": "agy", "error": f"timeout after {AGY_TIMEOUT + 30}s"}
    except FileNotFoundError:
        return {"reviewer": "agy", "error": f"binary not found: {AGY_BINARY}"}
    except Exception as e:
        return {"reviewer": "agy", "error": f"{type(e).__name__}: {e}"}


def _kill_process_tree(pid: int) -> dict:
    """Kill the entire process tree rooted at pid.

    On Windows, uses taskkill.exe /T /F to recursively kill all descendants.
    This is necessary because opencode.CMD spawns cmd.exe -> node.exe -> MCP
    servers, and killing only the root leaves descendants orphaned.

    Returns a dict with:
      ok: True if the kill succeeded (or nothing was left to kill)
      error: short error string when ok is False, else None
    """
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            return {"ok": False, "error": "taskkill.exe not found"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "taskkill timed out after 30s"}
        except OSError as e:
            return {"ok": False, "error": f"OSError: {e}"}
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()[:200]
            return {"ok": False, "error": f"taskkill exit {result.returncode}: {stderr}"}
        return {"ok": True, "error": None}
    else:
        try:
            import signal

            sig = getattr(signal, "SIGKILL", signal.SIGTERM)
            os.kill(pid, sig)
        except ProcessLookupError:
            return {"ok": True, "error": None}
        except OSError as e:
            return {"ok": False, "error": f"OSError: {e}"}
        return {"ok": True, "error": None}


def _parse_opencode_json_events(stdout: str) -> str:
    """Parse OpenCode JSON-lines output, extracting text from type:text events."""
    text_parts = []
    for line in (stdout or "").strip().splitlines():
        try:
            event = json.loads(line)
            if event.get("type") == "text":
                part = event.get("part", {})
                if part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
        except json.JSONDecodeError:
            continue
    return "".join(text_parts).strip()


def run_opencode_model(model_id: str, doc_path: str, session_model: str) -> dict:
    """Run an opencode model as an agentic reviewer."""
    prompt = REVIEW_PROMPT_TEMPLATE.format(doc_path=doc_path, session_model=session_model)
    reviewer_name = model_id.split("/")[-1]

    # Resolve binary to full path on Windows (npm bin often missing from Python's env)
    opencode_path = OPENCODE_BINARY
    if os.name == "nt" and "\\" not in OPENCODE_BINARY and "/" not in OPENCODE_BINARY:
        import shutil

        resolved = shutil.which(OPENCODE_BINARY)
        if resolved:
            opencode_path = resolved

    # Use a unique DB per subprocess to avoid SQLite lock contention
    # when running multiple opencode instances in parallel (issues #15188, #29395)
    import tempfile
    import uuid

    env = os.environ.copy()
    env["OPENCODE_DB"] = str(Path(tempfile.gettempdir()) / f"red_team_{uuid.uuid4().hex[:8]}.db")

    timeout = OPENCODE_TIMEOUT + 30
    command = [opencode_path, "run", "-m", model_id, "--format", "json", prompt]
    task_id = f"{reviewer_name}-{uuid.uuid4().hex[:8]}"
    marker_written = False

    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            cwd=WORKDIR,
            env=env,
            shell=False,
        )
    except FileNotFoundError:
        return {
            "reviewer": reviewer_name,
            "model_id": model_id,
            "error": "opencode binary not found",
        }
    except Exception as e:
        return {
            "reviewer": reviewer_name,
            "model_id": model_id,
            "error": f"{type(e).__name__}: {e}",
        }

    # Write a marker so the reaper can kill this process tree if the
    # Python supervisor itself is terminated.
    try:
        marker = markers.create_marker(
            task_id=task_id,
            reviewer=reviewer_name,
            model_id=model_id,
            root_pid=proc.pid,
            command=command,
            cwd=WORKDIR,
            deadline_seconds=timeout,
        )
        markers.write_marker(marker)
        marker_written = True
    except Exception:
        pass

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        cleanup = _kill_process_tree(proc.pid)
        try:
            proc.communicate(timeout=15)
        except Exception:
            proc.kill()
            try:
                proc.communicate(timeout=5)
            except Exception:
                pass
        if marker_written:
            markers.remove_marker(task_id)
        result = {
            "reviewer": reviewer_name,
            "model_id": model_id,
            "error": f"timeout after {timeout}s",
            "timeout_duration": timeout,
            "cleanup_ok": cleanup["ok"],
        }
        if cleanup["error"]:
            result["cleanup_error"] = cleanup["error"]
        return result
    except Exception as e:
        cleanup = _kill_process_tree(proc.pid)
        try:
            proc.communicate(timeout=5)
        except Exception:
            pass
        if marker_written:
            markers.remove_marker(task_id)
        result = {
            "reviewer": reviewer_name,
            "model_id": model_id,
            "error": f"{type(e).__name__}: {e}",
            "cleanup_ok": cleanup["ok"],
        }
        if cleanup["error"]:
            result["cleanup_error"] = cleanup["error"]
        return result

    if marker_written:
        markers.remove_marker(task_id)

    if proc.returncode != 0:
        return {
            "reviewer": reviewer_name,
            "model_id": model_id,
            "error": f"exit {proc.returncode}: {(stderr or '')[:200]}",
        }

    text = _parse_opencode_json_events(stdout or "")
    if not text:
        return {"reviewer": reviewer_name, "model_id": model_id, "error": "no text in output"}
    return {"reviewer": reviewer_name, "model_id": model_id, "raw_response": text}


# --- Orchestration ---


def collect_reviewers(session_model: str, extra_models: list[str]) -> list[dict]:
    """Build the reviewer list, skipping session model.

    If a provider isn't configured, run_opencode_model will fail gracefully
    via fail-open and the error will be reported in the results.
    """
    reviewers = [{"name": "agy", "type": "agy"}]

    for model_id in DEFAULT_OPENCODE_MODELS:
        if should_skip_reviewer(model_id, session_model):
            print(f"  SKIP: {model_id} (matches session model)")
            continue
        reviewers.append(
            {"name": model_id.split("/")[-1], "type": "opencode", "model_id": model_id}
        )

    for model_id in extra_models:
        if should_skip_reviewer(model_id, session_model):
            print(f"  SKIP: {model_id} (matches session model)")
            continue
        reviewers.append(
            {"name": model_id.split("/")[-1], "type": "opencode", "model_id": model_id}
        )

    return reviewers


def main(doc_path: str, extra_models: list[str]) -> None:
    doc = Path(doc_path)
    if not doc.exists():
        print(f"ERROR: Document not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    session_model = detect_session_model()
    reviewers = collect_reviewers(session_model, extra_models)

    print(f"Document: {doc_path} ({doc.stat().st_size} bytes)")
    print(f"Session model (skipped): {session_model}")
    print(f"Reviewers ({len(reviewers)}):")
    for r in reviewers:
        label = r.get("model_id", r["name"])
        print(f"  - {label}")
    print("-" * 60)

    start = time.time()
    results: list[dict] = []

    # All reviewers run in parallel — each opencode subprocess gets its own
    # OPENCODE_DB to avoid SQLite lock contention (issues #15188, #29395)
    with ThreadPoolExecutor(max_workers=len(reviewers)) as pool:
        futures: dict = {}

        for r in reviewers:
            if r["type"] == "agy":
                futures[pool.submit(run_agy, doc_path, session_model)] = r["name"]
            else:
                futures[pool.submit(run_opencode_model, r["model_id"], doc_path, session_model)] = (
                    r["name"]
                )

        for future in as_completed(futures):
            name = futures[future]
            result = future.result()
            elapsed = time.time() - start
            results.append(result)

            if "error" in result:
                print(f"  [{name}] FAIL ({elapsed:.1f}s): {result['error'][:80]}")
            else:
                print(f"  [{name}] OK ({elapsed:.1f}s): {len(result['raw_response'])} chars")

    print("-" * 60)

    success_count = sum(1 for r in results if "error" not in r)
    if success_count == 0:
        print("HARD FAILURE: all reviewers failed.", file=sys.stderr)
        sys.exit(2)

    if success_count < len(reviewers):
        print(f"NOTE: {len(reviewers) - success_count} reviewer(s) failed — results are partial.\n")

    output = {
        "document": doc_path,
        "session_model_skipped": session_model,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reviewers_total": len(reviewers),
        "reviewers_succeeded": success_count,
        "reviewers_failed": len(reviewers) - success_count,
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def parse_args() -> tuple[str, list[str], bool]:
    doc_path = None
    extra_models: list[str] = []
    include_go = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--reviewer" and i + 1 < len(args):
            extra_models.append(args[i + 1])
            i += 2
        elif args[i] == "--go":
            include_go = True
            i += 1
        elif not doc_path:
            doc_path = args[i]
            i += 1
        else:
            i += 1

    # Also check env var for extra reviewers
    env_extras = os.environ.get("RED_TEAM_EXTRA_REVIEWERS", "")
    if env_extras:
        extra_models.extend(m.strip() for m in env_extras.split(",") if m.strip())

    # If --go, prepend all OpenCode Go models to extras
    if include_go:
        extra_models = OPENCODE_GO_MODELS + extra_models

    if not doc_path:
        print(
            f"Usage: {sys.argv[0]} <document_path> [--reviewer provider/model] [--go]",
            file=sys.stderr,
        )
        sys.exit(1)

    return doc_path, extra_models, include_go


if __name__ == "__main__":
    doc_path, extra_models, include_go = parse_args()
    main(doc_path, extra_models)
