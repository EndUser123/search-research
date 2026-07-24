#!/usr/bin/env python3
"""
Adaptive extraction utility — the Layer 1 context firewall.

This script reads file(s), constructs a prompt, calls a completion model
(DiffusionGemma primary, fallbacks), and returns structured JSON. The
orchestrator never sees raw file content — only the extracted facts.

Implements the mitigations from [[context-firewall-architecture]]:

  1. --prompt: arbitrary extraction intent (not hardcoded templates)
  2. --generous: over-extract by default (cheaper than re-introduction)
  3. --confidence: model self-rates extraction quality; low → escalate to Layer 2
  4. --threshold: size check (<5K words → "read directly, skip Layer 1")
  5. --multi: merge multiple files for cross-file context
  6. --re-extract: re-run with different prompt when Layer 1 was insufficient
  7. Telemetry: every call logged to usage.jsonl

Usage:
    # Basic extraction
    python extract.py file.py --prompt "extract all function signatures and return types"

    # Generous mode (extract more than asked — for uncertain tasks)
    python extract.py file.py --prompt "summarize error handling" --generous

    # Multi-file cross-file extraction
    python extract.py core.py app.py --prompt "trace how compare_folders is called" --multi

    # JSON output
    python extract.py *.py --prompt "list all imports from external libraries" --format json

    # Check if Layer 1 is even needed (size threshold)
    python extract.py small_config.json --prompt "extract settings" --check-only
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────

# Size threshold: files smaller than this (in words) should be read directly,
# not routed through Layer 1. The firewall overhead exceeds the benefit.
SIZE_THRESHOLD_WORDS = 5000

# Context budget per call (DiffusionGemma: 262K tokens rated, ~40-50% effective)
MAX_CONTEXT_CHARS = 100_000  # ~25K tokens, conservative for safety

# API endpoints (from config.toml — hardcoded here for standalone use)
DGEMMA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DGEMMA_MODEL = "google/diffusiongemma-26b-a4b-it"

# Telemetry integration
TELEMETRY_SCRIPT = Path(r"C:\Users\brsth\.grok\skills\model-benchmark\scripts\telemetry.py")

# ── Helpers ────────────────────────────────────────────────────────────────


def read_api_key() -> str:
    """Read NVIDIA API key from Grok config.toml."""
    import tomllib
    config_path = Path.home() / ".grok" / "config.toml"
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    # Try nested dict format
    if "model" in config:
        for slug, section in config["model"].items():
            if slug == "nvidia-diffusiongemma-26b" and isinstance(section, dict):
                return section.get("api_key", "")
    # Try flat key format
    for key, section in config.items():
        if key == "model.nvidia-diffusiongemma-26b" and isinstance(section, dict):
            return section.get("api_key", "")
    return os.environ.get("NVIDIA_API_KEY", "")


def count_words(text: str) -> int:
    """Approximate word count for size threshold check."""
    return len(text.split())


def read_files(file_paths: list[str]) -> list[dict]:
    """Read files and return list of {path, content, words, error}."""
    results = []
    for fp in file_paths:
        try:
            content = Path(fp).read_text(encoding="utf-8", errors="replace")
            results.append({
                "path": fp,
                "content": content,
                "words": count_words(content),
                "error": None,
            })
        except Exception as e:
            results.append({
                "path": fp,
                "content": "",
                "words": 0,
                "error": str(e),
            })
    return results


def build_prompt(files: list[dict], extraction_intent: str, generous: bool, multi: bool) -> str:
    """Construct the extraction prompt from file content + intent."""
    # Build file context
    file_sections = []
    for f in files:
        if f["error"]:
            file_sections.append(f"## File: {f['path']}\n[ERROR: {f['error']}]")
        else:
            file_sections.append(f"## File: {f['path']}\n```\n{f['content']}\n```")

    files_text = "\n\n".join(file_sections)

    # Build extraction instruction
    generous_note = ""
    if generous:
        generous_note = """\
EXTRACTION MODE: GENEROUS. Extract MORE than asked. Include related context,
adjacent details, and anything potentially relevant. Over-extraction is better
than under-extraction here — the consumer can filter, but cannot recover what
you omit.
"""

    multi_note = ""
    if multi and len(files) > 1:
        multi_note = """\
CROSS-FILE MODE: These files are related. Look for cross-file patterns:
functions defined in one file and called in another, shared data structures,
import/export relationships, and naming conventions that span files.
"""

    confidence_instruction = """\
CONFIDENCE: After your extraction, rate your confidence (high/medium/low) that
this extraction captures everything the requester needs. If you suspect you may
have missed something important, or if the files contain content that doesn't
fit the extraction intent but might be significant (e.g., security issues,
architectural patterns, unexpected code), set confidence to "low" and note what
you might have missed in the "escalation_hint" field.
"""

    prompt = f"""You are a code analysis assistant. Extract information from the following file(s).

{generous_note}{multi_note}
EXTRACTION REQUEST: {extraction_intent}

{files_text}

{confidence_instruction}

Return your response as JSON with this structure:
{{
  "extraction": <your extracted content — the main output>,
  "confidence": "high" | "medium" | "low",
  "escalation_hint": "<if confidence is low, explain what might be missed and suggest whether a full re-read with tools is needed>",
  "anomalies": ["<list any unexpected findings: security issues, architectural concerns, or anything not matching the extraction intent but potentially important>"],
  "files_covered": {len(files)},
  "notes": "<any caveats about the extraction>"
}}
"""
    return prompt


def call_model(prompt: str, api_key: str, timeout: int = 60) -> dict:
    """Call DiffusionGemma API and return the response."""
    import requests

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DGEMMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise code analysis assistant. Always respond in valid JSON when asked."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.0,  # deterministic extraction — see [[context-firewall-architecture]] § "Determinism"
    }

    start = time.monotonic()
    try:
        resp = requests.post(DGEMMA_URL, json=payload, headers=headers, timeout=timeout)
        elapsed_ms = (time.monotonic() - start) * 1000

        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "latency_ms": elapsed_ms,
            }

        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return {
            "success": True,
            "content": content,
            "latency_ms": elapsed_ms,
            "input_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"),
        }
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "success": False,
            "error": f"{type(e).__name__}: {e}",
            "latency_ms": elapsed_ms,
        }


def log_telemetry(latency_ms: float, success: bool, files_count: int,
                  input_tokens: int | None, output_tokens: int | None,
                  extraction_intent: str, error: str = "") -> None:
    """Log to telemetry if the library is available (best-effort)."""
    try:
        sys.path.insert(0, str(TELEMETRY_SCRIPT.parent))
        from telemetry import log_call
        log_call(
            model="nvidia-diffusiongemma-26b",
            provider="nvidia",
            task_domain="extraction",
            latency_ms=latency_ms,
            success=success,
            caller="extract.py",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error_type=error,
            notes=f"intent={extraction_intent[:80]}; files={files_count}",
        )
    except (ImportError, OSError, TypeError) as e:
        # Telemetry is best-effort — log to stderr so failures are visible, not silent
        print(f"telemetry warning: {type(e).__name__}: {e}", file=sys.stderr)
    except Exception as e:
        # Unexpected error — surface it rather than silently swallowing
        print(f"telemetry UNEXPECTED error: {type(e).__name__}: {e}", file=sys.stderr)


def parse_json_response(content: str) -> dict:
    """Parse JSON from model response, handling markdown code fences."""
    # Strip markdown code fences if present
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        if lines[0].startswith("```"):
            lines = lines[1:]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        # Fallback: return raw content
        return {
            "extraction": content,
            "confidence": "unknown",
            "escalation_hint": "Model response was not valid JSON — raw content returned. Consider re-extracting or escalating to Layer 2.",
            "anomalies": [],
            "files_covered": 0,
            "notes": "JSON parse failed",
        }


# ── Main ───────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive extraction utility — Layer 1 context firewall",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract function signatures
  python extract.py app.py --prompt "extract all function signatures and return types"

  # Generous extraction (over-extract for uncertain tasks)
  python extract.py core.py --prompt "summarize the data flow" --generous

  # Multi-file cross-file analysis
  python extract.py core.py app.py tests/test_core.py --prompt "trace how compare_folders is tested" --multi

  # Check if Layer 1 is needed (size threshold)
  python extract.py small_config.json --prompt "extract settings" --check-only

  # JSON output for programmatic consumption
  python extract.py *.py --prompt "list security-relevant code patterns" --format json
        """,
    )
    parser.add_argument("files", nargs="+", help="File(s) to extract from")
    parser.add_argument("--prompt", required=True,
                        help="Extraction intent — what to extract from the files")
    parser.add_argument("--generous", action="store_true",
                        help="Over-extract by default (include adjacent details)")
    parser.add_argument("--multi", action="store_true",
                        help="Multi-file mode — look for cross-file patterns")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check if Layer 1 is needed (size threshold); don't extract")
    parser.add_argument("--timeout", type=int, default=60,
                        help="API timeout in seconds (default: 60)")
    parser.add_argument("--no-telemetry", action="store_true",
                        help="Don't log to telemetry JSONL")
    args = parser.parse_args()

    # Read files
    files = read_files(args.files)
    total_words = sum(f["words"] for f in files)
    total_chars = sum(len(f["content"]) for f in files)

    # Check for read errors
    errors = [f for f in files if f["error"]]
    if errors:
        for e in errors:
            print(f"ERROR reading {e['path']}: {e['error']}", file=sys.stderr)
        if len(errors) == len(files):
            sys.exit(1)

    # Size threshold check (mitigation 7: overuse trap)
    if args.check_only:
        if total_words < SIZE_THRESHOLD_WORDS:
            print(json.dumps({
                "layer_1_needed": False,
                "reason": f"Files total {total_words} words (< {SIZE_THRESHOLD_WORDS} threshold). Read directly — Layer 1 overhead exceeds benefit.",
                "total_words": total_words,
                "files": len(files),
            }, indent=2))
        else:
            print(json.dumps({
                "layer_1_needed": True,
                "reason": f"Files total {total_words} words (>= {SIZE_THRESHOLD_WORDS} threshold). Layer 1 extraction recommended.",
                "total_words": total_words,
                "files": len(files),
            }, indent=2))
        return

    # Auto-skip Layer 1 for small files (unless --multi forces it)
    if not args.multi and total_words < SIZE_THRESHOLD_WORDS:
        result = {
            "layer_1_needed": False,
            "reason": f"Files total {total_words} words (< {SIZE_THRESHOLD_WORDS} threshold). Read directly.",
            "total_words": total_words,
            "files": [f["path"] for f in files],
            "recommendation": "These files are small enough to read directly in the orchestrator. Layer 1 extraction adds latency without meaningful context savings.",
        }
        print(json.dumps(result, indent=2) if args.format == "json" else result["reason"])
        return

    # Context budget check (truncate if needed, at line boundaries)
    truncated_files = []
    if total_chars > MAX_CONTEXT_CHARS:
        scale = MAX_CONTEXT_CHARS / total_chars
        for f in files:
            if f["content"]:
                max_len = int(len(f["content"]) * scale)
                # Enforce a per-file minimum so small files aren't gutted
                max_len = max(max_len, 1000)
                if len(f["content"]) > max_len:
                    # Truncate at the nearest preceding newline (preserves syntax boundaries)
                    cut_point = f["content"].rfind("\n", 0, max_len)
                    if cut_point < max_len * 0.8:
                        cut_point = max_len  # fallback if no newline found nearby
                    f["content"] = f["content"][:cut_point] + "\n... [TRUNCATED for context budget] ..."
                    truncated_files.append(f["path"])
        if truncated_files:
            print(f"WARNING: {len(truncated_files)} file(s) truncated at line boundaries for context budget: {', '.join(truncated_files)}", file=sys.stderr)

    # Build prompt
    prompt = build_prompt(files, args.prompt, args.generous, args.multi)

    # Get API key
    api_key = read_api_key()
    if not api_key:
        print(json.dumps({
            "error": "No NVIDIA API key found in config.toml or env. Set NVIDIA_API_KEY or check config.",
            "layer_1_needed": True,
            "total_words": total_words,
        }, indent=2))
        sys.exit(1)

    # Call model
    print(f"Extracting from {len(files)} file(s) ({total_words} words)...", file=sys.stderr)
    result = call_model(prompt, api_key, timeout=args.timeout)

    # Log telemetry
    if not args.no_telemetry:
        log_telemetry(
            latency_ms=result.get("latency_ms", 0),
            success=result["success"],
            files_count=len(files),
            input_tokens=result.get("input_tokens"),
            output_tokens=result.get("output_tokens"),
            extraction_intent=args.prompt,
            error="" if result["success"] else result.get("error", "")[:100],
        )

    if not result["success"]:
        print(json.dumps({
            "error": result["error"],
            "latency_ms": result.get("latency_ms", 0),
            "layer_1_needed": True,
            "recommendation": "Layer 1 extraction failed. Options: (1) retry, (2) fall back to gemma-4-31b-it or gemini-3.5-flash-lite, (3) escalate to Layer 2 agent with file read access.",
        }, indent=2))
        sys.exit(1)

    # Parse response
    parsed = parse_json_response(result["content"])

    # Add metadata
    parsed["_meta"] = {
        "latency_ms": result["latency_ms"],
        "input_tokens": result.get("input_tokens"),
        "output_tokens": result.get("output_tokens"),
        "files_extracted": len(files),
        "total_words": total_words,
        "generous_mode": args.generous,
        "multi_mode": args.multi,
        "extraction_intent": args.prompt,
        "layer_1_needed": True,
    }

    # Escalation logic (mitigations 1-3)
    confidence = parsed.get("confidence", "unknown")
    anomalies = parsed.get("anomalies", [])
    if confidence == "low" or anomalies:
        parsed["_meta"]["escalation_recommended"] = True
        parsed["_meta"]["escalation_reason"] = []
        if confidence == "low":
            parsed["_meta"]["escalation_reason"].append(
                "Low extraction confidence — Layer 2 agent with file access may find more."
            )
        if anomalies:
            parsed["_meta"]["escalation_reason"].append(
                f"{len(anomalies)} anomalies detected that may need deeper investigation."
            )

    # Output
    if args.format == "json":
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    else:
        # Text format: just the extraction + escalation hint
        print(parsed.get("extraction", ""))
        if parsed.get("_meta", {}).get("escalation_recommended"):
            print(f"\n--- ESCALATION RECOMMENDED ---", file=sys.stderr)
            for r in parsed["_meta"]["escalation_reason"]:
                print(f"  - {r}", file=sys.stderr)
            hint = parsed.get("escalation_hint", "")
            if hint:
                print(f"  Hint: {hint}", file=sys.stderr)


if __name__ == "__main__":
    main()
