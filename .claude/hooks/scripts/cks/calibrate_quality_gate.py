#!/usr/bin/env python3
"""Calibrate the CKS quality gate against the real corpus.

Negatives (should REJECT): the 109 auto-captured decision fragments purged on
2026-07-04, read from the pre-purge backup DB.
Positives (should ACCEPT): the curated knowledge/pattern rows in the live DB
(ingested from human-written memory topic files).

Emits measured_tp_on_corpus per the CLAUDE.md gate rule. The gate may only
block once this reports acceptable discrimination.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_gate import judge_entry

BACKUP_DB = Path("P:/packages/.claude-marketplace/plugins/search-research/data/cks.db.bak-20260704-decision-purge")
LIVE_DB = Path("P:/packages/.claude-marketplace/plugins/search-research/data/cks.db")
OUT = Path(__file__).resolve().parent / "quality_gate_calibration.json"
WORKERS = 6


def load(db: Path, where: str) -> list[tuple]:
    conn = sqlite3.connect(db)
    rows = conn.execute(f"SELECT id, type, title, content FROM entries WHERE {where}").fetchall()
    conn.close()
    return rows


def main() -> None:
    negatives = load(BACKUP_DB, "type='decision'")
    positives = load(LIVE_DB, "type IN ('knowledge','pattern')")
    print(f"corpus: {len(negatives)} negatives (junk), {len(positives)} positives (curated)")

    def score(row, expected):
        _id, etype, title, content = row
        v = judge_entry(title or "", content or "", etype)
        return {"id": _id, "type": etype, "title": (title or "")[:80],
                "expected": expected, "verdict": v}

    results = []
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(score, r, "reject") for r in negatives]
        futs += [ex.submit(score, r, "accept") for r in positives]
        for i, fut in enumerate(cf.as_completed(futs), 1):
            results.append(fut.result())
            if i % 25 == 0:
                print(f"  scored {i}/{len(futs)}")

    neg = [r for r in results if r["expected"] == "reject"]
    pos = [r for r in results if r["expected"] == "accept"]
    unknown = [r for r in results if r["verdict"] == "unknown"]
    tp = sum(1 for r in neg if r["verdict"] == "reject")          # junk correctly rejected
    fn = sum(1 for r in neg if r["verdict"] == "accept")          # junk wrongly accepted
    fp = sum(1 for r in pos if r["verdict"] == "reject")          # curated wrongly rejected
    tn = sum(1 for r in pos if r["verdict"] == "accept")          # curated correctly accepted

    summary = {
        "measured_tp_on_corpus": {
            "corpus": "cks.db.bak-20260704-decision-purge (109 junk) + live knowledge/pattern (curated)",
            "junk_rejected_TP": tp, "junk_accepted_FN": fn,
            "curated_rejected_FP": fp, "curated_accepted_TN": tn,
            "unknown_verdicts": len(unknown),
            "junk_reject_rate": round(tp / len(neg), 3) if neg else None,
            "curated_reject_rate_FP": round(fp / len(pos), 3) if pos else None,
        },
        "false_positives": [r for r in pos if r["verdict"] == "reject"],
        "false_negatives": [r for r in neg if r["verdict"] == "accept"],
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary["measured_tp_on_corpus"], indent=2))
    print(f"detail -> {OUT}")


if __name__ == "__main__":
    main()
