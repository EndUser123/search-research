---
current_session_id: 019fdf3d-a0bd-7062-abc4-24dcf064ae49
parent_handoff_path: P:/docs/handoffs/session-019fdf3d-ship-py-hardening-20260808/HANDOFF.md
status: open
last_updated_at: 2026-08-08T12:25:00Z
---

# Session observations — 2026-08-08

Session 019fdf3d: AAR-driven fleet hardening cycle (ship-py, /tp, /todo, /go, skill-dev, minimal_bias_gate, quality_gate).

## Observations

### 1. Verification receipt pattern ordering is load-bearing

The quality_gate verification loop burned 6+ turns because `verification_receipt_writer.py` matched `ast.parse` as `unit_behavior` instead of `syntax` — the generic "python test/verify/check" pattern was listed BEFORE `ast.parse|py_compile` in `_VERIFIER_PATTERNS`. Pattern priority in regex-based receipt classification is a silent failure mode: the receipt gets the wrong capability tag, the gate sees insufficient capability, and the loop burns turns with misleading diagnostics.

**Implication:** any regex-based capability classifier needs ordered patterns from most-specific to least-specific. A future `validate_patterns.py` could check for this class of ordering bug by verifying no general pattern shadows a specific one.

### 2. Ship-py as self-correcting pipeline — the check-and-fix principle scales

Adding `--fix` modes to doc-check and skill-dev reduced the verification loop from "report → manual fix → re-verify" to "report → auto-fix → re-verify." This worked because the fixes were deterministic (add `host:` frontmatter, close code fences, convert unresolved wikilinks). The principle: verification skills should auto-fix what they can deterministically fix, not just report. This applies broadly to any scanner that finds deterministic defects.

### 3. Compaction summary preamble pollutes continuation-coverage extraction

The continuation-coverage system extracted the compaction summary text as a `user_goal` candidate. This is a known false positive from `transcript_opening_goal` extraction when the session starts from compaction. The extraction should skip compaction-summary blocks (text matching "This session is being continued from a previous conversation").

### 4. /tp review target ambiguity is a two-instance pattern this session

The agent targeted shipped code instead of proposals when asked "/tp review" — twice in one session. The fix (target-confirmation step in protocol.md) is structural, but the pattern itself signals that "review" without a stated target defaults to code-review framing. The default should be "state the target first" for ALL review invocations, not just /tp.

### 5. Todo accounting gate revealed 28→1 silent collapse

The /todo scanner produced 28 items but the renderer surfaced only 1. The LLM collapsed 27 items to "done" without evidence. The accounting gate (`Scanned N → surfaced N → dropped N`) forces the collapse to be visible. This is the same class as the "evidence-scope discipline" rule — stronger umbrella claims than the evidence supports — but applied to rendering, not completion claims.
