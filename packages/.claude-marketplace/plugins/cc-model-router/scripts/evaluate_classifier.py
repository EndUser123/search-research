#!/usr/bin/env python3
"""Evaluation harness for the hierarchical classifier.

Reads a labeled corpus, runs the classify pipeline on each prompt,
and reports confusion matrix + per-class metrics + low-confidence rate.

Usage:
    python scripts/evaluate_classifier.py [--corpus tests/fixtures/eval_corpus.jsonl]

Corpus format (JSONL, one per line):
    {"prompt": "...", "label": "reasoning"}
    {"prompt": "...", "label": "coding"}
    {"prompt": "...", "label": "background"}
    {"prompt": "...", "label": "local-coding"}
"""
from __future__ import annotations

import json
import sys
import pathlib
from collections import Counter, defaultdict

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

from classifier.pipeline import classify_pipeline, ClassifyResult
from classifier.tfidf_backend import TfidfBackend

EXEMPLARS = PLUGIN_ROOT / "config" / "exemplars.json"
DEFAULT_CORPUS = PLUGIN_ROOT / "tests" / "fixtures" / "eval_corpus.jsonl"

LABELS = ["background", "coding", "reasoning", "local-coding"]


def load_corpus(path: str | pathlib.Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))
    return rows


def evaluate(corpus: list[dict], scorer, config: dict) -> None:
    # Collect predictions
    y_true, y_pred = [], []
    low_conf_count = 0
    short_followup_results = []

    for row in corpus:
        prompt = row["prompt"]
        label = row["label"]
        context = row.get("context")
        result = classify_pipeline(prompt, scorer, config, context)
        y_true.append(label)
        y_pred.append(result.task_type)
        if result.low_confidence:
            low_conf_count += 1
        # Track short follow-ups separately
        if len(prompt.split()) < 10:
            short_followup_results.append({
                "prompt": prompt[:60], "expected": label,
                "got": result.task_type, "conf": round(result.confidence, 3),
                "low": result.low_confidence,
            })

    # Confusion matrix
    all_labels = sorted(set(y_true + y_pred))
    print("=" * 60)
    print("CLASSIFIER EVALUATION REPORT")
    print("=" * 60)
    print(f"\nCorpus size: {len(corpus)}")
    print(f"Labels: {all_labels}\n")

    # Confusion matrix
    cm = defaultdict(lambda: defaultdict(int))
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1

    print("Confusion Matrix (rows=actual, cols=predicted):")
    header = f"{'':>15s}" + "".join(f"{l:>15s}" for l in all_labels)
    print(header)
    for actual in all_labels:
        row = f"{actual:>15s}" + "".join(f"{cm[actual][pred]:>15d}" for pred in all_labels)
        print(row)

    # Per-class metrics
    print("\nPer-Class Metrics:")
    print(f"{'Class':>15s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s} {'Support':>8s}")
    total_correct = 0
    for label in all_labels:
        tp = cm[label][label]
        fp = sum(cm[a][label] for a in all_labels if a != label)
        fn = sum(cm[label][p] for p in all_labels if p != label)
        support = sum(cm[label].values())
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        total_correct += tp
        print(f"{label:>15s} {precision:>10.3f} {recall:>10.3f} {f1:>10.3f} {support:>8d}")

    accuracy = total_correct / len(corpus) if corpus else 0
    print(f"\n{'Accuracy':>15s}: {accuracy:.3f}")
    print(f"{'Low-conf rate':>15s}: {low_conf_count}/{len(corpus)} = {low_conf_count/len(corpus):.3f}")

    # Top confusion pairs
    confusions = []
    for actual in all_labels:
        for pred in all_labels:
            if actual != pred and cm[actual][pred] > 0:
                confusions.append((cm[actual][pred], actual, pred))
    confusions.sort(reverse=True)
    if confusions:
        print("\nTop Confusion Pairs:")
        for count, actual, pred in confusions[:5]:
            print(f"  {actual} → {pred}: {count}")

    # Short follow-up report
    if short_followup_results:
        print(f"\nShort Follow-up Prompts (<10 words): {len(short_followup_results)}")
        correct = sum(1 for r in short_followup_results if r["got"] == r["expected"])
        print(f"  Accuracy on short: {correct}/{len(short_followup_results)} = {correct/len(short_followup_results):.3f}")
        for r in short_followup_results:
            mark = "✓" if r["got"] == r["expected"] else "✗"
            print(f"  {mark} [{r['conf']:.2f}] '{r['prompt']}' expected={r['expected']} got={r['got']}")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Evaluate classifier on labeled corpus")
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS), help="Path to labeled corpus JSONL")
    args = ap.parse_args()

    corpus_path = pathlib.Path(args.corpus)
    if not corpus_path.exists():
        print(f"Corpus not found: {corpus_path}", file=sys.stderr)
        sys.exit(1)

    corpus = load_corpus(corpus_path)
    scorer = TfidfBackend(EXEMPLARS) if EXEMPLARS.exists() else None
    config = {"classifier": {
        "semantic_threshold": 0.55, "low_confidence_margin": 0.10,
        "background_threshold": 0.50, "reasoning_threshold": 0.60,
        "trivial_coding_max_words": 15, "followup_context_boost": 0.15,
    }}

    evaluate(corpus, scorer, config)


if __name__ == "__main__":
    main()
