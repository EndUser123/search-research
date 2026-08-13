#!/usr/bin/env python3
"""Audit manifest gaps and degraded pages outside current ownership.

This is a read-only local-evidence audit. It never calls NotebookLM, changes
the queue, or writes the manifest. A gap is not repaired, and a degraded page
is not deleted or promoted, unless a separate guarded operation has an exact,
unambiguous receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_QUEUE = Path("P:/.data/wiki/_state/nlm-sync/queue.json")
DEFAULT_MANIFEST = Path("P:/.data/wiki/_state/nlm-sync-manifest.json")
DEFAULT_RECEIPT_ROOTS = (Path("P:/.logs/wiki-yt-queue"),)
DEFAULT_TRANSCRIPT_ROOT = Path("P:/.data/wiki/sources/transcripts")
DEFAULT_CONCEPT_ROOT = Path("P:/.data/wiki/concepts")
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".md", ".txt", ".out"}
RECEIPT_SUFFIXES = {".json", ".jsonl", ".log", ".out"}
MAX_SCAN_BYTES = 20 * 1024 * 1024
_FRONTMATTER_FIELD = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*):\s*(?P<value>.*)$")
_NOTEBOOK_REFERENCE = re.compile(
    r"NotebookLM notebook\s+(?P<notebook_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _frontmatter(text: str) -> dict[str, str]:
    """Parse the small scalar subset used by transcript frontmatter."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = _FRONTMATTER_FIELD.match(line)
        if match:
            fields[match.group("name")] = _unquote(match.group("value"))
    return fields


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_with_hash(path: Path) -> tuple[dict, str]:
    """Parse one byte snapshot and return its matching SHA-256."""
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def _record_ids(records) -> list[str]:
    """Return exact non-empty IDs in deterministic order, de-duplicated."""
    return sorted({
        str(record.get("nb_id", "")).strip()
        for record in records or []
        if isinstance(record, dict) and str(record.get("nb_id", "")).strip()
    })


def _queue_state_ids(queue: dict) -> dict[str, list[str]]:
    in_progress = queue.get("in_progress", {}) or {}
    if isinstance(in_progress, dict):
        in_progress = list(in_progress.values())
    return {
        "failed": _record_ids(queue.get("failed", [])),
        "poisoned": _record_ids(queue.get("poisoned", [])),
        "deferred": _record_ids(queue.get("needs_resynthesis", [])),
        "in_progress": _record_ids(in_progress),
    }


def _completed_ids(queue: dict) -> set[str]:
    return {
        str(item.get("nb_id", "")).strip()
        for item in queue.get("completed", [])
        if str(item.get("nb_id", "")).strip()
    }


def _manifest_ids(manifest: dict) -> set[str]:
    return {
        str(nb_id).strip()
        for nb_id in manifest.get("notebooks", {})
        if str(nb_id).strip()
    }


def _manifest_concept_slugs(manifest: dict) -> dict[str, set[str]]:
    """Return the manifest's current page ownership by notebook ID."""
    result: dict[str, set[str]] = {}
    for raw_id, entry in (manifest.get("notebooks", {}) or {}).items():
        notebook_id = str(raw_id).strip()
        if not notebook_id or not isinstance(entry, dict):
            continue
        result[notebook_id] = {
            str(slug).strip()
            for slug in entry.get("concept_slugs", []) or []
            if str(slug).strip()
        }
    return result


def _iter_text_files(roots: tuple[Path, ...]):
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_SCAN_BYTES:
                    continue
            except OSError:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            yield path, text


def _queue_receipts(queue: dict, gaps: set[str]) -> dict[str, list[dict]]:
    receipts = {nb_id: [] for nb_id in gaps}
    for item in queue.get("completed", []):
        nb_id = str(item.get("nb_id", "")).strip()
        if nb_id not in gaps:
            continue
        receipts[nb_id].append({
            "status": str(item.get("status", "")).strip(),
            "title": str(item.get("title", "")).strip(),
            "elapsed_s": item.get("elapsed_s"),
            "completed_at": item.get("completed_at"),
        })
    return receipts


def _transcript_evidence(
    gaps: set[str], root: Path | None,
) -> dict[str, dict]:
    evidence = {
        nb_id: {"paths": [], "source_ids": [], "titles": [], "exported_dates": []}
        for nb_id in gaps
    }
    if root is None:
        return evidence
    for path, text in _iter_text_files((root,)):
        fields = _frontmatter(text[:4000])
        nb_id = fields.get("notebook_id", "").strip()
        if nb_id not in gaps:
            continue
        row = evidence[nb_id]
        row["paths"].append(str(path))
        source_id = fields.get("source_id", "").strip()
        if source_id and source_id not in row["source_ids"]:
            row["source_ids"].append(source_id)
        title = fields.get("title", "").strip()
        if title and title not in row["titles"]:
            row["titles"].append(title)
        exported = fields.get("exported", "").strip()
        if exported and exported not in row["exported_dates"]:
            row["exported_dates"].append(exported)
    return evidence


def _concept_evidence(gaps: set[str], root: Path | None) -> dict[str, list[str]]:
    evidence = {nb_id: [] for nb_id in gaps}
    if root is None:
        return evidence
    patterns = {
        nb_id: re.compile(r"NotebookLM notebook\s+" + re.escape(nb_id) + r"\b", re.I)
        for nb_id in gaps
    }
    for path, text in _iter_text_files((root,)):
        for nb_id, pattern in patterns.items():
            if pattern.search(text):
                evidence[nb_id].append(str(path))
    return evidence


def _file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def _citation_coverage(root: Path | None) -> dict[str, object]:
    """Measure page-level citation evidence without parsing or rewriting pages."""
    pages = 0
    degraded_pages = 0
    cited_pages = 0
    degraded_cited_pages = 0
    page_rows: list[dict[str, object]] = []
    if root is None:
        return {
            "concept_page_count": 0,
            "pages_with_citations": 0,
            "pages_without_citations": 0,
            "citation_coverage_percent": None,
            "degraded_page_count": 0,
            "degraded_pages_with_citations": 0,
            "degraded_citation_coverage_percent": None,
            "pages": page_rows,
        }
    for path, text in _iter_text_files((root,)):
        if path.suffix.lower() != ".md":
            continue
        pages += 1
        fields = _frontmatter(text)
        degraded = "degraded-fallback" in fields.get("tags", "").lower()
        has_citations = bool(
            re.search(r"^## Citations(?:\s|$)", text, re.IGNORECASE | re.MULTILINE)
            and re.search(r"^[-*] \*\*Claim:\*\*", text, re.MULTILINE)
        )
        degraded_pages += int(degraded)
        cited_pages += int(has_citations)
        degraded_cited_pages += int(degraded and has_citations)
        page_rows.append({
            "path": str(path),
            "degraded": degraded,
            "has_citations": has_citations,
        })

    def percent(numerator: int, denominator: int) -> float | None:
        return round(numerator * 100.0 / denominator, 2) if denominator else None

    return {
        "concept_page_count": pages,
        "pages_with_citations": cited_pages,
        "pages_without_citations": pages - cited_pages,
        "citation_coverage_percent": percent(cited_pages, pages),
        "degraded_page_count": degraded_pages,
        "degraded_pages_with_citations": degraded_cited_pages,
        "degraded_citation_coverage_percent": percent(degraded_cited_pages, degraded_pages),
        "pages": page_rows,
    }


def _concept_inventory(root: Path | None) -> dict[str, list[str]]:
    """Index local concept slugs without inferring notebook ownership."""
    inventory: dict[str, list[str]] = {}
    if root is None:
        return inventory
    for path, _text in _iter_text_files((root,)):
        if path.suffix.lower() == ".md":
            inventory.setdefault(path.stem, []).append(str(path))
    return inventory


def _manifest_page_parity(manifest: dict, root: Path | None) -> dict[str, object]:
    """Report page-path parity separately from receipt-backed ownership."""
    manifest_slugs = _manifest_concept_slugs(manifest)
    inventory = _concept_inventory(root)
    missing: list[dict[str, str]] = []
    owners: dict[str, list[str]] = {}
    for notebook_id, slugs in manifest_slugs.items():
        for slug in slugs:
            owners.setdefault(slug, []).append(notebook_id)
            if slug not in inventory:
                missing.append({"notebook_id": notebook_id, "slug": slug})
    duplicate_ownership = {
        slug: sorted(notebook_ids)
        for slug, notebook_ids in owners.items()
        if len(set(notebook_ids)) > 1
    }
    owned_paths = {
        path
        for slug in owners
        for path in inventory.get(slug, [])
    }
    all_paths = [path for paths in inventory.values() for path in paths]
    return {
        "concept_file_count": len(all_paths),
        "manifest_unique_slug_count": len(owners),
        "manifest_referenced_slug_count": sum(len(slugs) for slugs in manifest_slugs.values()),
        "manifest_references_missing_on_disk": missing,
        "duplicate_manifest_slug_ownership": duplicate_ownership,
        "unowned_concept_file_count": len(set(all_paths) - owned_paths),
    }



def _unmanifested_degraded_pages(
    manifest: dict, root: Path | None,
) -> list[dict[str, object]]:
    """Find degraded pages absent from their notebook's current slug list.

    This is intentionally an audit-only signal. It does not infer ownership
    from a filename and never makes a manifest entry eligible for repair.
    """
    if root is None:
        return []
    manifest_slugs = _manifest_concept_slugs(manifest)
    pages: list[dict[str, object]] = []
    for path, text in _iter_text_files((root,)):
        if path.suffix.lower() != ".md":
            continue
        # Concept pages can carry long summaries before the tags field; unlike
        # transcript frontmatter, parse the complete bounded file here so a
        # degraded tag is not missed merely because it appears after 4 KiB.
        fields = _frontmatter(text)
        if "degraded-fallback" not in fields.get("tags", "").lower():
            continue
        notebook_ids = sorted({
            match.group("notebook_id")
            for match in _NOTEBOOK_REFERENCE.finditer(text)
        })
        slug = path.stem
        if not notebook_ids:
            pages.append({
                "path": str(path),
                "slug": slug,
                "notebook_ids": [],
                "status": "degraded_page_notebook_identity_missing",
            })
            continue
        missing_ids = [notebook_id for notebook_id in notebook_ids if notebook_id not in manifest_slugs]
        if missing_ids:
            pages.append({
                "path": str(path),
                "slug": slug,
                "notebook_ids": missing_ids,
                "status": "degraded_page_notebook_missing_from_manifest",
            })
            continue
        missing_slugs = [
            notebook_id
            for notebook_id in notebook_ids
            if slug not in manifest_slugs[notebook_id]
        ]
        if missing_slugs:
            pages.append({
                "path": str(path),
                "slug": slug,
                "notebook_ids": missing_slugs,
                "status": "degraded_page_slug_missing_from_manifest",
            })
    return pages


def _receipt_evidence(gaps: set[str], roots: tuple[Path, ...]) -> dict[str, list[str]]:
    """Find exact-ID receipt files; arbitrary text is not output evidence."""
    hits = {nb_id: [] for nb_id in gaps}
    for path, text in _iter_text_files(roots):
        if path.suffix.lower() not in RECEIPT_SUFFIXES:
            continue
        if any(token in path.name.lower() for token in ("audit", "packet", "handoff")):
            continue
        for nb_id in gaps:
            if nb_id in text:
                hits[nb_id].append(str(path))
    return hits


def build_report(
    queue_path: Path = DEFAULT_QUEUE,
    manifest_path: Path = DEFAULT_MANIFEST,
    evidence_roots: tuple[Path, ...] = DEFAULT_RECEIPT_ROOTS,
    transcript_root: Path | None = DEFAULT_TRANSCRIPT_ROOT,
    concept_root: Path | None = DEFAULT_CONCEPT_ROOT,
) -> dict:
    queue, queue_sha256 = _read_json_with_hash(queue_path)
    manifest, manifest_sha256 = _read_json_with_hash(manifest_path)
    completed = _completed_ids(queue)
    tracked = _manifest_ids(manifest)
    gaps = completed - tracked
    queue_receipts = _queue_receipts(queue, gaps)
    transcripts = _transcript_evidence(gaps, transcript_root)
    concepts = _concept_evidence(gaps, concept_root)
    receipts = _receipt_evidence(gaps, evidence_roots)
    degraded_pages = _unmanifested_degraded_pages(manifest, concept_root)
    queue_state_ids = _queue_state_ids(queue)
    citation_coverage = _citation_coverage(concept_root)
    page_parity = _manifest_page_parity(manifest, concept_root)
    rows = []
    for nb_id in sorted(gaps):
        transcript = transcripts[nb_id]
        source_ids = transcript["source_ids"]
        output_reconciled = bool(source_ids and transcript["paths"] and concepts[nb_id])
        receipt_found = bool(receipts[nb_id])
        if output_reconciled and receipt_found:
            status = "output_and_receipt_found_manual_review"
        elif output_reconciled:
            status = "output_provenance_found_receipt_missing"
        elif receipts[nb_id]:
            status = "receipt_only_output_missing"
        else:
            status = "queue_only_no_local_output_evidence"
        rows.append({
            "notebook_id": nb_id,
            "status": status,
            "queue_completed_records": queue_receipts[nb_id],
            "transcript_count": len(transcript["paths"]),
            "transcript_paths": transcript["paths"],
            "source_ids": source_ids,
            "transcript_titles": transcript["titles"],
            "exported_dates": transcript["exported_dates"],
            "concept_count": len(concepts[nb_id]),
            "concept_paths": concepts[nb_id],
            "transcript_sha256": {
                path: digest
                for path in transcript["paths"]
                if (digest := _file_sha256(Path(path))) is not None
            },
            "receipt_paths": receipts[nb_id],
            "concept_sha256": {
                path: digest
                for path in concepts[nb_id]
                if (digest := _file_sha256(Path(path))) is not None
            },
            "manifest_recovery_eligible": False,
        })
    output_reconciled_count = sum(
        row["status"] in {
            "output_provenance_found_receipt_missing",
            "output_and_receipt_found_manual_review",
        }
        for row in rows
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "queue_path": str(queue_path),
        "manifest_path": str(manifest_path),
        "queue_sha256": queue_sha256,
        "manifest_sha256": manifest_sha256,
        "queue_state_ids": queue_state_ids,
        "completed_distinct_count": len(completed),
        "manifest_entry_count": len(tracked),
        "gap_count": len(rows),
        "output_provenance_found_count": output_reconciled_count,
        "manifest_recovery_eligible_count": 0,
        "gaps": rows,
        "manifest_page_parity": page_parity,
        "unmanifested_degraded_page_count": len(degraded_pages),
        "unmanifested_degraded_pages": degraded_pages,
        "citation_coverage": citation_coverage,
        "reconciliation_receipt": {
            "queue_sha256": queue_sha256,
            "manifest_sha256": manifest_sha256,
            "queue_state_ids": queue_state_ids,
            "manifest_missing_ownership": {
                "references_missing_on_disk": page_parity[
                    "manifest_references_missing_on_disk"
                ],
                "degraded_pages_missing_ownership": degraded_pages,
            },
            "duplicate_manifest_ownership": page_parity[
                "duplicate_manifest_slug_ownership"
            ],
            "citation_coverage": citation_coverage,
            "recovery_eligibility": {
                "eligible": False,
                "status": "ineligible_read_only_audit",
                "reason": (
                    "No manifest mutation is authorized by this audit; exact "
                    "worker/profile/attempt evidence and a separately reviewed "
                    "repair packet are required."
                ),
            },
        },
        "decision": (
            "no_safe_manifest_recovery_receipts_incomplete"
            if rows
            else "no_completed_queue_ids_missing_from_manifest"
        ),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Historical Manifest Gap Audit",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Decision",
        "",
        f"`{report['decision']}`",
        "",
        f"- Distinct completed queue IDs: {report['completed_distinct_count']}",
        f"- Manifest entries: {report['manifest_entry_count']}",
        f"- Missing manifest entries: {report['gap_count']}",
        f"- Output/provenance matches: {report['output_provenance_found_count']}",
        f"- Manifest-recovery eligible: {report['manifest_recovery_eligible_count']}",
        f"- Queue SHA-256: `{report['queue_sha256'] or 'unavailable'}`",
        f"- Manifest SHA-256: `{report['manifest_sha256'] or 'unavailable'}`",
        "",
        "The audit is read-only. Transcript and concept output are not sufficient "
        "to fabricate a manifest entry when the exact worker/profile receipt is "
        "missing.",
        "",
        "## Gaps",
        "",
        "| Notebook ID | Status | Transcripts | Concepts | Receipts |",
        "|---|---|---:|---:|---:|",
    ]
    for row in report["gaps"]:
        lines.append(
            f"| `{row['notebook_id']}` | `{row['status']}` | "
            f"{row['transcript_count']} | {row['concept_count']} | "
            f"{len(row['receipt_paths'])} |"
        )
    if not report["gaps"]:
        lines.append("| none | none | none |")
    lines.extend([
        "",
        "## Manifest/page parity (not ownership proof)",
        "",
        f"- Concept files: {report['manifest_page_parity']['concept_file_count']}",
        f"- Manifest unique slugs: {report['manifest_page_parity']['manifest_unique_slug_count']}",
        f"- Manifest references missing on disk: {len(report['manifest_page_parity']['manifest_references_missing_on_disk'])}",
        f"- Duplicate slug ownership groups: {len(report['manifest_page_parity']['duplicate_manifest_slug_ownership'])}",
        f"- Unowned concept files: {report['manifest_page_parity']['unowned_concept_file_count']}",
        f"- Citation coverage: {report['citation_coverage']['citation_coverage_percent']}%",
        f"- Degraded-page citation coverage: {report['citation_coverage']['degraded_citation_coverage_percent']}%",
        "",
        "These counts describe local path parity only. They do not create a "
        "worker/profile/attempt receipt and cannot make a historical gap "
        "eligible for manifest recovery.",
        "",
        "## Degraded pages outside the current manifest",
        "",
        f"- Count: {report['unmanifested_degraded_page_count']}",
        "",
        "These pages are audit warnings only. They are not safe manifest-repair "
        "receipts and must not be deleted or promoted automatically.",
        "",
        "| Page | Notebook ID | Status |",
        "|---|---|---|",
    ])
    for page in report["unmanifested_degraded_pages"]:
        lines.append(
            f"| `{page['path']}` | `{', '.join(page['notebook_ids']) or 'missing'}` | "
            f"`{page['status']}` |"
        )
    if not report["unmanifested_degraded_pages"]:
        lines.append("| none | none | none |")
    lines.extend([
        "",
        "## Allowed action",
        "",
        "Recover a gap only when an exact worker receipt, profile, attempt, "
        "successful output, and source/manifest identity can be reconciled. "
        "This auditor intentionally never marks a gap eligible by itself.",
        "",
        "Recovery eligibility: `ineligible_read_only_audit`.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--evidence-root", type=Path, action="append", dest="evidence_roots",
                        help="Deprecated alias for --receipt-root")
    parser.add_argument("--receipt-root", type=Path, action="append", dest="receipt_roots")
    parser.add_argument("--transcript-root", type=Path, default=DEFAULT_TRANSCRIPT_ROOT)
    parser.add_argument("--concept-root", type=Path, default=DEFAULT_CONCEPT_ROOT)
    parser.add_argument("--output", type=Path,
                        help="Write JSON and adjacent Markdown receipt files")
    parser.add_argument("--print-receipt", action="store_true",
                        help="Print the complete JSON receipt to the terminal")
    args = parser.parse_args()
    if args.output is None and not args.print_receipt:
        parser.error("one of --output or --print-receipt is required")
    roots = tuple(args.receipt_roots or args.evidence_roots or DEFAULT_RECEIPT_ROOTS)
    report = build_report(
        args.queue,
        args.manifest,
        roots,
        args.transcript_root,
        args.concept_root,
    )
    md_path = None
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path = args.output.with_suffix(".md")
        md_path.write_text(render_markdown(report), encoding="utf-8")
    if args.print_receipt:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"json": str(args.output), "markdown": str(md_path), "gap_count": report["gap_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
