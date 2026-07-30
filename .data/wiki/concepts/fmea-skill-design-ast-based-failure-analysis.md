---
title: "FMEA skill design: AST-based component-level failure mode analysis"
created: 2026-07-29
source: session-019fa276 (/fmea skill build)
tags: [fmea, failure-modes, ast-analysis, pipeline-safety, skill-design, risk-priority, review]
agent: grok
host: both
cognitive_load: 2
verification: observed
summary: >
  Decision to build /fmea as an AST-based static analyzer rather than an
  LLM-driven reasoning skill. The scanner walks Python ASTs to find I/O
  boundaries (globs, subprocess calls, file ops, shared directories) and
  generates failure-mode tables with S×O×D ratings and RPN scores. First
  run on the nlm-to-wiki pipeline found the exact cluster_transcripts.py:195
  glob-without-filter boundary (RPN 576) that caused the real contamination
  bug. AST analysis was chosen over LLM reasoning because it's deterministic,
  fast (<1s), and catches the structural failure class (missing identity
  filters on shared-directory globs) that narrative pre-mortems miss.
relations:
  - target: wiki/concepts/shared-directory-contamination-pattern.md
    type: extends
  - target: wiki/concepts/systematic-problem-anticipation-methods-and-existing-tools.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# FMEA skill design: AST-based component-level failure mode analysis

## Decision context

**The problem:** `/red-team` and `/tp` catch narrative-level failures ("what
if the approach is wrong?"). They don't catch component-level failures
("what if this script reads from a shared directory without filtering?").
The cluster-filter bug in nlm-to-wiki (1,842 transcripts processed instead
of 298, causing 0-page failures) is the canonical example — no narrative
review would have caught it, but the I/O boundary was structurally visible.

**The question:** should /fmea use LLM reasoning ("describe your pipeline
and I'll hypothesize failure modes") or static analysis ("scan the code
and find the boundaries mechanically")?

## Decision: AST-based static analysis

**Chosen:** AST visitor that walks Python source files, identifies I/O
boundary calls, and generates failure modes from deterministic heuristics.

**Steelman of the rejected alternative (LLM reasoning):** an LLM can
reason about *semantic* failure modes ("what if the user provides invalid
input?") that AST analysis can't see. It can also suggest mitigations
("add a validation check here"). This is genuinely more powerful for
complex failure analysis.

**Why AST won:** the highest-value failure class in our workspace is
*structural* — missing identity filters on shared-directory globs,
non-atomic writes, files in P:/tmp/ that other LLMs delete. These are
all detectable from the AST without reasoning. AST analysis is:
- **Deterministic** — same input always produces same output (LLM reasoning varies)
- **Fast** — <1s for a 10-script pipeline (LLM reasoning takes minutes)
- **Mechanical** — doesn't suffer closure pressure or fatigue
- **Repeatable** — can run in CI or pre-commit without model access

## How it works

1. **Walk** target directory for `.py` files
2. **AST visitor** identifies 7 boundary types:
   - `file_read` (open, read_text) — S=5, O=4, D=3
   - `file_write` (write_text, os.replace) — S=6, O=5, D=7
   - `glob` (rglob, glob, iterdir) — S=9, O=8, D=8 (highest RPN: 576)
   - `subprocess` (subprocess.run, Popen) — S=7, O=6, D=5
   - `state_file` (sqlite3.connect) — S=6, O=4, D=4
   - `shared_dir` (paths matching /tmp/, /.data/, /.state/) — S=7, O=7, D=6
3. **Generate failure modes** from rating heuristics per boundary type
4. **Sort** by RPN (S×O×D) descending

## First-run validation

Scanned `P:/.agents/skills/nlm-to-wiki/scripts/` (8 Python files):
- 122 failure modes found
- 13 at RPN ≥400 (all glob boundaries)
- Top finding: `cluster_transcripts.py:195` — the exact line where the
  contamination bug was fixed with per-notebook frontmatter filtering

The scanner **would have caught the bug before it shipped** — which was
the acceptance criterion from the handoff.

## What this means for our workspace

/fmea fills a gap between narrative review (/tp, /red-team) and runtime
verification (/check, edit-then-verify). The three layers:

| Layer | What it catches | When it runs |
|-------|----------------|-------------|
| /fmea (AST) | Structural I/O boundary failures | Before pipeline runs at scale |
| /tp, /red-team (narrative) | Approach-level failures, framing errors | Before committing to a design |
| /check (runtime) | Behavioral failures, wrong output | After implementation |

Run /fmea on any pipeline before scaling it. Run it after refactoring to
verify the refactor didn't introduce new boundaries.

## Falsifier

This skill is wrong if:
- The rating heuristics are too aggressive (flagging everything as high-RPN)
- The rating heuristics are too conservative (missing real failures)
- AST analysis can't see a failure class that matters (e.g., race conditions
  in async code — AST sees the calls but not the timing)
- Nobody runs it before pipeline failures occur (usage gap, not capability gap)

## Receipts

- Skill: `P:/.agents/skills/fmea/scripts/fmea_scan.py` (commit `05cb160`)
- Tests: `P:/.agents/skills/fmea/scripts/test_fmea_scan.py` (10 tests, commit `eddf1f0`)
- First run: nlm-to-wiki pipeline, 122 modes, top RPN 576 at cluster_transcripts.py:195
- Handoff design: `P:/docs/handoffs/problem-prediction-skills-20260727/HANDOFF.md` Item 1
- Contamination pattern: [[shared-directory-contamination-pattern]]
- Mechanical enforcement principle: [[mechanical-enforcement-over-behavioral-reminder]]
- Problem anticipation survey: [[systematic-problem-anticipation-methods-and-existing-tools]]
