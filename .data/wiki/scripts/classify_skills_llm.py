#!/usr/bin/env python3
"""
Classify unmatched skills using a free model via direct API.

Reads skills from scan_external_skills.py that couldn't be classified by
keyword heuristics, sends them to mistral-medium-latest (free, 2s latency)
via direct HTTP API, and outputs the classified domains.

Batches N skills per API call to minimize latency (103 skills / 10 per batch
= 11 API calls at ~2s each = ~22s total).

Usage:
    python classify_skills_llm.py                  # classify + print results
    python classify_skills_llm.py --json           # JSON output
    python classify_skills_llm.py --batch-size 20  # skills per API call
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Import the scanner to get unmatched skills
sys.path.insert(0, str(Path(__file__).parent))
from scan_external_skills import scan_all_roots

# Mistral API (free tier, direct API — not spawn_subagent)
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-medium-latest"

# Fallback: NVIDIA-hosted GPT-OSS 20B (free, no rate limits)
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "openai/gpt-oss-20b"


def _load_api_keys() -> tuple[str, str]:
    """Load API keys from environment or config.toml (never hardcoded)."""
    mistral_key = os.environ.get("MISTRAL_API_KEY", "")
    nvidia_key = os.environ.get("NVIDIA_API_KEY", "")

    if not mistral_key or not nvidia_key:
        # Fall back to config.toml
        import re as _re
        config_path = Path(os.environ.get("USERPROFILE", "")) / ".grok" / "config.toml"
        if config_path.exists():
            config = config_path.read_text(encoding="utf-8", errors="replace")
            if not mistral_key:
                m = _re.search(r'\[model\.mistral-medium-latest\].*?api_key\s*=\s*"([^"]+)"', config, _re.DOTALL)
                if m:
                    mistral_key = m.group(1)
            if not nvidia_key:
                nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
                if not nvidia_key:
                    m2 = _re.search(r'nvapi-[A-Za-z0-9]+', config)
                    if m2:
                        nvidia_key = m2.group(0)
    return mistral_key, nvidia_key


SYSTEM_PROMPT = """You are a skill classifier. For each skill, output exactly one domain label.

Available domains:
- discovery: search, research, web scraping, crawling, information finding
- review: code review, critique, audit, adversarial analysis, stress-testing
- orchestration: pipelines, workflows, SDLC, task routing, delegation
- design: planning, architecture, specs, blueprints, brainstorming
- cross-model: second opinions, model comparison, external LLM dispatch
- fleet-ops: benchmarking, telemetry, monitoring, health checks, maintenance
- infrastructure: git, hooks, MCP servers, config, plugins, permissions, auth
- knowledge: wikis, notebooks, memory, documentation, handoffs, logging
- communication: email, slack, notifications, alerts, messaging
- content: images, video, PDFs, documents, game assets, UI/UX generation
- verification: testing, validation, assertions, TDD, completion checks
- coding: code generation, debugging, refactoring, implementation, SDKs

Output format: one JSON object per line, like:
{"name": "<skill-name>", "domain": "<domain>"}
"""


def call_mistral(messages: list[dict], timeout: int = 30) -> str:
    """Call Mistral API directly via HTTP."""
    mistral_key, _ = _load_api_keys()
    if not mistral_key:
        raise RuntimeError("No Mistral API key found (env MISTRAL_API_KEY or config.toml)")

    payload = json.dumps({
        "model": MISTRAL_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        MISTRAL_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mistral_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def call_nvidia(messages: list[dict], timeout: int = 60) -> str:
    """Call NVIDIA NIM API as fallback."""
    _, nvidia_key = _load_api_keys()
    if not nvidia_key:
        raise RuntimeError("No NVIDIA API key found (env NVIDIA_API_KEY or config.toml)")

    payload = json.dumps({
        "model": NVIDIA_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        NVIDIA_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {nvidia_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def call_model(messages: list[dict]) -> str:
    """Try Mistral first, fall back to NVIDIA on failure."""
    try:
        return call_mistral(messages)
    except Exception as e:
        print(f"  Mistral failed ({e}), trying NVIDIA...", file=sys.stderr)
        return call_nvidia(messages)


def extract_skill_info(skill_path: str) -> dict:
    """Read name + description from a SKILL.md file."""
    try:
        body = Path(skill_path).read_text(encoding="utf-8", errors="replace")
        parts = body.split("---", 2)
        if len(parts) < 3:
            return {"name": Path(skill_path).parent.name, "description": body[:500]}

        fm = parts[1]
        body_text = parts[2][:800]  # first 800 chars of body for context

        import re
        name_m = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
        desc_m = re.search(r'description:\s*>?\s*\n?\s*(.+?)(?:\n\n|\n\w)', fm, re.DOTALL)

        name = name_m.group(1).strip().strip("'\"") if name_m else Path(skill_path).parent.name
        desc = desc_m.group(1).strip()[:300] if desc_m else body_text[:300]

        return {"name": name, "description": desc}
    except Exception:
        return {"name": Path(skill_path).parent.name, "description": ""}


def classify_batch(skills_batch: list[dict]) -> list[str]:
    """Classify a batch of skills via one API call. Returns list of domains (by position)."""

    # Build the user message with all skills in the batch
    lines = ["Classify each skill into exactly one domain. Output one JSON line per skill, using the skill number.\n"]
    infos = []
    for i, s in enumerate(skills_batch):
        info = extract_skill_info(s["path"])
        infos.append(info)
        lines.append(f'{i+1}. Name: {info["name"]}')
        lines.append(f'   Description: {info["description"]}')
        lines.append("")

    user_msg = "\n".join(lines)

    system = SYSTEM_PROMPT.replace(
        'Output format: one JSON object per line, like:\n{"name": "<skill-name>", "domain": "<domain>"}',
        'Output format: one JSON object per line, using the NUMBER, like:\n{"num": 1, "domain": "<domain>"}\n{"num": 2, "domain": "<domain>"}'
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]

    response = call_model(messages)

    # Parse JSON lines from response — match by number, not name
    domains_by_num: dict[int, str] = {}
    for line in response.strip().split("\n"):
        line = line.strip().strip("`,")
        if not line:
            continue
        try:
            obj = json.loads(line)
            num = obj.get("num", 0)
            domain = obj.get("domain", "").strip().lower()
            if num and domain:
                domains_by_num[int(num)] = domain
        except (json.JSONDecodeError, ValueError):
            continue

    # Build results by position (1-indexed from prompt)
    results = []
    for i in range(len(skills_batch)):
        results.append(domains_by_num.get(i + 1, "unmatched"))

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Classify unmatched skills via free LLM")
    parser.add_argument("--batch-size", type=int, default=10, help="Skills per API call")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--all", action="store_true", help="Classify ALL skills (not just unmatched)")
    args = parser.parse_args()

    print("Scanning all skills...", file=sys.stderr)
    all_skills = scan_all_roots()

    if args.all:
        to_classify = all_skills
    else:
        to_classify = [s for s in all_skills if s["inferred_domain"] == "unmatched"]

    print(f"Classifying {len(to_classify)} skills via mistral-medium-latest...", file=sys.stderr)

    # Batch and classify
    all_results = {}  # path -> domain
    batch_count = 0
    for i in range(0, len(to_classify), args.batch_size):
        batch = to_classify[i : i + args.batch_size]
        batch_count += 1
        batch_names = [extract_skill_info(s["path"])["name"] for s in batch]
        print(f"  Batch {batch_count}: {len(batch)} skills ({', '.join(batch_names[:3])}...)", file=sys.stderr)

        try:
            t0 = time.time()
            domains = classify_batch(batch)
            elapsed = time.time() - t0
            print(f"    -> {len([d for d in domains if d != 'unmatched'])} classified in {elapsed:.1f}s", file=sys.stderr)
            for j, s in enumerate(batch):
                all_results[s["path"]] = domains[j] if j < len(domains) else "unmatched"
        except Exception as e:
            print(f"    -> FAILED: {e}", file=sys.stderr)

    # Merge results with original skill data
    classified = []
    for s in to_classify:
        info = extract_skill_info(s["path"])
        llm_domain = all_results.get(s["path"], "unmatched")
        classified.append({
            "name": info["name"],
            "path": s["path"],
            "source": s["source"],
            "llm_domain": llm_domain,
            "description": info["description"][:150],
        })

    if args.json:
        print(json.dumps(classified, indent=2))
    else:
        # Print summary
        from collections import Counter
        domain_counts = Counter(c["llm_domain"] for c in classified)
        print(f"\nClassification complete: {len(classified)} skills")
        print("\nBy domain (LLM-classified):")
        for domain, count in domain_counts.most_common():
            print(f"  {domain:20s}: {count}")

        # Print details
        print("\nDetails:")
        for c in sorted(classified, key=lambda x: (x["llm_domain"], x["name"])):
            print(f"  {c['llm_domain']:20s}  {c['name']:35s} ({c['source']})")


if __name__ == "__main__":
    main()
