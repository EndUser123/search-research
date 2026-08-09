---
title: Non-Regex Hook Optimization Alternatives
tags: [hooks, performance, optimization, pattern-matching]
created: 2026-04-15
source: session-derived (NotebookLM + live analysis)
relations:
  - target: wiki/concepts/mcp-http-server-placeholder-resolution
    type: related
---

# Non-Regex Hook Optimization Alternatives

Regex-based pattern matching in Claude Code hooks has systematic weaknesses: word-boundary false positives, backtracking pathologies, and per-pattern O(n) loops. Six alternatives address these at different layers.

---

## 1. Engine-Level Process Avoidance (`if` field)

**Zero-cost filtering** — Claude Code evaluates the `if` field natively before spawning any subprocess.

```json
{ "if": "Bash(git *)" }
```

No script is spawned for non-matching commands. `T_spawn = 0` for irrelevant commands. This is the highest-ROI optimization: eliminate the hook entirely for inputs it doesn't apply to.

**When to use**: Any hook that only applies to a subset of tools or commands.

---

## 2. Aho-Corasick Automaton

For phrase lists (e.g., `DEFER_PATTERNS` in `autonomy_gate.py`), compile keywords into an Aho-Corasick automaton: **single O(n) pass matching all patterns simultaneously**, vs looping through individual regex checks.

```python
import ahocorasick
A = ahocorasick.Automaton()
for idx, key in enumerate(DEFER_PHRASES):
    A.add_word(key, (idx, key))
A.make_automaton()
# Single pass: O(n) regardless of pattern count
matches = list(A.iter(text))
```

**When to use**: Lists of ≥5 literal phrases where order doesn't matter (e.g., DEFER_PATTERNS, LAZY_FIX_PHRASES).

---

## 3. SIMD-Accelerated Quick Rejection

Before deep pattern analysis, use CPU vector instructions (SSE2, AVX2, NEON via `memchr` crate or `bytearray.find()`) for sub-microsecond substring searches.

Acts as a **Global Quick Reject** layer:
- If the raw substring isn't found → bypass heavier matching entirely
- If found → proceed to full pattern check

```python
# Quick reject: check if any anchor keyword is present first
ANCHORS = frozenset(["leave", "defer", "later", "wait", "skip"])
if not any(anchor in text_lower for anchor in ANCHORS):
    return None  # Fast exit, no regex needed
```

**When to use**: Hooks running on every Stop or PostToolUse where most responses are clean.

---

## 4. `frozenset` + Substring Matching

Replace `\b` word-boundary regex with exact substring lookups against a `frozenset`.

```python
# Instead of:
_PATTERNS = [re.compile(r"\bI'll\s+leave\s+that\b", re.IGNORECASE)]

# Use:
DEFER_EXACT = frozenset(["i'll leave that", "leave that for now", "defer this"])
hit = next((p for p in DEFER_EXACT if p in text_lower), None)
```

**Why better than `\b` regex**:
- Word boundaries break on compound commands (`&&`, `||`), trailing spaces, JavaScript → "Java Script"
- `frozenset` lookup is O(1), no backtracking pathologies like `(a+)+`
- Context separation: substring match confirms keyword exists; span classifier handles context separately

**Refactoring candidates in `lazy_closure_detector.py`**: The compiled phrase lists (`_LAZY_JUSTIFICATION`, `_WORK_AVOIDANCE`, etc.) are all candidates for `frozenset` replacement where exact phrases suffice.

---

## 5. AST Span Classification

Parse command structure to classify tokens by `SpanKind` before applying any pattern check:

| SpanKind | Examples | Action |
|----------|----------|--------|
| `Executed` | `git commit`, `python foo.py` | MUST check |
| `InlineCode` | `` `echo "math"` `` | MUST check |
| `Data` | `echo "skip to domain"` | Skip |
| `Comment` | `# skip this` | Skip |

This two-tier approach eliminates false positives from string literals without regex complexity.

**False positive example this prevents**: `echo "I'll leave that for now"` triggering a deferral detection.

---

## 6. Prompt Hooks (LLM Evaluation)

For **semantically ambiguous** cases that regex cannot reliably handle, use `type: "prompt"` hooks with a fast model (Haiku) returning strict JSON:

```json
{ "ok": false, "reason": "Response defers debt without spawn_task" }
```

**When to use**: Semantic decisions — e.g., "did the model acknowledge debt without tracking it?" — where 6+ regex variants still miss novel phrasing.

**Cost**: ~50–200ms latency per invocation. Use only for Stop hooks, not PreToolUse.

---

## Specific Refactoring Candidates

| File | Current | Better Alternative |
|------|---------|-------------------|
| `autonomy_gate.py` DEFER_PATTERNS | 6 regex word-boundary patterns | Aho-Corasick or `frozenset` scan |
| `lazy_closure_detector.py` phrase lists | Compiled regex lists with `\b` | `frozenset` categories + AST Span Classifier |
| `StopHook_skill_execution_gate.py` slash extraction | `re.match(r"^/([a-zA-Z][\w-]*)", ...)` | `prompt.startswith("/") + split()` |
| `StopHook_skill_execution_gate.py` required_first_command_patterns | YAML frontmatter + `re.search` loop | `frozenset` of exact command strings |
| `anti_lazy_diff_nudge.py` suffix match | `re.search(r"/SKILL\.md$", path, re.IGNORECASE)` | `path.lower().endswith("/skill.md")` |

---

## Canonical Reference Implementation

**dcg (Destructive Command Guard)** — cited as the reference implementation using all four techniques: Aho-Corasick, SIMD quick-reject, span classification, and dual regex engine. Pattern to emulate for high-throughput hooks.

---

## Decision Matrix

```
Is the hook called on every tool invocation?
├─ YES → Use if field (technique 1) + SIMD quick-reject (3) first
│
└─ NO → Is the input a fixed set of literal phrases?
         ├─ YES → frozenset (4)
         └─ NO → Are phrases ≥5 patterns? → Aho-Corasick (2)
                 Is context (literal vs executed) the failure mode? → AST (5)
                 Is the decision semantic? → Prompt hook (6)
```

## Related

- Lazy Closure Detector
- Deferral Detection Pattern
- hook-architecture
- Stop Hook Backstop Pattern
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
