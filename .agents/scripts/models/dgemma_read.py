"""
DiffusionGemma direct-API file reader with enhanced multi-perspective fan-out.

Bypasses spawn_subagent (which fails with empty-content errors) and calls
the Nvidia endpoint directly. Verified working 2026-07-21 via T1-T4 tests.

Three modes:
  - single (default): one pass, fast, good for breadth scanning
  - enhanced: 3-perspective parallel fan-out + merge, higher quality
  - batch: multiple files in one call using 256K context window

Usage:
    python diffusiongemma_read.py <file_path>                     # single pass
    python diffusiongemma_read.py <file_path> --enhanced          # multi-perspective
    python diffusiongemma_read.py <dir_or_glob> --batch           # batch multiple files
    python diffusiongemma_read.py <file_path> --enhanced --json   # JSON output

Enhanced mode: 3 parallel perspectives (~2.7s fan-out) + 1 merge (~1.4s) = ~4.1s total.
Batch mode: 20 files in one call (~6.5s), 256K context, 1-sentence summaries each.

Model: google/diffusiongemma-26b-a4b-it (Google model, Nvidia inference)
Endpoint: https://integrate.api.nvidia.com/v1/chat/completions
Cost: free (Nvidia-hosted)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
API_KEY = os.environ.get(
    "NVIDIA_API_KEY",
    "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",
)
MODEL = "google/diffusiongemma-26b-a4b-it"

# Context budget for dynamic truncation (replaces the fixed max_file_chars).
# These are derived from real constraints, not magic numbers:
#   - 262144 rated tokens × ~4 chars/token = ~1M chars theoretical
#   - effective budget ~40-50% (tool-call overhead + thinking tokens)
#   - reserve ~20% for output + prompt framing
# → ~400K chars usable input budget per call.
CONTEXT_CHARS_BUDGET = 400_000
MIN_FILE_CAP = 5_000  # floor: tiny batches still get a sane per-file ceiling


def _dynamic_file_cap(num_files: int) -> int:
    """Compute the per-file char cap from the context budget, divided fairly.
    num_files=1 → full budget. num_files=20 → budget/20. Floor at MIN_FILE_CAP.
    No magic numbers — derived from CONTEXT_CHARS_BUDGET (the real context window)."""
    if num_files <= 0:
        return CONTEXT_CHARS_BUDGET
    return max(CONTEXT_CHARS_BUDGET // num_files, MIN_FILE_CAP)


DEFAULT_PROMPT = (
    "Read this SKILL.md file and produce a structured summary:\n"
    "## Purpose\n(1 sentence)\n\n"
    "## Unique techniques\n(2-3 with section name where they appear)\n\n"
    "## Failure mode prevented\n(1 sentence)\n\n"
    "Cite what's actually in the file. Do not speculate."
)

ENHANCED_PERSPECTIVES = [
    "What is the purpose of this skill? What unique techniques does it use? Be specific about technique names.",
    "What failure modes does this skill prevent? What is unique about its approach compared to standard practices?",
    "List the 3 most important features of this skill with their section names or step numbers. Include line references if visible.",
]

MERGE_PROMPT_TEMPLATE = (
    "Three analyses of the same skill file are below. Merge them into a single "
    "structured summary with these sections:\n"
    "## Purpose (1 sentence)\n"
    "## Unique techniques (2-3 with section name)\n"
    "## Failure mode prevented (1 sentence)\n\n"
    "Mark findings confirmed by multiple analyses as [HIGH] confidence. "
    "Mark findings from only one analysis as [MEDIUM].\n\n"
    "Analysis 1:\n{p1}\n\nAnalysis 2:\n{p2}\n\nAnalysis 3:\n{p3}"
)


def _log_telemetry(success: bool, latency_ms: float, error: str = "") -> None:
    """Best-effort telemetry log to usage.db via model-benchmark library. Non-blocking."""
    try:
        sys.path.insert(0, str(Path.home() / ".grok" / "skills" / "model-benchmark" / "scripts"))
        from telemetry import log_call
        log_call(
            model=MODEL, provider="nvidia",
            task_domain="extraction",
            latency_ms=round(latency_ms, 1), success=success,
            caller="dgemma_read", cost_usd=0.0,
        )
    except Exception:
        pass  # telemetry failure must never break the read


def _call_api(messages: list[dict], max_tokens: int = 600) -> str:
    """Make a single API call to DiffusionGemma."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode("utf-8"), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Accept", "application/json")
    _t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            choice = body["choices"][0]
            if choice.get("finish_reason") == "length":
                raise ValueError(
                    f"Output truncated at max_tokens. Usage: {body.get('usage', {})}"
                )
            content = choice["message"]["content"]
            if not content:
                raise ValueError(f"Empty content. Usage: {body.get('usage', {})}")
            _log_telemetry(True, (time.time() - _t0) * 1000)
            return content
    except Exception as e:
        _log_telemetry(False, (time.time() - _t0) * 1000, str(e))
        raise


def read_single(file_path: str, prompt: str | None = None, max_tokens: int = 600) -> dict:
    """Single-pass read. Fast (~1s). Good for breadth scanning."""
    content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    user_prompt = prompt or DEFAULT_PROMPT
    start = time.time()
    messages = [
        {"role": "system", "content": "You are a helpful assistant that reads files and summarizes them accurately."},
        {"role": "user", "content": f"{user_prompt}\n\n--- FILE CONTENT ---\n{content}"},
    ]
    summary = _call_api(messages, max_tokens=max_tokens)
    elapsed = time.time() - start
    return {"summary": summary, "elapsed": elapsed, "mode": "single", "calls": 1}


def read_enhanced(file_path: str) -> dict:
    """Multi-perspective parallel fan-out + merge. Higher quality (~4s)."""
    content = Path(file_path).read_text(encoding="utf-8", errors="replace")

    def call_perspective(prompt: str) -> str:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that reads files and summarizes them accurately."},
            {"role": "user", "content": f"{prompt}\n\n--- FILE CONTENT ---\n{content}"},
        ]
        return _call_api(messages)

    # Parallel fan-out
    start = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(call_perspective, p): i for i, p in enumerate(ENHANCED_PERSPECTIVES)}
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()
    fan_out_elapsed = time.time() - start

    # Sequential merge
    merge_start = time.time()
    merge_prompt = MERGE_PROMPT_TEMPLATE.format(
        p1=results[0], p2=results[1], p3=results[2]
    )
    merged = _call_api(
        [
            {"role": "system", "content": "You are an expert at synthesizing multiple analyses into a coherent summary."},
            {"role": "user", "content": merge_prompt},
        ],
        max_tokens=800,
    )
    merge_elapsed = time.time() - merge_start
    total_elapsed = time.time() - start

    return {
        "summary": merged,
        "elapsed": total_elapsed,
        "fan_out_elapsed": fan_out_elapsed,
        "merge_elapsed": merge_elapsed,
        "mode": "enhanced",
        "calls": 4,
        "perspectives": [results[i] for i in range(3)],
    }


GENERIC_STEMS = {"SKILL", "README", "INDEX", "CHANGELOG", "TODO", "NOTES"}


def _display_name(p: Path) -> str:
    """Prefer parent dir name when the filename is generic (SKILL.md, README.md).
    Avoids batch output where every skill shows up as name='SKILL'."""
    if p.stem.upper() in GENERIC_STEMS and p.parent != p.parent.parent:
        return p.parent.name
    return p.stem


def read_batch(
    file_paths: list[str],
    prompt: str | None = None,
    batch_size: int = 20,
    max_file_chars: int | None = None,
) -> dict:
    """Batch multiple files into one API call using 256K context.

    Groups files into batches of batch_size (default 20), sends each batch
    as a single call, and returns combined summaries.

    Args:
        file_paths: list of file paths to read
        prompt: custom summary prompt (default: 1-sentence purpose per file)
        batch_size: max files per API call (default 20, ~50K tokens)
        max_file_chars: per-file char cap. None = dynamic (derived from CONTEXT_CHARS_BUDGET // batch_count). The dynamic cap self-adjusts: 2 files → ~200K each, 20 files → ~20K each.

    Returns dict with:
        - summaries: list of {file, summary} dicts
        - elapsed: total wall time
        - calls: number of API calls made
        - mode: "batch"
    """
    # Prompt with explicit file count to prevent the model from stopping early.
    # Without "EXACTLY N files", the model non-deterministically skips the last
    # file when the batch is large (observed: 6 files in → 5 summaries out).
    if prompt:
        user_prompt = prompt
    else:
        # The count is injected per-batch below (after batching).
        user_prompt = None

    # Dynamic cap: if caller didn't specify, derive from context budget.
    # This is the self-adjusting cap — no fixed magic number.
    if max_file_chars is None:
        # Use the largest batch (first group) to size the cap; all batches
        # use the same cap so summaries are comparable across batches.
        effective_batch = min(batch_size, len(file_paths)) if file_paths else 1
        max_file_chars = _dynamic_file_cap(effective_batch)

    # Read and prepare file contents
    prepared = []
    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            prepared.append({"path": fp, "name": _display_name(p), "content": "[FILE MISSING]", "truncated": False})
            continue
        content = p.read_text(encoding="utf-8", errors="replace")
        truncated = False
        if len(content) > max_file_chars:
            content = content[:max_file_chars] + "\n... [truncated]"
            truncated = True
        prepared.append({"path": fp, "name": _display_name(p), "content": content, "truncated": truncated})

    # Batch into groups
    batches = []
    for i in range(0, len(prepared), batch_size):
        batch = prepared[i : i + batch_size]
        batch_text = []
        for j, f in enumerate(batch):
            batch_text.append(f"--- FILE {j+1}: {f['name']} ---\n{f['content']}")
        batches.append({
            "files": batch,
            "text": "\n\n".join(batch_text),
            "count": len(batch),
        })

    start = time.time()
    all_summaries = []

    for bi, batch in enumerate(batches):
        # Build the count-explicit prompt for this batch.
        if user_prompt is None:
            effective_prompt = (
                f"There are EXACTLY {batch['count']} files below. "
                f"You MUST produce a numbered summary for ALL {batch['count']} files "
                f"(items 1 through {batch['count']}). "
                f"For EACH file, provide a 1-sentence summary of its purpose. "
                f"Format as a numbered list 1-{batch['count']}."
            )
        else:
            effective_prompt = user_prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that reads files and summarizes them accurately.",
            },
            {
                "role": "user",
                "content": f"{effective_prompt}\n\n{batch['text']}",
            },
        ]
        max_tokens = min(200 * batch["count"] + 200, 4000)
        try:
            result = _call_api(messages, max_tokens=max_tokens)
        except Exception as e:
            result = f"[BATCH ERROR: {type(e).__name__}: {e}]"

        # Parse numbered list from result
        import re
        lines = result.strip().split("\n")
        current_num = 0
        for line in lines:
            match = re.match(r"^(\d+)[\.\)]\s*(.+)", line.strip())
            if match:
                num = int(match.group(1))
                summary = match.group(2).strip()
                if current_num < len(batch["files"]):
                    f = batch["files"][current_num]
                    all_summaries.append({
                        "file": f["path"],
                        "name": f["name"],
                        "summary": summary,
                        "truncated": f["truncated"],
                    })
                current_num += 1
            elif current_num > 0 and current_num <= len(batch["files"]) and line.strip() and not match:
                # continuation of previous summary
                if all_summaries:
                    all_summaries[-1]["summary"] += " " + line.strip()

    elapsed = time.time() - start
    return {
        "summaries": all_summaries,
        "elapsed": elapsed,
        "calls": len(batches),
        "mode": "batch",
        "total_files": len(file_paths),
        "summarized": len(all_summaries),
    }


def main():
    parser = argparse.ArgumentParser(description="DiffusionGemma file reader")
    # Accept one or more paths. Single/enhanced mode uses paths[0]; batch mode uses all.
    parser.add_argument("paths", nargs="+", help="One or more paths: file (single/enhanced), multiple files (batch), or directory/glob (batch)")
    parser.add_argument("--enhanced", action="store_true", help="Use multi-perspective fan-out + merge")
    parser.add_argument("--batch", action="store_true", help="Batch multiple files in one call (files, directory, or glob pattern)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--prompt", default=None, help="Custom prompt")
    parser.add_argument(
        "--prompt-file",
        type=Path,
        default=None,
        help="Read a custom prompt from a file (avoids Windows command-line limits)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=600,
        help="Maximum output tokens for single-file mode (default: 600)",
    )
    parser.add_argument("--batch-size", type=int, default=20, help="Max files per API call (batch mode)")
    parser.add_argument("--pattern", default="*.md", help="Glob pattern for directory mode (default: *.md; use SKILL.md for skill trees)")
    args = parser.parse_args()

    try:
        if args.max_tokens <= 0:
            parser.error("--max-tokens must be positive")
        if args.prompt and args.prompt_file:
            parser.error("--prompt and --prompt-file are mutually exclusive")
        custom_prompt = args.prompt
        if args.prompt_file:
            custom_prompt = args.prompt_file.read_text(encoding="utf-8")

        if args.batch:
            # Resolve files from: (a) multiple explicit paths, (b) a directory, (c) a glob.
            files = []
            for path_arg in args.paths:
                p = Path(path_arg)
                if p.is_dir():
                    # Directory mode: rglob with --pattern (default *.md; SKILL.md for skill trees)
                    files.extend(str(f) for f in p.rglob(args.pattern))
                elif "*" in path_arg or "?" in path_arg:
                    import glob
                    files.extend(glob.glob(path_arg))
                elif p.is_file():
                    files.append(path_arg)
                else:
                    print(f"ERROR: path not found or not a file/dir/glob: {path_arg}", file=sys.stderr)
                    sys.exit(1)
            files = sorted(set(files))  # dedupe

            if not files:
                print(f"ERROR: No files found for paths: {args.paths}", file=sys.stderr)
                sys.exit(1)

            print(f"Batching {len(files)} files (batch_size={args.batch_size})...", file=sys.stderr)
            result = read_batch(files, prompt=custom_prompt, batch_size=args.batch_size)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                for s in result["summaries"]:
                    print(f"- **{s['name']}**: {s['summary']}")
                print(f"\n--- batch mode: {result['elapsed']:.1f}s, {result['calls']} calls, {result['summarized']}/{result['total_files']} files ---", file=sys.stderr)

        elif args.enhanced:
            result = read_enhanced(args.paths[0])
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(result["summary"])
                print(f"\n--- {result['mode']} mode: {result['elapsed']:.1f}s, {result['calls']} calls ---", file=sys.stderr)

        else:
            result = read_single(
                args.paths[0], prompt=custom_prompt, max_tokens=args.max_tokens
            )
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(result["summary"])
                print(f"\n--- {result['mode']} mode: {result['elapsed']:.1f}s, {result['calls']} calls ---", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
