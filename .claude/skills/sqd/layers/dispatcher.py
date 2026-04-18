"""SQD dispatcher — parallel multi-LLM adversarial review dispatch."""

import asyncio
import json
import sys
from pathlib import Path

MODELS = {"gemma", "m27", "deepseek", "kimi", "qwen-coder", "devstral", "nemotron-ultra", "nemotron-3-super", "elephant", "qwen-free", "nemotron-free"}

# pi model identifiers: provider/model-id format
# Maps dispatch model name -> pi provider and model-id
PI_MODEL_MAP = {
    # google
    "gemma": "google/gemma-4-31b-it",
    # minimax
    "m27": "minimax/MiniMax-M2.7",
    # nvidia-nim
    "deepseek": "nvidia-nim/deepseek-ai/deepseek-v3.2",
    "kimi": "nvidia-nim/moonshotai/kimi-k2.5",
    "qwen-coder": "nvidia-nim/qwen/qwen3-coder-480b-a35b-instruct",
    "devstral": "nvidia-nim/mistralai/devstral-2-123b-instruct-2512",
    "nemotron-ultra": "nvidia-nim/nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "nemotron-3-super": "nvidia-nim/nvidia/llama-3.3-nemotron-super-49b-v1.5",
    # openrouter
    "elephant": "openrouter/openrouter/elephant-alpha",
    "qwen-free": "openrouter/qwen/qwen3-coder:free",
    "nemotron-free": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
}

PI_BIN = "pi.cmd"
DISPATCH_TIMEOUT_SEC = 300


def _parse_pi_jsonl(raw_output: str) -> dict | None:
    """Parse pi JSONL output, extracting final assistant message."""
    try:
        full_text = ""
        for line in raw_output.strip().splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    etype = obj.get("type")
                    if etype == "message_update":
                        part = obj.get("part", {})
                        if isinstance(part, dict):
                            ame = part.get("assistantMessageEvent", {})
                            if ame.get("type") == "text_delta":
                                delta = ame.get("delta", "")
                                if delta:
                                    full_text += delta
                    elif etype == "agent_end":
                        msgs = obj.get("messages", [])
                        for msg in msgs:
                            if msg.get("role") == "assistant":
                                # Surface API errors from the message itself
                                if msg.get("stopReason") == "error" or msg.get("errorMessage"):
                                    err = msg.get("errorMessage", "unknown error")
                                    return {"error": err}
                                content = msg.get("content", "")
                                if content:
                                    return {"text": content}
                        if full_text:
                            return {"text": full_text}
                        return obj
            except json.JSONDecodeError:
                continue
        return {"text": full_text} if full_text else None
    except Exception:
        return None


def _score_from_finding(finding: dict) -> float:
    """Extract a 0.0-1.0 quality score from a finding dict.

    Looks for common score fields in priority order.
    """
    for key in ("score", "quality_score", "confidence", "rating"):
        if key in finding and isinstance(finding[key], (int, float)):
            return float(finding[key])
    # Walk through nested dicts
    for val in finding.values():
        if isinstance(val, dict):
            score = _score_from_finding(val)
            if score >= 0:
                return score
    return 0.5  # default


async def dispatch_single(target: str, model: str, output_dir: Path) -> dict:
    """Dispatch adversarial review to a single LLM provider via pi.

    Args:
        target: Path or description of artifact to review.
        model: Model name (deepseek, gemini, claude, gpt).
        output_dir: Directory to write per-model findings.

    Returns:
        dict with at least keys: score (float 0-1), model, finding_text, raw
    """
    if model not in PI_MODEL_MAP:
        raise ValueError(f"Unknown model: {model}. Must be one of {list(PI_MODEL_MAP)}")

    pi_model = PI_MODEL_MAP[model]
    # pi uses --provider and --model as separate args
    pi_parts = pi_model.split("/", 1)
    provider = pi_parts[0]
    model_id = pi_parts[1] if len(pi_parts) > 1 else pi_model
    output_path = output_dir / f"finding_{model}.json"

    # Build the adversarial review prompt
    prompt = (
        f"You are performing an adversarial code review.\n"
        f"Review the artifact at: {target}\n\n"
        f"Provide a JSON response with:\n"
        f'{{"score": <0.0-1.0>, "summary": "<1 sentence>", "issues": ["<issue1>", ...]}}'
    )

    cmd = [PI_BIN, "--mode", "json", "--provider", provider, "--model", model_id, prompt]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=(prompt + "\n").encode()),
            timeout=DISPATCH_TIMEOUT_SEC,
        )
        return_code = proc.returncode
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"pi ({model}) timed out after {DISPATCH_TIMEOUT_SEC}s")
    except OSError as e:
        raise RuntimeError(f"Failed to spawn pi ({model}): {e}")

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    if return_code != 0:
        raise RuntimeError(f"pi ({model}) exited {return_code}: {stderr[:500]}")

    # Parse JSONL output
    result = _parse_pi_jsonl(stdout)
    if result is None:
        # Fallback: try raw JSON
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"No parseable JSON from pi ({model}). stdout: {stdout[:500]}")

    if "error" in result:
        raise RuntimeError(f"pi ({model}) API error: {result['error']}")

    score = _score_from_finding(result)
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return {
        "score": score,
        "model": model,
        "finding_text": result.get("summary", result.get("text", "")),
        "issues": result.get("issues", []),
        "raw": result,
        "output_path": str(output_path),
    }


async def dispatch_parallel(target: str, models: list[str], output_dir: Path) -> int:
    """Dispatch adversarial review to multiple LLM providers.

    Models are dispatched sequentially via pi.

    Args:
        target: Path or description of artifact to review.
        models: List of model names (deepseek, gemini, claude, gpt).
        output_dir: Directory to write findings.

    Returns:
        Exit code: 0 consensus, 1 divergent, 2 model failure, 3 target not found.
    """
    if not models:
        return 3

    findings = []
    for model in models:
        try:
            finding = await dispatch_single(target, model, output_dir)
            findings.append(finding)
        except Exception as e:
            print(f"[SQD ERROR] {e}", file=sys.stderr)
            return 2

    scores = [f["score"] for f in findings if isinstance(f, dict)]
    if not scores:
        return 2

    # Consensus: all scores within the same integer bucket (e.g. all 0.7-0.79 → 7)
    if len(set(int(s * 10) for s in scores)) == 1:
        return 0  # consensus

    await synthesize(findings, output_dir)
    return 1


async def synthesize(findings: list, output_dir: Path) -> None:
    """Synthesize divergent findings into a consensus report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "synthesis.json"
    with open(out_path, "w") as f:
        json.dump({"findings": findings}, f, indent=2, ensure_ascii=False)
