---
title: "Verifier pattern classification: specificity ordering beats highest-match"
created: 2026-07-31
source: session-019fb3a8 (/tp critique of _detect_verifier proposal)
tags: [verification, receipt-system, pattern-matching, specificity, gaming-surface, hook-fix]
agent: grok
host: both
cognitive_load: 2
verification: workspace_verified
summary: >
  The verification receipt writer classifies commands by scanning regex
  patterns. Original ordering was by rank (not specificity), causing compound
  commands to misclassify. /tp critiqued a proposed "highest-match" fix as
  creating a gaming surface. The actual fix: reorder by specificity (unique
  tokens first). The exit-code gate (line 987 in quality_gate.py) makes most
  gaming concerns moot — a failed command produces non-zero exit →
  VERIFICATION_FAILED receipt → gate rejects.
relations:
  - target: wiki/concepts/framing-check-pattern
    type: related
  - target: wiki/concepts/subagent-shell-quoting-durable-fix
    type: related
---

# Verifier pattern classification: specificity ordering beats highest-match

## Decision context

The verification receipt writer's `_detect_verifier` function classifies shell commands by matching regex patterns. The original ordering placed `py_compile` (rank 0, syntax) before `ruff` (rank 2, static_analysis) and `pytest` (rank 3, unit_behavior). This meant combined commands like `ruff check f.py && py_compile f.py && pytest test_f.py` were classified as `syntax` instead of `static_analysis` or `unit_behavior`.

A proposal to change to "highest-match" (scan all patterns, return highest rank) was critiqued by /tp as creating a gaming surface: `echo "pytest" && py_compile f.py` would match pytest's pattern and claim `unit_behavior` without actually running tests.

## The actual fix

**Reorder patterns by specificity, not by rank.** Unique tokens (pytest, ruff, runtime_hook_probe) are checked first; common substrings (py_compile, import) are checked last. First-match now returns the most specific verifier.

## Why the gaming concern is mostly moot

The close gate (`quality_gate.py` line 987) rejects any receipt where `actual_exit_status != 0`. So:
- `ruff && pytest` where ruff fails → non-zero exit → VERIFICATION_FAILED → rejected
- `echo "pytest" && py_compile` → py_compile exit 0, but no tests ran → the receipt claims unit_behavior, but the actual verification was only syntax-level

The remaining gaming surface (string injection via echo/echo in comments) is low-risk on this fleet because the agent writing receipts is the same agent that benefits from honest receipts — no adversarial separation.

## What this means for our workspace

- Pattern ordering matters: specificity > rank for first-match classifiers
- The exit-code gate is the structural defense against gaming, not the pattern classifier
- /tp fresh-lens critique correctly identified the gaming risk but incorrectly concluded it was fatal — verification against the actual code showed the exit-code gate handles it

## Falsifier

This is wrong if a future agent finds a way to produce exit-code-0 receipts for commands that didn't actually verify (e.g., `true && echo "pytest"`). The mitigation: the exit-code gate + the receipt writer's scope-matching logic (receipts must list the actual files checked).
