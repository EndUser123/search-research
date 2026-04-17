#!/usr/bin/env python3
"""
Benchmark GLM vs MiniMax for research_flash workloads.
Measures latency (TTFT + total) and response quality.
10 trials per model, trim top/bottom 10%, average remainder.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

# Load P:/.env for API keys
_dotenv_path = Path("P:/.env")
if _dotenv_path.exists():
    from dotenv import load_dotenv

    load_dotenv(_dotenv_path)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROMPT = (
    "Explain the difference between a mutex and a semaphore in operating systems. "
    "Include a practical code example in Python. Keep the response under 200 words."
)

GLM_CONFIG = {
    "name": "GLM-4.7 (Z.AI Max)",
    "model": "glm-4.7",
    "endpoint": "https://api.z.ai/api/coding/paas/v4/chat/completions",
    "api_key": os.environ.get("Z_AI_API_KEY", ""),  # Z_AI_API_KEY is the real key
    "headers": {
        "Authorization": f"Bearer {os.environ.get('Z_AI_API_KEY', '')}",
        "Content-Type": "application/json",
    },
}

MM_CONFIG = {
    "name": "MiniMax-M2.7",
    "model": "MiniMax-M2.7",
    "endpoint": "https://api.minimax.io/v1/chat/completions",
    "api_key": os.environ.get("MINIMAX_API_KEY", ""),
    "headers": {
        "Authorization": f"Bearer {os.environ.get('MINIMAX_API_KEY', '')}",
        "Content-Type": "application/json",
    },
}

TRIALS = 10
TRIM_PERCENT = 0.1  # 10% — remove 1 from each end for 10 trials


@dataclass
class TrialResult:
    ttft_ms: float  # Time to first token (ms)
    total_ms: float  # Total response time (ms)
    tokens: int = 0
    quality_score: float | None = None


def trim_mean(values: list[float], trim_pct: float) -> float:
    """Trim outliers and return mean of remainder."""
    if len(values) < 3:
        return statistics.mean(values)
    n_trim = max(1, int(len(values) * trim_pct))
    sorted_vals = sorted(values)
    trimmed = sorted_vals[n_trim:-n_trim] if n_trim > 0 else sorted_vals
    return statistics.mean(trimmed) if trimmed else statistics.mean(values)


def run_trial(
    client: httpx.Client,
    config: dict,
) -> TrialResult | None:
    """Run a single benchmark trial. Returns None on error."""
    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 400,
        "temperature": 0.7,
    }

    try:
        start = time.perf_counter()
        ttft: float | None = None
        total_tokens = 0
        accumulated = ""

        with client.stream("POST", config["endpoint"], json=payload, timeout=60.0) as resp:
            if resp.status_code != 200:
                body = resp.read().decode(errors="replace")
                print(f"  HTTP {resp.status_code}: {body[:200]}")
                return None

            # Streaming response — process SSE lines as they arrive
            for chunk in resp.iter_lines():
                if not chunk:
                    continue
                if chunk.startswith("data:"):
                    data = chunk[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = (
                            json.loads(data)
                            .get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if ttft is None:
                            ttft = (time.perf_counter() - start) * 1000
                        accumulated += delta
                    except json.JSONDecodeError:
                        pass
                elif ttft is None:
                    # First non-data chunk — TTFT marker
                    ttft = (time.perf_counter() - start) * 1000

        total_ms = (time.perf_counter() - start) * 1000
        total_tokens = len(accumulated.split())

        return TrialResult(ttft_ms=ttft or 0, total_ms=total_ms, tokens=total_tokens)

    except Exception as e:
        print(f"  Error: {e}")
        return None


def run_benchmark(config: dict) -> dict[str, float]:
    """Run 10 trials, trim outliers, return statistics."""
    print(f"\nBenchmarking {config['name']}...")
    print(f"  Endpoint: {config['endpoint']}")
    print(f"  Model: {config['model']}")

    client = httpx.Client(headers=config["headers"], timeout=60.0)
    results: list[TrialResult] = []

    for i in range(TRIALS):
        print(f"  Trial {i + 1}/{TRIALS}...", end=" ")
        result = run_trial(client, config)
        if result:
            results.append(result)
            print(f"TTFT={result.ttft_ms:.0f}ms  total={result.total_ms:.0f}ms")
        else:
            print("FAILED")

    client.close()

    if len(results) < 3:
        print("Not enough successful trials to compute statistics.")
        return {}

    ttfts = [r.ttft_ms for r in results]
    totals = [r.total_ms for r in results]

    n_trim = max(1, int(len(results) * TRIM_PERCENT))
    ttft_trimmed = sorted(ttfts)[n_trim:-n_trim] if n_trim > 0 else ttfts
    total_trimmed = sorted(totals)[n_trim:-n_trim] if n_trim > 0 else totals

    stats = {
        "trials": len(results),
        "trimmed_n": len(ttft_trimmed),
        "ttft_mean_ms": round(statistics.mean(ttft_trimmed), 1),
        "ttft_median_ms": round(statistics.median(ttfts), 1),
        "ttft_std_ms": round(statistics.stdev(ttfts), 1) if len(ttfts) > 1 else 0,
        "total_mean_ms": round(statistics.mean(total_trimmed), 1),
        "total_median_ms": round(statistics.median(totals), 1),
        "total_std_ms": round(statistics.stdev(totals), 1) if len(totals) > 1 else 0,
    }

    print(f"\n  Results ({len(ttft_trimmed)} trials after trimming {n_trim} each end):")
    print(
        f"  TTFT:   mean={stats['ttft_mean_ms']}ms  median={stats['ttft_median_ms']}ms  std={stats['ttft_std_ms']}ms"
    )
    print(
        f"  Total:  mean={stats['total_mean_ms']}ms  median={stats['total_median_ms']}ms  std={stats['total_std_ms']}ms"
    )

    return stats


def compare_responses(model_a: dict, res_a: TrialResult, model_b: dict, res_b: TrialResult) -> None:
    """Simple quality comparison by fetching a judge score."""
    # This is a placeholder — real implementation would call a judge LLM
    # For now, we print a note that quality comparison requires human review
    print("\nQuality comparison requires a judge LLM or human review.")
    print(f"  {model_a['name']} response: {res_a.tokens} tokens in {res_a.total_ms:.0f}ms")
    print(f"  {model_b['name']} response: {res_b.tokens} tokens in {res_b.total_ms:.0f}ms")


def main() -> None:
    print("=" * 60)
    print("GLM vs MiniMax Latency Benchmark")
    print(f"Prompt: {PROMPT[:60]}...")
    print(f"Trials: {TRIALS} per model | Trimming: {TRIM_PERCENT * 100:.0f}% each end")
    print("=" * 60)

    glm_stats = run_benchmark(GLM_CONFIG) if GLM_CONFIG["api_key"] else {}
    mm_stats = run_benchmark(MM_CONFIG) if MM_CONFIG["api_key"] else {}

    if not glm_stats or not mm_stats:
        print("\nSkipping comparison — one or both API keys missing.")
        return

    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)

    winner = lambda a, b: "GLM-4.7" if a < b else "MiniMax-M2.7"

    print("\nTime To First Token (TTFT):")
    print(f"  GLM-4.7 (Z.AI Max):   {glm_stats['ttft_mean_ms']}ms trimmed mean")
    print(f"  MiniMax-M2.7:         {mm_stats['ttft_mean_ms']}ms trimmed mean")
    print(f"  → Faster TTFT: {winner(glm_stats['ttft_mean_ms'], mm_stats['ttft_mean_ms'])}")

    print("\nTotal Response Time:")
    print(f"  GLM-4.7 (Z.AI Max):   {glm_stats['total_mean_ms']}ms trimmed mean")
    print(f"  MiniMax-M2.7:         {mm_stats['total_mean_ms']}ms trimmed mean")
    print(f"  → Faster Total: {winner(glm_stats['total_mean_ms'], mm_stats['total_mean_ms'])}")


if __name__ == "__main__":
    main()
