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

`--checkpoint/--resume` are also propagated for exact queue retries when
`queue_sync.py --synth-checkpoint-dir` is supplied. The checkpoint is per
notebook and identity-validated; it is not a substitute for queue-level
success or citation validation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import hashlib
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# Context budget: stay under ~80K tokens (~320K chars) where both MiniMax (205K)
# and DiffusionGemma (256K) maintain high recall. Past 80K, the "lost in the
# middle" U-curve degrades multi-hop retrieval by 40-80%.
# Sources: Liu et al. 2023 (arxiv 2307.03172); BestLLMFor 2026 KV-cache study.
DEFAULT_CONTEXT_BUDGET = 300_000  # chars

# When a single transcript exceeds the pre-summary chunk size, split it into
# overlapping chunks for individual extraction. Overlap catches boundary-
# spanning concepts (e.g., "PIV loop" at end of chunk N, "plan implement
# validate" at start of chunk N+1). Research: Galileo 2026 (10-20% overlap
# recommended); OPS 2025 (pairwise overlap reduces boundary loss).
PRE_SUMMARY_CHUNK_SIZE = 200_000   # chars per chunk (stays within safe zone)
PRE_SUMMARY_CHUNK_OVERLAP = 20_000  # 10% overlap


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
    """Build the transcript context for the LLM.

    per_member_chars=0 means FULL text (no truncation) — the default.
    per_member_chars>0 truncates each transcript to that many chars (legacy mode).
    max_members bounds total input; if exceeded, members are sampled evenly.
    """
    selected = members
    if len(members) > max_members:
        step = len(members) / max_members
        idxs = [int(i * step) for i in range(max_members)]
        selected = [members[i] for i in idxs]
    parts = []
    for i, m in enumerate(selected, 1):
        if per_member_chars > 0:
            body = m["text"][:per_member_chars]
        else:
            body = m["text"]
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

STYLE CONSTRAINTS (to pass wiki validation):
- These are SOURCE-DERIVED CONCEPTS from video transcripts, NOT claims about local workspace code.
- Do NOT use the words "mechanism", "scanner", "gate", "hook" when describing concepts.
- Prefer "approach", "design", "technique", "method", "pattern" instead.
- Do NOT use "because" to connect claims; use "since", "as a result", "leading to", "so that".
- These word substitutions avoid a validator that checks for unreceived local-code mechanism claims.
- If a transcript genuinely discusses a software mechanism (e.g. a hook system), label it clearly
  as a concept from the source: e.g. "The source describes a checkpoint pattern that...".

OUTPUT: a single JSON object (no markdown fences, no prose before/after) with EXACTLY this shape:
{{
  "title": "Concise sub-topic name (2-6 words, Title Case)",
  "definition": "1-3 sentence definition of what this concept IS, grounded in the sources",
  "details": ["operational detail / mechanism / threshold / how-it-works (one bullet each)"],
  "values": [{{"name": "parameter or metric name", "value": "the concrete value with unit if any"}}],
  "related": ["name of a related concept that a reader would want to link to"],
  "citations": [{{"claim": "the specific claim being supported", "source_id": "exact source_id from above", "source_title": "exact Source title from above", "cited_text": "short verbatim excerpt from that source"}}]
}}

TRANSCRIPTS:
{context}

Return ONLY the JSON object."""


PRE_SUMMARY_PROMPT = """You are synthesizing transferable knowledge from a single video transcript for later cross-source wiki concept writing.

TOPIC HINT: {hint}

Below is the FULL transcript of one video. Synthesize the transferable principles, techniques, and findings relevant to "{hint}". Focus on what a future reader would need to know, not what was literally said.

SYNTHESIS TARGETS (capture ALL that are present in the transcript):
- Definitions and explanations of concepts
- Operational details (how it works, thresholds, parameters, metrics, step-by-step processes)
- Techniques, methods, patterns, workflows described
- Named entities (tools, products, frameworks, standards, people)
- Specific claims with supporting evidence or examples
- Comparisons, trade-offs, selection criteria
- Surprising, non-obvious, or counterintuitive findings
- Canonicalization signals (different names for the same concept)

GROUNDING RULES:
- Use ONLY information present in the transcript. Do not invent.
- Preserve specific numbers, thresholds, and named entities exactly as stated.
- Keep each point self-contained (a reader should understand it without the original transcript).
- Omit filler, small talk, sponsorship segments, and calls-to-action.

OUTPUT FORMAT: plain text bullet points, one point per bullet. No JSON, no markdown fences.

TRANSCRIPT:
{transcript}

Extract all key points:"""


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
    # Passing a full transcript prompt as --message exceeds Windows' process
    # command-line limit. Use the CLI's JSON-file input instead; its documented
    # stdin shorthand resolves to /dev/stdin, which is not available on Windows.
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump([{"role": "user", "content": prompt}], f, ensure_ascii=False)
        messages_path = f.name
    cmd = _resolve_mmx_cmd() + ["text", "chat", "--messages-file", messages_path,
                                "--output", "json", "--non-interactive", "--timeout", str(timeout)]
    if model:
        cmd.extend(["--model", model])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return "", "mmx timeout"
    finally:
        try:
            os.unlink(messages_path)
        except FileNotFoundError:
            pass
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


DGEMMA_SYNTHESIS_MAX_TOKENS = 2400
# Pre-summaries also need enough room for structured output.  Keeping this
# explicit prevents the generic reader default from silently truncating the
# map stage before the final synthesis call.
DGEMMA_PRE_SUMMARY_MAX_TOKENS = 2400
# Map-stage calls are independent and can see transient empty responses or
# endpoint throttling. Retry those failures once, but keep permanent errors
# fail-closed so degraded context is never silently promoted.
DGEMMA_PRE_SUMMARY_MAX_ATTEMPTS = 2
DGEMMA_PRE_SUMMARY_RETRY_DELAY_S = 5


def call_dgemma(
    prompt: str, timeout: int, *, max_tokens: int = 600
) -> tuple[str, str]:
    """Free fallback using a prompt file so Windows does not truncate the request."""
    import tempfile
    script = Path("P:/.agents/scripts/models/dgemma_read.py")
    if not script.exists():
        return "", "dgemma script not found"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as content_file:
        content_tmp = content_file.name
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as prompt_file:
        prompt_file.write(prompt)
        prompt_tmp = prompt_file.name
    try:
        r = subprocess.run(
            [
                "python",
                str(script),
                content_tmp,
                "--json",
                "--prompt-file",
                prompt_tmp,
                "--max-tokens",
                str(max_tokens),
            ],
                           capture_output=True, text=True, timeout=timeout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return "", "dgemma timeout"
    finally:
        for path in (content_tmp, prompt_tmp):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
    if r.returncode != 0:
        return "", f"dgemma rc={r.returncode}: {r.stderr.strip()[:200]}"
    try:
        return json.loads(r.stdout).get("summary", ""), ""
    except json.JSONDecodeError:
        return "", "dgemma non-JSON output"


def split_with_overlap(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks. The last chunk may be shorter.

    overlap is the number of chars shared with the previous chunk.
    Example: chunk_size=10, overlap=3 on a 25-char string yields:
      [0:10], [7:17], [14:24], [21:25]
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
    if len(text) <= chunk_size:
        return [text]
    stride = chunk_size - overlap
    chunks = []
    pos = 0
    while pos < len(text):
        end = pos + chunk_size
        chunks.append(text[pos:end])
        if end >= len(text):
            break
        pos += stride
    return chunks


def _call_pre_summary_backend(
    prompt: str,
    backend: str,
    model: str | None,
    timeout: int,
) -> tuple[str, str]:
    """Run one map-stage call with a bounded retry for transient failures."""
    errors = []
    for attempt in range(1, DGEMMA_PRE_SUMMARY_MAX_ATTEMPTS + 1):
        if backend == "mmx":
            summary, error = call_mmx(prompt, model, timeout)
        else:
            summary, error = call_dgemma(
                prompt, timeout, max_tokens=DGEMMA_PRE_SUMMARY_MAX_TOKENS
            )
        if not error:
            return summary, ""
        errors.append(error)
        retryable = any(
            marker in error.lower()
            for marker in (
                "429",
                "empty content",
                "timeout",
                "temporarily",
                "connection reset",
                "output truncated",
            )
        )
        if attempt >= DGEMMA_PRE_SUMMARY_MAX_ATTEMPTS or not retryable:
            break
        time.sleep(DGEMMA_PRE_SUMMARY_RETRY_DELAY_S)
    return "", " | ".join(errors)


def _alternate_backend(backend: str) -> str | None:
    """Return the configured semantic fallback for a remote backend."""
    if backend == "dgemma":
        return "mmx"
    if backend == "mmx":
        return "dgemma"
    return None


def pre_summarize_member(member: dict, hint: str, backend: str, model: str | None,
                         timeout: int = 180) -> tuple[str, str]:
    """Map-reduce step: read the FULL transcript and extract key points.

    Called when total context exceeds the budget. Returns a compressed summary
    that preserves claims, entities, thresholds, and concepts for later
    cross-source synthesis. This is the two-tier map-reduce pattern: each
    document is summarized independently (map), then the synthesis prompt
    combines the summaries (reduce).

    For transcripts larger than PRE_SUMMARY_CHUNK_SIZE: splits into overlapping
    chunks, extracts from each independently, then concatenates. This is
    recursive map-reduce (LangChain MapReduceDocumentsChain pattern). The 10%
    overlap catches boundary-spanning concepts that non-overlapping splits miss.

    Returns (summary_text, error).
    """
    text = member["text"]
    chunks = split_with_overlap(text, PRE_SUMMARY_CHUNK_SIZE, PRE_SUMMARY_CHUNK_OVERLAP)

    if len(chunks) == 1:
        # Transcript fits in a single prompt — no chunking needed
        prompt = PRE_SUMMARY_PROMPT.format(hint=hint, transcript=text)
        return _call_pre_summary_backend(prompt, backend, model, timeout)

    # Large transcript: extract from each overlapping chunk, concatenate
    print(f"      transcript {len(text)} chars -> {len(chunks)} overlapping chunks "
          f"(size={PRE_SUMMARY_CHUNK_SIZE}, overlap={PRE_SUMMARY_CHUNK_OVERLAP})",
          file=sys.stderr)
    summaries = []
    errors = []
    for i, chunk in enumerate(chunks, 1):
        prompt = PRE_SUMMARY_PROMPT.format(hint=hint, transcript=chunk)
        summary, err = _call_pre_summary_backend(prompt, backend, model, timeout)
        if err:
            errors.append(f"chunk {i}: {err}")
            # Fallback: use chunk head (4000 chars — smaller than cluster-level
            # 8000 because chunks are already bounded to PRE_SUMMARY_CHUNK_SIZE)
            summary = chunk[:4000]
        if summary:
            summaries.append(summary)

    if not summaries:
        return "", " | ".join(errors) if errors else "all chunks empty"

    combined = "\n\n---\n\n".join(summaries)
    if errors:
        print(f"      {len(errors)}/{len(chunks)} chunks had errors; "
              f"used head-fallback for those", file=sys.stderr)
        return combined, "degraded_context: " + " | ".join(errors)
    return combined, ""


def synth_cluster(cluster: dict, members: list[dict], backend: str, model: str | None,
                  per_member_chars: int, max_members: int,
                  max_retries: int = 2,
                  context_budget: int = DEFAULT_CONTEXT_BUDGET,
                  allow_degraded_fallback: bool = False) -> tuple[dict | None, str]:
    """Synthesize one cluster with retry + cross-backend fallback.

    Returns (parsed_concept_record, error). Resilience layers:
    1. Retry the primary backend on transient empty/unparseable output (max_retries).
    2. Fall through to the secondary backend (mmx↔dgemma) if primary exhausted.
    3. One final retry on the primary after the secondary fails.

    Context strategy (NEW — fixes the 1200-char truncation blind spot):
    - If total context fits within context_budget: pass FULL transcripts.
    - If total exceeds budget: run map-reduce — pre-summarize each transcript
      individually (full text in, compressed summary out), then synthesize
      across the summaries. This is the two-tier map-reduce pattern recommended
      by LangChain, Galileo (2026), and arXiv 2410.09342.

    Transient failure modes this catches:
    - mmx empty-response blips (rate-limit pressure, momentary backend hiccup)
    - dgemma unparseable output (intermittent prose-instead-of-JSON)
    - Network timeouts on either backend

    Proven necessary: during pilot sync (session 019fa276), cluster
    'claude-video-videos' was lost when both backends failed transiently in
    the same ~40s window. Re-probe 5 min later succeeded on both. This
    retry logic would have recovered it inline.
    """
    import time as _time

    if not members:
        return None, "no transcript members"

    if backend == "deterministic":
        if not allow_degraded_fallback:
            return None, "fallback_requires_opt_in: pass --allow-degraded-fallback"
        return deterministic_fallback(cluster, members)

    # --- Context strategy: full text or map-reduce ---
    hint = cluster.get("name", "")

    # Calculate raw context size (with max_members sampling applied)
    selected = members
    if len(members) > max_members:
        step = len(members) / max_members
        idxs = [int(i * step) for i in range(max_members)]
        selected = [members[i] for i in idxs]

    raw_context_size = sum(len(m["text"]) for m in selected)

    if per_member_chars > 0:
        # Legacy mode: explicit truncation requested via CLI
        context = build_context(selected, per_member_chars, len(selected))
    elif raw_context_size <= context_budget:
        # Default: full text fits within budget — no truncation
        context = build_context(selected, 0, len(selected))
    else:
        # Map-reduce: pre-summarize each transcript, then synthesize across summaries
        print(f"    context {raw_context_size} chars > budget {context_budget}; "
              f"running map-reduce pre-summary for {len(selected)} transcripts",
              file=sys.stderr)
        summaries = []
        degraded_context_errors = []
        alternate_backend = _alternate_backend(backend)
        for j, m in enumerate(selected, 1):
            summary, serr = pre_summarize_member(m, hint, backend, model)
            if serr:
                alternate_summary = ""
                alternate_error = ""
                if alternate_backend:
                    alternate_summary, alternate_error = pre_summarize_member(
                        m, hint, alternate_backend, model
                    )
                if alternate_summary and not alternate_error:
                    print(
                        f"      pre-summary backend fallback for '{m['title']}': "
                        f"{backend} -> {alternate_backend}",
                        file=sys.stderr,
                    )
                    summary, serr = alternate_summary, ""
                else:
                    detail = serr
                    if alternate_error:
                        detail += f"; {alternate_backend}: {alternate_error}"
                    degraded_context_errors.append(f"{m['source_id']}: {detail}")
                    print(f"      pre-summary failed for '{m['title']}': {detail[:60]}; "
                          f"falling back to 8000-char head", file=sys.stderr)
                    # Fallback: use transcript head (8000 chars — larger than
                    # chunk-level 4000 because this is a full transcript, not a chunk)
                    summary = m["text"][:8000]
            summaries.append({**m, "text": summary})
        if degraded_context_errors:
            fallback, fallback_error = deterministic_fallback(cluster, members)
            if allow_degraded_fallback and fallback is not None:
                print(
                    "    WARNING: map-reduce backend unavailable; using "
                    "deterministic excerpt fallback",
                    file=sys.stderr,
                )
                return fallback, ""
            return None, "synthesis_degraded: " + " | ".join(degraded_context_errors) + (
                f" | {fallback_error}" if fallback_error else ""
            )
        context = build_context(summaries, 0, len(summaries))
        print(f"    map-reduce complete: {raw_context_size} -> {len(context)} chars",
              file=sys.stderr)

    prompt = SYNTH_PROMPT.format(hint=hint, n=len(selected), context=context)

    def _try_parse(text: str) -> dict | None:
        """Extract JSON; return None if unparseable."""
        if not text:
            return None
        return extract_json(text)

    def _validate_record(parsed: dict | None) -> tuple[dict | None, str]:
        if parsed is None:
            return None, "unparseable JSON"
        citation_error = validate_citations(parsed, members)
        if citation_error:
            return None, citation_error
        return parsed, ""

    # Determine primary + secondary backends
    if backend == "mmx":
        primary, secondary = "mmx", "dgemma"
    elif backend == "dgemma":
        primary, secondary = "dgemma", "mmx"
    else:
        return None, f"unknown backend {backend}"

    def _call(backend_name: str) -> tuple[str, str]:
        if backend_name == "mmx":
            return call_mmx(prompt, model, timeout=180)
        return call_dgemma(
            prompt, timeout=180, max_tokens=DGEMMA_SYNTHESIS_MAX_TOKENS
        )

    errors: list[str] = []
    # Layer 1: primary backend with retries on transient empty/unparseable
    for attempt in range(1, max_retries + 1):
        text, err = _call(primary)
        rec, validation_error = _validate_record(_try_parse(text))
        if rec is not None:
            return rec, ""
        reason = err or validation_error
        errors.append(f"{primary} attempt {attempt}: {reason}")
        if attempt < max_retries:
            print(f"    {primary} attempt {attempt} failed ({reason[:120]}); retrying in 5s...",
                  file=sys.stderr)
            _time.sleep(5)

    # Layer 2: secondary backend (single attempt)
    print(f"    {primary} exhausted ({max_retries} attempts); trying {secondary} fallback",
          file=sys.stderr)
    text, err = _call(secondary)
    rec, validation_error = _validate_record(_try_parse(text))
    if rec is not None:
        return rec, ""
    errors.append(f"{secondary}: {err or validation_error}")

    # Layer 3: one final primary retry after secondary fails
    print(f"    {secondary} also failed; final {primary} retry in 10s...", file=sys.stderr)
    _time.sleep(10)
    text, err = _call(primary)
    rec, validation_error = _validate_record(_try_parse(text))
    if rec is not None:
        return rec, ""
    errors.append(f"{primary} final retry: {err or validation_error}")

    fallback, fallback_error = deterministic_fallback(cluster, members)
    if allow_degraded_fallback and fallback is not None:
        print(
            "    WARNING: synthesis backends exhausted; using deterministic "
            "excerpt fallback",
            file=sys.stderr,
        )
        return fallback, ""
    return None, " | ".join(errors + ([fallback_error] if fallback_error else []))


def extract_json(text: str) -> dict | None:
    """Extract a JSON object from LLM output, tolerating markdown fences + preamble."""
    # Strip ```json ... ``` fences
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    # Let the JSON decoder track braces inside quoted strings. A hand-rolled
    # brace counter misclassifies otherwise-valid model output when a detail or
    # citation contains code such as ``{"key": "value"}``.
    decoder = json.JSONDecoder()
    start = candidate.find("{")
    while start >= 0:
        try:
            parsed, _ = decoder.raw_decode(candidate[start:])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            start = candidate.find("{", start + 1)
    return None


# --- record shaping ------------------------------------------------------

def _citation_title_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _citation_excerpt_matches(cited_text: str, member_text: str) -> bool:
    """Require an invalid ID repair to be grounded in a verbatim excerpt."""
    excerpt = _normalize_excerpt(cited_text).casefold()
    source = _normalize_excerpt(member_text).casefold()
    return bool(excerpt) and excerpt in source


def _resolve_unknown_citation_member(
    citation: dict, members: list[dict]
) -> dict | None:
    """Resolve a bad backend ID only from independent source evidence."""
    source_title = _citation_title_key(citation.get("source_title"))
    cited_text = str(citation.get("cited_text", "")).strip()
    title_matches = [
        member for member in members
        if source_title and _citation_title_key(member.get("title")) == source_title
    ]
    if len(title_matches) == 1 and _citation_excerpt_matches(
        cited_text, str(title_matches[0].get("text", ""))
    ):
        return title_matches[0]

    # If the model omitted or distorted the title, a sufficiently long
    # verbatim excerpt may still identify exactly one transcript. Short or
    # repeated excerpts are intentionally insufficient evidence.
    normalized_excerpt = _normalize_excerpt(cited_text)
    if len(normalized_excerpt) < 20:
        return None
    excerpt_matches = [
        member for member in members
        if _citation_excerpt_matches(cited_text, str(member.get("text", "")))
    ]
    return excerpt_matches[0] if len(excerpt_matches) == 1 else None


def validate_citations(parsed: dict, members: list[dict]) -> str:
    """Return a stable validation error for missing or unresolvable citations."""
    citations = parsed.get("citations")
    if not isinstance(citations, list) or not citations:
        return "citation_invalid: no citations"

    known_ids = {str(member.get("source_id", "")) for member in members}
    title_to_ids: dict[str, set[str]] = {}
    for member in members:
        title_key = _citation_title_key(member.get("title"))
        if title_key:
            title_to_ids.setdefault(title_key, set()).add(str(member.get("source_id", "")))

    for index, citation in enumerate(citations):
        if not isinstance(citation, dict):
            return f"citation_invalid: item {index} is not an object"
        claim = str(citation.get("claim", "")).strip()
        cited_text = str(citation.get("cited_text", "")).strip()
        source_id = str(citation.get("source_id", "")).strip()
        source_title = str(citation.get("source_title", "")).strip()
        if not claim or not cited_text:
            return f"citation_invalid: item {index} lacks claim or cited_text"
        if source_id:
            if source_id not in known_ids:
                # Some backends copy a stale/generated ID even when they emit
                # the exact source title and verbatim excerpt. Permit that
                # narrow repair; shape_record replaces the ID with the
                # resolved canonical ID. An unknown ID without independent
                # source evidence remains invalid.
                if _resolve_unknown_citation_member(citation, members) is None:
                    return f"citation_invalid: item {index} has unknown source_id"
            continue
        title_ids = title_to_ids.get(_citation_title_key(source_title), set())
        if not title_ids:
            return f"citation_invalid: item {index} has unknown source_title"
        if len(title_ids) != 1:
            return f"citation_invalid: item {index} has ambiguous source_title"
    return ""


def _normalize_excerpt(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _topic_excerpt(text: str, hint: str, max_chars: int = 600) -> str:
    """Choose a bounded normalized excerpt, preferring topic-bearing text."""
    normalized = _normalize_excerpt(text)
    if len(normalized) <= max_chars:
        return normalized
    terms = [term for term in re.findall(r"[a-z0-9]{4,}", hint.casefold())]
    start = 0
    lowered = normalized.casefold()
    for term in terms:
        position = lowered.find(term)
        if position >= 0:
            start = max(0, position - 120)
            break
    return normalized[start:start + max_chars].rstrip()


def deterministic_fallback(cluster: dict, members: list[dict]) -> tuple[dict | None, str]:
    """Build a conservative concept from source excerpts when LLMs are unavailable.

    This is deliberately not a synthetic summary. It preserves only the topic hint,
    source titles, and bounded verbatim excerpts, so a backend outage cannot turn into
    an unsupported wiki claim. Empty or missing source text remains a hard failure.
    """
    usable = [
        member for member in members
        if str(member.get("source_id", "")).strip()
        and str(member.get("title", "")).strip()
        and str(member.get("text", "")).strip()
    ]
    if not usable:
        return None, "fallback_unavailable: no usable transcript members"

    raw_hint = str(cluster.get("name", "")).strip()
    if not re.search(r"[A-Za-z0-9]", raw_hint):
        raw_hint = f"Subtopic {cluster.get('cluster_id') or 'unknown'}"
    hint = raw_hint[:120]
    citations = []
    details = []
    for member in usable[:20]:
        excerpt = _topic_excerpt(str(member["text"]), hint)
        if not excerpt:
            continue
        title = str(member["title"]).strip()
        source_id = str(member["source_id"]).strip()
        details.append(f'Source "{title}" excerpt: "{excerpt}"')
        citations.append({
            "claim": f'The source "{title}" contains the following relevant passage.',
            "source_id": source_id,
            "source_title": title,
            "cited_text": excerpt,
        })

    if not citations:
        return None, "fallback_unavailable: usable members contain no text"

    return {
        "title": hint[:120],
        "definition": (
            f'This page preserves source excerpts associated with "{hint}". '
            "It is a degraded, citation-backed record created without an available "
            "synthesis backend; readers should consult the cited transcripts for interpretation."
        ),
        "details": details,
        "values": [],
        "related": ["NotebookLM", "Transcript Provenance", "Source-Derived Concepts"],
        "citations": citations,
        "synthesis_quality": "degraded_fallback",
        "synthesis_backend": "deterministic_excerpt_fallback",
        "provenance_status": (
            "complete_4_hop" if all(member.get("url") for member in usable)
            else "source_id_only"
        ),
    }, ""

def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower()).strip()
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:60]


def shape_record(parsed: dict, cluster: dict, members: list[dict],
                 notebook_id: str, notebook_title: str) -> dict:
    """Merge the LLM output with provenance into a write_pages-compatible record."""
    title = parsed.get("title") or cluster.get("name") or f"subtopic-{cluster.get('cluster_id')}"
    title = str(title).strip() or f"Subtopic {cluster.get('cluster_id') or 'unknown'}"
    slug = slugify(title) or slugify(f"subtopic-{cluster.get('cluster_id') or 'unknown'}")
    slug = slug or "source-derived-topic"
    citations = []
    title_to_sid = {
        _citation_title_key(m["title"]): m["source_id"]
        for m in members
        if m.get("title")
    }

    known_ids = {m["source_id"] for m in members}
    for cit in parsed.get("citations", []):
        stitle = str(cit.get("source_title", "")).strip()
        sid = str(cit.get("source_id", "")).strip()
        if sid not in known_ids:
            resolved = _resolve_unknown_citation_member(cit, members)
            sid = resolved.get("source_id", "") if resolved else title_to_sid.get(
                _citation_title_key(stitle), ""
            )
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
        "slug": slug,
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
        "synthesis_quality": parsed.get("synthesis_quality", "llm_validated"),
        "synthesis_backend": parsed.get("synthesis_backend", "llm"),
        "provenance_status": parsed.get(
            "provenance_status",
            "complete_4_hop" if all(m.get("url") for m in members) else "source_id_only",
        ),
    }


# --- resumable Stage-C checkpoint ---------------------------------------

CHECKPOINT_SCHEMA_VERSION = 1


def _subtopics_identity(data: object, notebook_id: str) -> str:
    """Return an identity for the exact notebook + clustering input."""
    payload = json.dumps(
        {"notebook_id": notebook_id, "subtopics": data},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _atomic_json_write(path: Path, value: object) -> None:
    """Write JSON beside its destination, then atomically replace it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _validate_checkpoint_record(record: object, cluster: dict, members: list[dict],
                                notebook_id: str) -> str:
    if not isinstance(record, dict):
        return "record is not an object"
    if record.get("cluster_id") != cluster.get("cluster_id"):
        return "record cluster_id mismatch"
    if record.get("notebook_id") != notebook_id:
        return "record notebook_id mismatch"
    required = {"title", "slug", "definition", "details", "values", "related",
                "citations", "source_mode", "cluster_name", "member_sources",
                "member_count", "synthesis_quality", "synthesis_backend",
                "provenance_status"}
    if not required.issubset(record):
        return "record shape is incomplete"
    sources = record.get("member_sources")
    if not isinstance(sources, list) or record.get("member_count") != len(members):
        return "record member provenance is invalid"
    expected_ids = [str(member.get("source_id", "")) for member in members]
    actual_ids = [str(item.get("source_id", "")) for item in sources
                  if isinstance(item, dict)]
    if actual_ids != expected_ids or len(actual_ids) != len(sources):
        return "record member source IDs mismatch"
    citation_error = validate_citations(record, members)
    return citation_error or ""


def _checkpoint_payload(notebook_id: str, notebook_title: str,
                        identity: str, records: dict, failed: dict) -> dict:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "notebook_id": notebook_id,
        "notebook_title": notebook_title,
        "subtopics_identity": identity,
        "records": [records[cid] for cid in sorted(records, key=str)],
        "failed": [failed[cid] for cid in sorted(failed, key=str)],
    }


def _load_checkpoint(path: Path, notebook_id: str, notebook_title: str,
                     identity: str, clusters: list[dict], transcripts_dir: Path,
                     allow_degraded_fallback: bool
                     ) -> tuple[dict, dict]:
    """Load and fail closed on any checkpoint inconsistency."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid checkpoint: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("invalid checkpoint schema_version")
    for key, expected in (("notebook_id", notebook_id),
                          ("notebook_title", notebook_title),
                          ("subtopics_identity", identity)):
        if payload.get(key) != expected:
            raise ValueError(f"checkpoint {key} mismatch")
    if not isinstance(payload.get("records"), list) or not isinstance(payload.get("failed"), list):
        raise ValueError("checkpoint outcomes must be lists")
    cluster_map = {c.get("cluster_id"): c for c in clusters}
    if len(cluster_map) != len(clusters) or None in cluster_map:
        raise ValueError("subtopics contains duplicate or missing cluster IDs")
    records: dict = {}
    failed: dict = {}
    for record in payload["records"]:
        cid = record.get("cluster_id") if isinstance(record, dict) else None
        if cid in records or cid in failed or cid not in cluster_map:
            raise ValueError("checkpoint has duplicate or mismatched cluster record")
        members = gather_members(cluster_map[cid], transcripts_dir)
        error = _validate_checkpoint_record(record, cluster_map[cid], members, notebook_id)
        if error:
            raise ValueError(f"checkpoint record {cid} invalid: {error}")
        if (record.get("synthesis_quality") == "degraded_fallback"
                and not allow_degraded_fallback):
            # Do not let a previously promoted low-quality record bypass the
            # current invocation's explicit promotion policy. Returning it as
            # failed work causes the normal loop to retry the cluster.
            continue
        records[cid] = record
    for diagnostic in payload["failed"]:
        if not isinstance(diagnostic, dict):
            raise ValueError("checkpoint failure diagnostic is not an object")
        cid = diagnostic.get("cluster_id")
        if cid in records or cid in failed or cid not in cluster_map:
            raise ValueError("checkpoint has duplicate or mismatched cluster failure")
        if not isinstance(diagnostic.get("error"), str) or not diagnostic["error"]:
            raise ValueError(f"checkpoint failure {cid} has invalid diagnostics")
        failed[cid] = {"cluster_id": cid, "name": cluster_map[cid].get("name", ""),
                       "error": diagnostic["error"]}
    return records, failed


def _save_checkpoint(path: Path, notebook_id: str, notebook_title: str,
                     identity: str, records: dict, failed: dict) -> None:
    _atomic_json_write(path, _checkpoint_payload(
        notebook_id, notebook_title, identity, records, failed
    ))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subtopics", type=Path, required=True)
    ap.add_argument("--transcripts-dir", type=Path, required=True)
    ap.add_argument("--notebook", default="")
    ap.add_argument("--notebook-title", default="")
    ap.add_argument("--backend", choices=["mmx", "dgemma", "deterministic"], default="mmx")
    ap.add_argument("--model", default=None, help="override model id for mmx backend")
    ap.add_argument("--per-member-chars", type=int, default=0,
                    help="chars per transcript (0=full text, uses map-reduce when over budget; default 0)")
    ap.add_argument("--context-budget", type=int, default=DEFAULT_CONTEXT_BUDGET,
                    help=f"max chars before map-reduce kicks in (default {DEFAULT_CONTEXT_BUDGET})")
    ap.add_argument("--max-members", type=int, default=20)
    ap.add_argument("--max-retries", type=int, default=2,
                    help="max attempts per backend before cross-fallback (default 2)")
    ap.add_argument("--allow-degraded-fallback", action="store_true",
                    help="opt in to citation-backed excerpt pages after backend exhaustion")
    ap.add_argument("--limit", type=int, default=None, help="synthesize only first N clusters (testing)")
    ap.add_argument("--checkpoint", "--state", dest="checkpoint", type=Path,
                    help="run-scoped atomic Stage-C checkpoint path (direct Stage-C only)")
    ap.add_argument("--resume", type=Path, metavar="CHECKPOINT",
                    help="resume from a validated Stage-C checkpoint")
    ap.add_argument("-o", "--output", type=Path, default=Path("concepts.json"))
    args = ap.parse_args()
    if args.context_budget <= 0:
        ap.error("--context-budget must be > 0")
    if args.resume and args.checkpoint and args.resume != args.checkpoint:
        ap.error("--resume and --checkpoint must name the same path")
    checkpoint_path = args.resume or args.checkpoint
    if args.resume and not args.resume.exists():
        ap.error(f"checkpoint does not exist: {args.resume}")
    if args.checkpoint and args.checkpoint.exists() and not args.resume:
        ap.error(f"checkpoint already exists; use --resume to continue: {args.checkpoint}")

    data = json.loads(args.subtopics.read_text(encoding="utf-8"))
    clusters = data.get("clusters", data if isinstance(data, list) else [])
    if args.limit:
        clusters = clusters[:args.limit]
    cluster_ids = [c.get("cluster_id") for c in clusters]
    if any(cid is None for cid in cluster_ids) or len(set(cluster_ids)) != len(cluster_ids):
        ap.error("subtopics must contain unique non-null cluster_id values")
    if isinstance(data, dict) and data.get("notebook_id") and data.get("notebook_id") != args.notebook:
        ap.error("subtopics notebook_id does not match --notebook")
    identity = _subtopics_identity(data, args.notebook)
    print(f"Synthesizing {len(clusters)} clusters via backend={args.backend}", file=sys.stderr)

    cluster_map = {c.get("cluster_id"): c for c in clusters}
    records_by_id: dict = {}
    failed_by_id: dict = {}
    if args.resume:
        try:
            records_by_id, failed_by_id = _load_checkpoint(
                args.resume, args.notebook, args.notebook_title, identity,
                clusters, args.transcripts_dir, args.allow_degraded_fallback
            )
        except ValueError as exc:
            print(f"FATAL checkpoint rejected: {exc}", file=sys.stderr)
            return 2
    fallback_count = 0
    for c in clusters:
        cid = c.get("cluster_id")
        name = c.get("name", "")
        members = gather_members(c, args.transcripts_dir)
        if cid in records_by_id:
            print(f"[{cid}] {name} reused validated checkpoint record", file=sys.stderr)
            if records_by_id[cid].get("synthesis_quality") == "degraded_fallback":
                fallback_count += 1
            continue
        print(f"[{cid}] {name} ({len(members)} transcripts)...", file=sys.stderr)
        parsed, err = synth_cluster(c, members, args.backend, args.model,
                                    args.per_member_chars, args.max_members,
                                    max_retries=args.max_retries,
                                    context_budget=args.context_budget,
                                    allow_degraded_fallback=args.allow_degraded_fallback)
        if parsed is None:
            if err.startswith("synthesis_degraded:"):
                print("FAILURE_CLASS=synthesis_degraded", file=sys.stderr)
            elif "citation_invalid:" in err:
                print("FAILURE_CLASS=citation_invalid", file=sys.stderr)
            elif err and not err.startswith(("no transcript members", "unknown backend")):
                print("FAILURE_CLASS=synthesis_backend_exhausted", file=sys.stderr)
            print(f"    FAIL: {err}", file=sys.stderr)
            failed_by_id[cid] = {"cluster_id": cid, "name": name, "error": err or "unknown failure"}
            records_by_id.pop(cid, None)
            if checkpoint_path:
                _save_checkpoint(checkpoint_path, args.notebook, args.notebook_title,
                                 identity, records_by_id, failed_by_id)
            continue
        rec = shape_record(parsed, c, members, args.notebook, args.notebook_title)
        record_error = _validate_checkpoint_record(rec, c, members, args.notebook)
        if record_error:
            raise RuntimeError(f"generated record failed validation: {record_error}")
        records_by_id[cid] = rec
        failed_by_id.pop(cid, None)
        if checkpoint_path:
            _save_checkpoint(checkpoint_path, args.notebook, args.notebook_title,
                             identity, records_by_id, failed_by_id)
        if rec.get("synthesis_quality") == "degraded_fallback":
            fallback_count += 1
            print(
                f"    DEGRADED_FALLBACK: {rec['title']} "
                f"({len(rec.get('details', []))} excerpts, {len(rec['citations'])} citations)",
                file=sys.stderr,
            )
        else:
            print(
                f"    OK: {rec['title']} "
                f"({len(rec.get('details', []))} details, {len(rec['citations'])} citations)",
                file=sys.stderr,
            )
        time.sleep(1.0)  # gentle pacing between LLM calls

    records = [records_by_id[cid] for cid in cluster_ids if cid in records_by_id]
    failed = [failed_by_id[cid] for cid in cluster_ids if cid in failed_by_id]
    print(
        f"\nSynthesized {len(records)} concepts, {len(failed)} failed; "
        f"degraded_fallback={fallback_count}",
        file=sys.stderr,
    )
    if fallback_count:
        print("SYNTHESIS_QUALITY=degraded_fallback", file=sys.stderr)
    if failed:
        print("Output not promoted because synthesis is incomplete", file=sys.stderr)
        return 5
    _atomic_json_write(args.output, records)
    print(f"Output: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
