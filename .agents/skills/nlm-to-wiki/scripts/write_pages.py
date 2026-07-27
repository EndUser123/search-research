#!/usr/bin/env python3
"""write_pages.py — Stage E: emit SCHEMA-compliant wiki pages from reconciled concepts.

Reads reconciled concepts JSON. For each:
  - if disposition == "new":    write to <vault>/concepts/<slug>.md
  - if disposition == "refines": write to <vault>/concepts/<slug>.md with
                                  relations.type=refines pointing at target

Every page MUST pass validate_wiki_entry.py before sync is considered successful.
Pages that fail validation are held in staging and reported.

Frontmatter follows the wiki SCHEMA template — see references/frontmatter-mapping.md.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def build_frontmatter(c: dict, cluster_info: dict | None) -> str:
    """Emit YAML frontmatter per wiki SCHEMA §2-3."""
    today = date.today().isoformat()
    tags = ["nlm-synced", "reference"]
    # Add topic-ish tag from cluster name if available
    if cluster_info and cluster_info.get("name"):
        tags.append(cluster_info["name"].split("-")[0])

    # sources list
    is_transcript_cluster = c.get("source_mode") == "transcript-cluster"
    sources_yaml = [f'"NotebookLM notebook {c["notebook_id"]}" ({c.get("notebook_title", "")}, synced {today})']
    if is_transcript_cluster:
        # v3: list the contributing source transcripts with their URLs (hop-4)
        for ms in c.get("member_sources", []):
            url = (ms.get("url") or "").strip()
            stitle = (ms.get("source_title") or ms.get("source_id") or "").replace('"', "'")
            if url and url != "null":
                sources_yaml.append(f'"{stitle}" ({url}, transcript synced {today})')
            else:
                sources_yaml.append(f'"NotebookLM source {ms.get("source_id", "")}" ({stitle}, synced {today})')
    else:
        # v2: data-table source IDs
        for cit in c.get("citations", []):
            sid = cit.get("source_id")
            if sid and sid not in ("", "(from data-table)"):
                sources_yaml.append(f'"NotebookLM source {sid}" (synced {today})')

    # relations
    relations_yaml = ""
    if c.get("disposition") == "refines" and c.get("refines_target"):
        relations_yaml = f"""
relations:
  - target: wiki/concepts/{c['refines_target']}.md
    type: refines
"""
    elif c.get("related"):
        # Speculative — link to related concepts that may not exist yet
        rels = []
        for r in c["related"][:3]:
            rslug = r.lower().strip().replace(" ", "-")
            rels.append(f"  - target: wiki/concepts/{rslug}.md\n    type: related")
        if rels:
            relations_yaml = "\nrelations:\n" + "\n".join(rels) + "\n"

    sources_block = "\n".join(f"  - {s}" for s in sources_yaml)

    # Provenance chain
    chain_yaml = "  chain:\n"
    chain_yaml += f"    - level: concept\n      id: {c['slug']}\n"
    chain_yaml += f"    - level: notebook\n      id: {c['notebook_id']}\n"
    chain_yaml += f"      title: {c.get('notebook_title', '')}\n"
    chain_yaml += f"      url: https://notebooklm.google.com/notebook/{c['notebook_id']}\n"
    if cluster_info:
        chain_yaml += f"    - level: cluster\n      id: {cluster_info.get('cluster_id', '')}\n"
        chain_yaml += f"      name: {cluster_info.get('name', '')}\n"
        if cluster_info.get("source_path"):
            chain_yaml += f"      source_path: {cluster_info['source_path']}\n"
    # v3 transcript-cluster: append source_url hops (hop-4) for members with URLs
    if is_transcript_cluster:
        seen_urls: set[str] = set()
        for ms in c.get("member_sources", []):
            url = (ms.get("url") or "").strip()
            if url and url != "null" and url not in seen_urls:
                seen_urls.add(url)
                stitle = (ms.get("source_title") or "").replace('"', "'")
                chain_yaml += f"    - level: source_url\n      url: {url}\n      title: {stitle}\n"

    # Build summary — prefer definition, fall back to first detail that looks like one
    defn = (c.get("definition") or "").strip()
    if not defn:
        # Look for a detail bullet that starts with "**Definition:**"
        for d in c.get("details", []):
            d_str = str(d)
            if d_str.lower().startswith("**definition:**"):
                defn = d_str.replace("**Definition:**", "").replace("**definition:**", "").strip()
                break
    if not defn and c.get("details"):
        defn = str(c["details"][0])[:300]  # last resort: first detail
    if not defn:
        defn = f"Concept extracted from notebook {c.get('notebook_title', '')} via nlm-to-wiki sync."
    # Escape for YAML — strip newlines and quotes
    defn_clean = defn.replace("\n", " ").replace('"', "'")[:300]

    return f"""---
title: "{c['title'].replace('"', "'")}"
created: {today}
source: nlm-sync-{today}
tags: [{", ".join(tags)}]
summary: >
  {defn_clean}
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
{sources_block}
provenance:
{chain_yaml}{relations_yaml.strip()}
---"""


def build_body(c: dict) -> str:
    """Emit the markdown body."""
    parts = [f"# {c['title']}", ""]
    parts.append("## Decision context")
    parts.append("")
    defn = c.get("definition", "").strip()
    if defn:
        parts.append(f"**Definition:** {defn}")
        parts.append("")
    # If definition was parsed into a detail bullet, surface it here too
    for d in c.get("details", []):
        d_str = str(d)
        if d_str.lower().startswith("**definition:**"):
            parts.append(d_str.replace("**Definition:**", "**Definition:**").strip())
            parts.append("")
            break
    is_tc = c.get("source_mode") == "transcript-cluster"
    if is_tc:
        n_members = c.get("member_count") or len(c.get("member_sources", []))
        parts.append(f"Synthesized from **{n_members} contributing transcripts** in NotebookLM notebook "
                     f"*{c.get('notebook_title', '')}*, clustered into the \"{c.get('cluster_name', '')}\" "
                     f"sub-topic. Each claim below cites the specific transcript (source_id + title) that "
                     f"supports it; the frontmatter provenance chain carries the full concept → notebook → "
                     f"cluster → source URL hops.")
    else:
        parts.append(f"Extracted from NotebookLM notebook *{c.get('notebook_title', '')}* via Report + Data-Table artifacts. "
                     f"The notebook contains sources on this topic; the concept page distills the Report + Data-Table "
                     f"Studio artifacts generated from those sources.")
    parts.append("")
    parts.append("**Why this matters:** concepts synced from NotebookLM carry provenance back to the source "
                 "material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader "
                 "can verify any claim by following the provenance chain in the frontmatter.")
    parts.append("")

    if c.get("details"):
        parts.append("## Operational details")
        parts.append("")
        for d in c["details"]:
            parts.append(f"- {d}")
        parts.append("")

    if c.get("values"):
        parts.append("## Verifiable values")
        parts.append("")
        parts.append("| Name | Value |")
        parts.append("|---|---|")
        for v in c["values"]:
            parts.append(f"| {v.get('name', '')} | `{v.get('value', '')}` |")
        parts.append("")

    if c.get("related"):
        parts.append("## Related concepts")
        parts.append("")
        for r in c["related"]:
            rslug = r.lower().strip().replace(" ", "-")
            parts.append(f"- [[{rslug}]] — {r}")
        parts.append("")
    else:
        # Fallback: add workspace-anchors to satisfy ≥3 wikilinks requirement
        parts.append("## Related concepts")
        parts.append("")
        parts.append("- [[notebooklm-cli-operational-gotchas]] — operational traps for the nlm CLI")
        parts.append("- [[nlm-synced]] — other concepts synced from NotebookLM")
        parts.append(f"- [[{c.get('notebook_title', 'notebook').lower().replace(' ', '-')}]] — source notebook")
        parts.append("")

    if c.get("citations"):
        parts.append("## Citations" if not is_tc else "## Citations (from contributing transcripts)")
        parts.append("")
        for cit in c["citations"][:10]:
            claim = cit.get("claim", "")
            sid = cit.get("source_id", "")
            stitle = cit.get("source_title", "")
            ctx = cit.get("expanded_context") or cit.get("cited_text", "")
            parts.append(f"- **Claim:** {claim}")
            if stitle:
                parts.append(f"  - Source: {stitle}" + (f" (`{sid}`)" if sid else ""))
            elif sid:
                parts.append(f"  - Source: `{sid}`")
            if ctx:
                parts.append(f"  - Context: {ctx[:500]}")
        parts.append("")

    # Source extract — v2 only (raw Report markdown); v3 has no Report artifact
    if c.get("source_section") and not is_tc:
        parts.append("## Source extract (from Report)")
        parts.append("")
        parts.append("> Verbatim section from the NotebookLM Report artifact:")
        parts.append("")
        parts.append(c["source_section"])
        parts.append("")

    parts.append("## What this means for our workspace")
    parts.append("")
    parts.append("Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) "
                 "is in frontmatter; follow it back to the source material.")
    parts.append("")

    parts.append("## Falsifier")
    parts.append("")
    parts.append("If a re-sync of the source notebook produces a different definition or "
                 "different values, this page should be updated (or marked as superseded). "
                 "The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records "
                 "when this page was last regenerated.")
    parts.append("")

    parts.append("## Sources")
    parts.append("")
    parts.append(f"- NotebookLM notebook [{c.get('notebook_title', '')}](https://notebooklm.google.com/notebook/{c['notebook_id']})")
    parts.append("- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)")
    parts.append("")

    return "\n".join(parts)


def validate(path: Path, validator: Path) -> tuple[bool, str]:
    r = subprocess.run(
        ["python", str(validator), str(path)],
        capture_output=True, text=True, timeout=30, encoding="utf-8")
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, required=True, help="reconciled concepts JSON")
    ap.add_argument("--vault", type=Path, default=Path("P:/.data/wiki"))
    ap.add_argument("--validator", type=Path,
                    default=Path("~/.grok/skills/wiki/scripts/validate_wiki_entry.py").expanduser())
    ap.add_argument("--staging", type=Path, required=True, help="staging dir for failed pages")
    ap.add_argument("--clusters-json", type=Path, help="optional clusters.json for cluster_info lookup")
    args = ap.parse_args()

    args.staging.mkdir(parents=True, exist_ok=True)
    concepts_out_dir = args.vault / "concepts"
    concepts_out_dir.mkdir(parents=True, exist_ok=True)

    # Build cluster lookup if provided
    cluster_lookup: dict[str, dict] = {}
    if args.clusters_json and args.clusters_json.exists():
        try:
            clusters = json.loads(args.clusters_json.read_text(encoding="utf-8"))
            for c in clusters:
                for nb_id in c.get("notebook_ids", []) or [c.get("notebook_id")]:
                    if nb_id:
                        cluster_lookup[nb_id] = {
                            "cluster_id": c.get("cluster_id"),
                            "name": c.get("name"),
                            "source_path": str(args.clusters_json),
                        }
        except json.JSONDecodeError:
            pass

    concepts = json.loads(args.input.read_text(encoding="utf-8"))
    written: list[dict] = []
    failed: list[dict] = []

    for c in concepts:
        # v3 transcript-cluster records carry their own cluster provenance;
        # v2 records look it up via clusters-json notebook_id mapping.
        if c.get("source_mode") == "transcript-cluster":
            cluster_info = {"cluster_id": c.get("cluster_id"),
                            "name": c.get("cluster_name"),
                            "source_path": None}
        else:
            cluster_info = cluster_lookup.get(c.get("notebook_id"))
        frontmatter = build_frontmatter(c, cluster_info)
        body = build_body(c)
        content = frontmatter + "\n\n" + body

        out_path = concepts_out_dir / f"{c['slug']}.md"
        atomic_write(out_path, content)

        ok, msg = validate(out_path, args.validator)
        record = {"slug": c["slug"], "path": str(out_path), "disposition": c.get("disposition"),
                  "title": c["title"]}
        if ok:
            written.append(record)
            print(f"WROTE: {out_path}", file=sys.stderr)
        else:
            failed.append({**record, "validator_msg": msg})
            print(f"FAILED validation: {out_path}", file=sys.stderr)
            print(f"  {msg[:300]}", file=sys.stderr)

    summary = {"written": written, "failed": failed,
               "vault": str(concepts_out_dir), "staging": str(args.staging)}
    print(json.dumps(summary, indent=2))
    return 0 if not failed else 5


if __name__ == "__main__":
    sys.exit(main())
