#!/usr/bin/env python3
"""synthesize_subtopics.py — Stage C (v3): LLM-synthesize a concept page per sub-topic cluster.

For each cluster in subtopics.json, gather the contributing transcripts and
ask an LLM to synthesize a wiki concept page: a definition grounded in the
sources, operational details, verifiable values, related concepts, and
per-claim citations back to the contributing transcripts (source_id + title +
verbatim excerpt). The output is a concept JSON array shaped for the existing
reconcile.py + write_pages.py stages (write_pages renders it; reconcile dedups it).

Backend: `mmx` CLI (MiniMax-M2.7) by default, verified working on this host
via the node-script resolver documented in the /mmx skill. DiffusionGemma
(`dgemma`) is a free fallback. Direct MiniMax/ZAI HTTP APIs are NOT used —
the env keys are CLI-scoped, not platform-scoped (verified by probe this session).

Usage:
  python synthesize_subtopics.py --subtopics P:/tmp/subtopics.json \\
      --transcripts-dir P:/.data/wiki/sources/transcripts/ \\
      --notebook <uuid> --notebook-title "Pilot" -o P:/tmp/concepts.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


# --- transcripts ---------------------------------------------------------

def read_transcript(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    m = FRONTMATTER_RE.match(raw)
    text = raw
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"').strip("'")
        text = raw[m.end():]
    return {"source_id": meta.get("source_id", path.stem), "title": meta.get("title", ""),
            "url": (meta.get("url") or "").strip() or None, "text": text.strip()}


def gather_members(cluster: dict, transcripts_dir: Path) -> list[dict]:
    members: list[dict] = []
    for sid in cluster.get("member_source_ids", []):
        p = transcripts_dir / f"{sid}.md"
        if p.exists():
            members.append(read_transcript(p))
    return members


def build_context(members: list[dict], per_member_chars: int, max_members: int) -> str:
    """Build the transcript context for the LLM, capping length.

    Caps: per_member_chars (default 1200) keeps each transcript's opening;
    max_members (default 20) bounds total input. If a cluster exceeds
    max_members, members are sampled evenly so the synthesis sees the spread.
    """
    selected = members
    if len(members) > max_members:
        step = len(members) / max_members
        idxs = [int(i * step) for i in range(max_members)]
        selected = [members[i] for i in idxs]
    parts = []
    for i, m in enumerate(selected, 1):
        body = m["text"][:per_member_chars]
        parts.append(f"### Source {i}: {m['title']}\n[source_id: {m['source_id']}]\n\n{body}")
    return "\n\n---\n\n".join(parts)


SYNTH_PROMPT = """You are synthesizing a wiki concept page from raw video transcripts.

TOPIC HINT: {hint}

Below are {n} transcript excerpts from videos in the same NotebookLM notebook,
clustered together because they discuss the same sub-topic. Synthesize a
cohesive wiki concept page that distills what these sources collectively say.

GROUNDING RULES (strict):
- Use ONLY information present in the transcripts. Do not invent facts, numbers, or quotes.
- Every claim in details/values must cite its source via the citations array.
- If sources disagree, note the disagreement; do not paper over it.
- Write for a technical reader who values precision over hand-holding.

OUTPUT: a single JSON object (no markdown fences, no prose before/after) with EXACTLY this shape:
{{
  "title": "Concise sub-topic name (2-6 words, Title Case)",
  "definition": "1-3 sentence definition of what this concept IS, grounded in the sources",
  "details": ["operational detail / mechanism / threshold / how-it-works (one bullet each)"],
  "values": [{{"name": "parameter or metric name", "value": "the concrete value with unit if any"}}],
  "related": ["name of a related concept that a reader would want to link to"],
  "citations": [{{"claim": "the specific claim being supported", "source_title": "exact Source title from above", "cited_text": "short verbatim excerpt from that source"}}]
}}

TRANSCRIPTS:
{context}

Return ONLY the JSON object."""


# --- LLM backends --------------------------------------------------------

def _resolve_mmx_cmd() -> list[str]:
    """Resolve the mmx CLI on Windows (node-script resolver from /mmx skill)."""
    node_script = os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules",
                               "mmx-cli", "dist", "mmx.mjs")
    if os.path.exists(node_script):
        return ["node", node_script]
    return ["mmx"]


def call_mmx(prompt: str, model: str | None, timeout: int) -> tuple[str, str]:
    """Call mmx text chat, return (text, error)."""
    cmd = _resolve_mmx_cmd() + ["text", "chat", "--message", prompt,
                                "--output", "json", "--non-interactive", "--timeout", str(timeout)]
    if model:
        cmd.extend(["--model", model])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return "", "mmx timeout"
    if r.returncode != 0:
        return "", f"mmx rc={r.returncode}: {r.stderr.strip()[:200]}"
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return "", f"mmx non-JSON: {r.stdout.strip()[:200]}"
    base = data.get("base_resp", {}) if isinstance(data, dict) else {}
    if base.get("status_code", 0) != 0:
        return "", f"mmx status {base.get('status_code')}: {base.get('status_msg', '')[:150]}"
    content = data.get("content", []) if isinstance(data, dict) else []
    for c in content:
        if "text" in c:
            return c["text"], ""
    return "", "mmx returned no text block"


def call_dgemma(prompt: str, timeout: int) -> tuple[str, str]:
    """Free fallback: write prompt to a temp file, call dgemma_read.py, parse summary."""
    import tempfile
    script = Path("P:/.agents/scripts/models/dgemma_read.py")
    if not script.exists():
        return "", "dgemma script not found"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(prompt)
        tmp = f.name
    try:
        r = subprocess.run(["python", str(script), tmp, "--json"],
                           capture_output=True, text=True, timeout=timeout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return "", "dgemma timeout"
    finally:
        os.unlink(tmp)
    if r.returncode != 0:
        return "", f"dgemma rc={r.returncode}: {r.stderr.strip()[:200]}"
    try:
        return json.loads(r.stdout).get("summary", ""), ""
    except json.JSONDecodeError:
        return "", "dgemma non-JSON output"


def synth_cluster(cluster: dict, members: list[dict], backend: str, model: str | None,
                  per_member_chars: int, max_members: int) -> tuple[dict | None, str]:
    """Synthesize one cluster. Returns (parsed_concept_record, error)."""
    if not members:
        return None, "no transcript members"
    context = build_context(members, per_member_chars, max_members)
    prompt = SYNTH_PROMPT.format(hint=cluster.get("name", ""), n=len(members), context=context)

    text, err = "", ""
    if backend == "mmx":
        text, err = call_mmx(prompt, model, timeout=180)
        if not text:
            print(f"    mmx failed ({err}); trying dgemma fallback", file=sys.stderr)
            text, err = call_dgemma(prompt, timeout=180)
    elif backend == "dgemma":
        text, err = call_dgemma(prompt, timeout=180)
    else:
        return None, f"unknown backend {backend}"

    if not text:
        return None, err

    rec = extract_json(text)
    if rec is None:
        return None, f"could not parse JSON from LLM output (len {len(text)})"
    return rec, ""


def extract_json(text: str) -> dict | None:
    """Extract a JSON object from LLM output, tolerating markdown fences + preamble."""
    # Strip ```json ... ``` fences
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    # Find the first {...} block
    start = candidate.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(candidate)):
        if candidate[i] == "{":
            depth += 1
        elif candidate[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(candidate[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


# --- record shaping ------------------------------------------------------

def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower()).strip()
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:60]


def shape_record(parsed: dict, cluster: dict, members: list[dict],
                 notebook_id: str, notebook_title: str) -> dict:
    """Merge the LLM output with provenance into a write_pages-compatible record."""
    title = parsed.get("title") or cluster.get("name") or f"subtopic-{cluster.get('cluster_id')}"
    citations = []
    title_to_sid = {m["title"]: m["source_id"] for m in members if m.get("title")}
    for cit in parsed.get("citations", []):
        stitle = cit.get("source_title", "")
        sid = title_to_sid.get(stitle, "")
        citations.append({
            "claim": cit.get("claim", ""),
            "source_id": sid,
            "source_title": stitle,
            "cited_text": cit.get("cited_text", "")[:600],
        })
    member_sources = [{"source_id": m["source_id"], "source_title": m["title"], "url": m["url"]}
                      for m in members]
    return {
        "title": title,
        "slug": slugify(title),
        "notebook_id": notebook_id,
        "notebook_title": notebook_title,
        "definition": parsed.get("definition", ""),
        "details": parsed.get("details", []),
        "values": parsed.get("values", []),
        "related": parsed.get("related", []),
        "citations": citations,
        "source_mode": "transcript-cluster",
        "cluster_id": cluster.get("cluster_id"),
        "cluster_name": cluster.get("name", ""),
        "member_sources": member_sources,
        "member_count": len(members),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subtopics", type=Path, required=True)
    ap.add_argument("--transcripts-dir", type=Path, required=True)
    ap.add_argument("--notebook", default="")
    ap.add_argument("--notebook-title", default="")
    ap.add_argument("--backend", choices=["mmx", "dgemma"], default="mmx")
    ap.add_argument("--model", default=None, help="override model id for mmx backend")
    ap.add_argument("--per-member-chars", type=int, default=1200)
    ap.add_argument("--max-members", type=int, default=20)
    ap.add_argument("--limit", type=int, default=None, help="synthesize only first N clusters (testing)")
    ap.add_argument("-o", "--output", type=Path, default=Path("concepts.json"))
    args = ap.parse_args()

    data = json.loads(args.subtopics.read_text(encoding="utf-8"))
    clusters = data.get("clusters", data if isinstance(data, list) else [])
    if args.limit:
        clusters = clusters[:args.limit]
    print(f"Synthesizing {len(clusters)} clusters via backend={args.backend}", file=sys.stderr)

    records: list[dict] = []
    failed: list[dict] = []
    for c in clusters:
        cid = c.get("cluster_id")
        name = c.get("name", "")
        members = gather_members(c, args.transcripts_dir)
        print(f"[{cid}] {name} ({len(members)} transcripts)...", file=sys.stderr)
        parsed, err = synth_cluster(c, members, args.backend, args.model,
                                    args.per_member_chars, args.max_members)
        if parsed is None:
            print(f"    FAIL: {err}", file=sys.stderr)
            failed.append({"cluster_id": cid, "name": name, "error": err})
            continue
        rec = shape_record(parsed, c, members, args.notebook, args.notebook_title)
        records.append(rec)
        print(f"    OK: {rec['title']} ({len(rec.get('details', []))} details, {len(rec['citations'])} citations)",
              file=sys.stderr)
        time.sleep(1.0)  # gentle pacing between LLM calls

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSynthesized {len(records)} concepts, {len(failed)} failed", file=sys.stderr)
    print(f"Output: {args.output}", file=sys.stderr)
    return 0 if not failed else 5


if __name__ == "__main__":
    sys.exit(main())
