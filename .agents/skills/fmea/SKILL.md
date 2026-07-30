---
name: fmea
description: >
  Failure Modes and Effects Analysis for pipelines and systems. Scans a
  target directory's Python scripts, identifies I/O boundaries (shared
  directories, external APIs, state files, caches, databases, subprocess
  calls), and for each boundary generates a structured FMEA table with
  severity × occurrence × detection ratings and RPN (Risk Priority Number).
  Catches component-level failures that narrative pre-mortems miss.
metadata:
  short-description: "FMEA scanner — finds component-level failure modes in pipelines"
argument-hint: "[<pipeline-path>] [--json]"
host: grok
depends_on: []
consumes: []
provides: [failure-modes-analysis, risk-priority-scoring]
domain: review
---

# /fmea — Failure Modes and Effects Analysis

**Catches component-level failures the narrative frame misses.**

`/red-team` and `/tp` catch narrative-level failures ("what if the
approach is wrong?"). `/fmea` catches component-level failures ("what if
this script reads from a shared directory without filtering?").

## What it does

Given a pipeline path (e.g., `.agents/skills/nlm-to-wiki/scripts/`),
`/fmea` scans each Python script for I/O boundaries and generates a
structured failure-mode table:

| Component | Failure mode | Cause | Effect | S | O | D | RPN |
|-----------|-------------|-------|--------|---|---|---|-----|
| cluster_transcripts.py | Reads all transcripts, not just target notebook | No per-notebook filter on directory glob | Cross-notebook contamination, 0-page failures | 9 | 10 | 8 | 720 |

**S** = Severity (1-10), **O** = Occurrence (1-10), **D** = Detection (1-10, higher = harder to detect), **RPN** = S×O×D.

## Usage

```bash
# Scan a pipeline directory
python scripts/fmea_scan.py <pipeline-path>

# JSON output for programmatic consumption
python scripts/fmea_scan.py <pipeline-path> --json

# Scan a single file
python scripts/fmea_scan.py <file.py>
```

## How it works

1. **Walk** the target directory for `.py` files
2. **Identify I/O boundaries** via AST analysis:
   - File reads/writes (`open()`, `Path.read_text()`, `Path.write_text()`)
   - Directory globs (`rglob`, `glob`, `iterdir`)
   - Subprocess calls (`subprocess.run`, `subprocess.Popen`)
   - External APIs (`requests`, `httpx`, CLI tools via subprocess)
   - State files (`.json`, `.sqlite`, `.db`, config files)
   - Shared directories (paths containing `tmp/`, `data/`, `state/`)
3. **Generate failure modes** for each boundary
4. **Rate** S/O/D based on boundary type and patterns
5. **Sort** by RPN descending

## When to use

- Before running a pipeline at scale (catches contamination, data loss)
- After a bug fix (did the fix close the failure mode, or just the instance?)
- During pipeline design (which components need guards?)
- Before refactoring (which boundaries are fragile?)

## Reference

- Session 019fa276 cluster-filter bug: `cluster_transcripts.py` read ALL
  1,842 transcripts from 7 notebooks instead of 298 from the target
  notebook. FMEA would have flagged: shared directory + no filter = RPN 720.
- Wiki: `shared-directory-contamination-pattern.md`
- Wiki: `systematic-problem-anticipation-methods-and-existing-tools.md`
