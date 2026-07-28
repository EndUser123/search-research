---
thread_id: verification-protocol-design-20260728
parent_handoff_path: none
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-28T14:05:00Z
status: open
handoff_type: investigation
accurate_as_of_head: LATEST
---

# Verification protocol design — multi-tier verification architecture

## Objective (one sentence)

Design and implement a multi-tier verification protocol that fills the gap
between per-edit read-back verification and per-session /check: a "scoped
tests after logical unit" tier that catches bugs fastest and cheapest.

## Status

OPEN — design clear, implementation needs operator input on where each piece lives.

## Producing context

The operator asked: "after a file edit or write, what's the best verification
we should do, given that on a stop event we can do a more comprehensive
verification? What should /review be given we also have /refactor?"

The analysis identified a 5-tier verification architecture:

```
1. Per-edit: read-back verify (automatic, PostToolUse)
2. Per-logical-unit: scoped tests (MISSING — the gap this handoff addresses)
3. Per-implementation-wave: /check (session-grounded)
4. After /check passes: /review (fresh-eyes, if load-bearing)
5. When design debt accumulates: /refactor (structural)
```

## The gap: Tier 2 (scoped tests)

Nothing currently fires between "I finished editing this file" and "let me run
/check on the whole session." The scoped test step is where most bugs get caught
fastest and cheapest (0.4s for a single test file vs 60s+ for /check with
subagents). It should be the default after any code edit, not just when the
model remembers.

## Design decisions needed

### D1: Where does the scoped-test reminder live?

**Option A: PostToolUse hook** — detects "N edits to .py files since last test
run" and reminds/incentivizes running scoped tests. Advisory, not blocking.
Cost: ~10ms per edit (counter check).

**Option B: AGENTS.md rule** — "after finishing a logical unit, run the scoped
test file." Behavioral rule — doesn't fire under pressure (the pattern this
workspace has documented repeatedly).

**Option C: /check auto-trigger** — when the model says "done with X," auto-fire
/check scoped to the changed files. Heavier than a test reminder but more
reliable.

**Recommendation:** Option A (PostToolUse hook). It's the mechanical-enforcement
pattern — same principle as the Stop hook receipt system. Behavioral rules (B)
have been shown to fail under closure pressure.

### D2: How does the hook know which test file to run?

The hook needs to map source files to test files. Patterns:
- `wiki_search.py` → `tests/test_wiki_search.py`
- `close_accounting.py` → `tests/test_scanner.py` (non-obvious mapping)
- `__lib/*.py` → `tests/test_*.py` (convention-based)

**Option A: Convention** — `{name}.py` → `tests/test_{name}.py`. Simple but
breaks on non-conventional mappings (close_accounting → test_scanner).

**Option B: Explicit mapping file** — a `.test_mapping.json` that maps source
files to test files. More accurate but maintenance burden.

**Option C: pytest --collect-only** — given a source file, find which test
files import it. Most accurate but slow (~2-5s per check).

**Recommendation:** Option A with override (convention + explicit exceptions
in a config file). Start simple, add exceptions as non-conventional mappings
are discovered.

### D3: /review vs /refactor boundary documentation

The distinction is clear but not documented in a wiki concept:

| Skill | Question | When | Lens |
|-------|----------|------|------|
| /review | "What bugs exist?" | After /check passes | Fresh-eyes, multi-lens |
| /refactor | "How should this be structured?" | When design debt accumulates | Structural |

**Recommendation:** write a wiki concept documenting the verification
architecture (the 5-tier model above). This concept would be referenced by
/check, /review, /refactor, and the new scoped-test hook.

### D4: Should /review auto-fire from /check?

Currently /check auto-fires /review when load-bearing triggers fire (hooks,
schemas, contracts touched). This is correct — but it adds 200-400s to every
/check on load-bearing work. The operator should decide whether this is worth
the latency or whether /review should be operator-invoked.

**Recommendation:** keep the auto-fire for now. The latency is justified for
load-bearing changes. Add `--no-auto-review` as an escape hatch (already
exists in the SKILL.md).

## Acceptance criteria

1. A PostToolUse hook (or equivalent) fires after code edits and reminds to
   run scoped tests
2. The hook maps source files to test files (convention + exceptions)
3. A wiki concept documents the 5-tier verification architecture
4. /review and /refactor have clearly documented boundaries

## Falsifier

This design is wrong if:
- The scoped-test reminder is too noisy (fires on every edit, not just logical
  units) → adjust the threshold (N edits or a "done" signal)
- The convention-based test mapping misses too many cases → switch to explicit
  mapping
- /review auto-fire adds unacceptable latency → make it operator-invoked

## Related

- Wiki: `verification-receipt-systems-design-landscape`
- Wiki: `mechanical-enforcement-over-behavioral-reminder`
- /check SKILL.md: Step 6.2 (auto-/review triggers)
- /review SKILL.md: multi-lens specialist architecture
- /refactor SKILL.md: structural improvement focus
