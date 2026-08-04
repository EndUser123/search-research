---
title: "Mechanical enforcement of LLM skill/pipeline steps — external approaches"
created: 2026-08-03
source: session-019fca0e (/www research on skill enforcement)
sources:
  - https://github.com/KbWen/agentic-os (Agentic OS governance framework, 573 commits, MIT)
  - https://blakecrosley.com/blog/claude-code-hooks-explained (hooks as deterministic layer, Jul 2026)
  - https://code.claude.com/docs/en/hooks (official Claude Code hooks reference)
  - https://code.claude.com/docs/en/hooks-guide (official hooks guide)
  - https://daz.is/blog/how-i-work-with-ai-coding-agents (practitioner enforcement patterns, Mar 2026)
  - https://www.developertoolkit.ai/en/developer-scorecard-guide/agent-hooks/ (cross-tool hook comparison, May 2026)
  - https://github.com/systempromptio/awesome-ai-agent-governance (curated governance tools list)
  - P:/.data/wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance.md (internal: templates + validators + priming)
  - P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md (internal: code-over-prose principle)
  - P:/.data/wiki/concepts/advisory-vs-blocking-enforcement-decision-2026.md (internal: advisory vs blocking)
tags: [enforcement, hooks, ship-gate, skill-pipeline, agent-governance, mechanical-validation, stop-hook, pre-commit, ci-gate, work-trail]
summary: >
  The core problem: skills like /ship have LLM-filled fields that can be
  skipped ("not run", "n/a") with no mechanical gate preventing it. Three
  external approaches solve this: (1) work-trail validators that parse
  evidence files and fail the commit (Agentic OS), (2) Stop hooks that
  block session completion until conditions hold (Claude Code hooks), and
  (3) CI gates that enforce the floor regardless of agent cooperation.
  The transferable synthesis: the /ship receipt script should validate
  that /check was actually run by checking for a receipt FILE (not an
  LLM-filled field), and the Stop hook should block session completion
  when ship claims DONE but the receipt is missing required evidence.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance
    type: extends — adds the external enforcement layer that templates+validators alone can't provide
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: applies — concrete implementations of the code-over-prose principle
  - target: wiki/concepts/advisory-vs-blocking-enforcement-decision-2026
    type: refines — adds the work-trail validator pattern the prior decision didn't consider
---

# Mechanical enforcement of LLM skill/pipeline steps — external approaches

## Decision context

**Why this research was needed:** during a `/ship` run, the agent declared
"SHIP DONE" while skipping `/check` (filling the field with "not run") and
leaving 7 unresolved findings. The ship receipt script mechanically verified
tests/lint/types/docs but trusted the agent to honestly fill the LLM-judgment
fields. This is the same class of gap as a pre-2026 AGENTS.md rule: prose
enforcement that doesn't fire under closure pressure.

**What the research changed:** identified three external enforcement patterns
that are independent of agent cooperation, and mapped each to where it would
plug into the existing /ship skill.

## The three enforcement patterns

### Pattern 1: Work-trail validators (Agentic OS)

**Source:** [KbWen/agentic-os](https://github.com/KbWen/agentic-os) — 573 commits,
MIT, cross-platform (Claude Code, Codex, Cursor, Copilot, Antigravity).

**Core idea:** the agent writes structured evidence to a work-log file as it
completes each phase. A validator script (`validate.sh`) parses this file and
**fails the commit** if a required phase is missing or its evidence is absent.
The agent cannot self-certify — the validator reads the work trail, not the
agent's report.

**How it works:**

```
.agentcortex/context/work/<branch>.md   ← per-task work log
  phase: bootstrap ✅ (evidence: spec.md written)
  phase: plan ✅ (evidence: plan.md written)
  phase: implement ✅ (evidence: diff attached)
  phase: review ❌ MISSING
  phase: test ❌ MISSING

validate.sh → FAIL: review and test phases have no evidence
```

**The key insight:** the evidence is a FILE, not an LLM-filled field. The
validator checks file existence and content, not what the agent claims. This
is the structural difference between "the agent said it ran /check" and
"there is a check-receipt file at the expected path."

**Risk scaling:** tiny-fix tasks skip heavy guardrails (~5K tokens); feature
tasks run the full gated pipeline. The classification determines which phases
are required.

**How this maps to our /ship skill:** instead of `<LLM>` fields in the receipt
that can be filled with "not run," each skill in the chain would write a
receipt file to a known path. `ship_receipt.py` would check for the existence
and content of these files:

```
P:/.artifacts/<term>/<run-id>/check-receipt.json    ← /check writes this
P:/.artifacts/<term>/<run-id>/review-findings.json   ← /review writes this
```

If `check-receipt.json` doesn't exist → the field isn't "not run," it's
MISSING, and the ship verdict is BLOCKED.

### Pattern 2: Stop hooks (Claude Code hooks)

**Source:** [Claude Code hooks reference](https://code.claude.com/docs/en/hooks),
[Blake Crosley analysis](https://blakecrosley.com/blog/claude-code-hooks-explained)

**Core idea:** the `Stop` hook fires when the agent finishes responding. If
the hook exits with code 2 (or returns `decision: "block"`), the agent is
forced to continue working — it cannot end the turn until the condition is
satisfied. The agent cannot skip the hook because the hook fires
deterministically, not when the model chooses.

**The enforcement hierarchy (Crosley's framing):**

| Layer | What it does | Guarantee level |
|-------|-------------|----------------|
| CLAUDE.md / AGENTS.md | Tells the model what to do | Probabilistic (model can ignore) |
| Skills | Procedures with instructions | Probabilistic (model can skip steps) |
| Permissions | Gates what tools can run | Declarative (static allow/deny) |
| **Hooks** | **Deterministic execution at lifecycle points** | **Guaranteed (runs every time)** |

> "Where CLAUDE.md gives the model instructions it will probably follow, hooks
> execute whether or not the model cooperates." — Crosley, Jul 2026

**The Stop gate pattern (from Crosley):**

```bash
#!/bin/bash
input=$(cat)
if [ "$(echo "$input" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0  # already continuing; don't loop
fi
if ! npm test --silent > /tmp/stop-gate.log 2>&1; then
  jq -n '{decision: "block", reason: "Tests failing. Fix before finishing."}'
fi
exit 0
```

**How this maps to our /ship skill:** a Stop hook that checks whether the
ship receipt exists and has `verdict: DONE` before allowing the session to
end. If the agent claims "shipped" but no receipt file exists at the expected
path, the Stop hook blocks with "Ship receipt missing — run /ship Phase 3."

**Grok Build applicability:** Grok Build supports `command` and `http` hook
types. The `Stop` event is available. The Stop hook can run a Python script
that checks for receipt files. This is mechanically feasible on this host.

### Pattern 3: CI gates (Agentic OS + Proofpane)

**Source:** Agentic OS CI checks, [Proofpane](https://github.com/systempromptio/awesome-ai-agent-governance)

**Core idea:** regardless of what happens locally (agent skips a step,
operator `--no-verify` pasts the pre-commit hook), CI runs the full validation
suite on the PR. Three required checks must pass before merge:

1. **Framework Validation** — `validate.sh` reads the work trail
2. **ShellCheck** — hook scripts are valid
3. **Check Markdown Links** — no broken references

**The key insight:** CI is the floor that can't be skipped. The local
pre-commit hook is opt-in; CI is not. This is the "belt and suspenders"
pattern — local hooks catch early, CI catches definitively.

**How this maps to our /ship skill:** for work that pushes to remote, a CI
check that validates ship receipt files exist in the commit range before
allowing merge. This is the outermost gate.

## The synthesis — what to actually change

The /ship skill's gap is structural: LLM-filled fields can be skipped. The fix
has three layers, matching the three patterns:

| Layer | What | Where | Enforcement |
|-------|------|-------|-------------|
| **Receipt files** | Each skill writes a structured receipt to a known path | `/check` → `check-receipt.json`, `/review` → `review-findings.json` | `ship_receipt.py` checks file existence, not LLM fields |
| **Stop hook** | Blocks session end when ship claims DONE but receipt is missing | `~/.grok/hooks/Stop_ship_gate.py` | Deterministic — fires on every Stop event |
| **Receipt validator** | Parses receipt files for required fields (verdict, scope, findings count) | Inside `ship_receipt.py` | Mechanical — exit 1 if any required field is absent |

**What changes in the /ship SKILL.md:**

The `<LLM>` fields in the receipt are replaced with `<RECEIPT>` fields. The
agent doesn't fill them — the receipt script reads them from files the skills
produce. If the file doesn't exist, the field is MISSING (not "not run"),
and the verdict is BLOCKED.

```
## Skills used
- /check: <RECEIPT: check-receipt.json — verdict + scope + concerns>
- /review: <RECEIPT: review-findings.json — findings count + severity>
- /doc-check: <RECEIPT: doc-check-result.json — pass/warn/block>
```

If any receipt file is missing → SHIP BLOCKED: "Missing receipt:
check-receipt.json. Run /check before shipping."

**What changes in /check and /review:**

Each skill writes a receipt file at the end of its run:

```json
// P:/.artifacts/<term>/<run-id>/check-receipt.json
{
  "verdict": "PASS",
  "concerns": 3,
  "tests_passed": 272,
  "tests_failed": 0,
  "scope": ["skills/ask/SKILL.md", "skills/handoff/SKILL.md"],
  "timestamp": "2026-08-03T..."
}
```

The receipt path is derived from session ID + run ID, matching the
`ship_run_id` already in the ship receipt.

## Disconfirmation

**What the research does NOT support:**

- **No source claims LLM-filled fields are sufficient.** Every enforcement
  approach found uses files, hooks, or CI — not agent self-reporting. This
  confirms the /ship gap is real and widely recognized.
- **Hooks can't enforce skill execution directly.** A Stop hook can check
  whether a receipt FILE exists, but it cannot force the agent to run `/check`.
  The enforcement is "block until receipt appears," not "make the agent run
  the skill." The agent still has to choose to run it — but it can't claim
  DONE without the receipt.
- **The `stop_hook_active` 8-block cap** means the gate can't loop forever.
  If the agent can't produce the receipt in 8 continuations, the session ends
  anyway. This is a known limitation, not a bug — it prevents infinite loops.
- **CI gates require push access and a remote.** For local-only work (like
  this session), the CI layer doesn't apply. The receipt files + Stop hook
  are the enforcement; CI is only for pushed work.

## Falsifier

This approach is wrong if:

- The receipt files become performative — the agent writes a receipt file
  with fabricated content (same as filling an LLM field with "not run").
  Mitigation: receipt files must contain machine-verified data (test counts
  from pytest output, lint results from ruff, file lists from git diff) —
  not agent-authored summaries.
- The Stop hook blocks legitimate session ends where /ship wasn't invoked.
  Mitigation: the hook only fires when the agent's last message contains
  "SHIP DONE" or the ship receipt path is referenced.
- Skills write receipt files but the content is wrong (e.g., /check writes
  a PASS receipt but didn't actually run tests). Mitigation: /check already
  runs tests mechanically — the receipt captures the pytest output, not the
  agent's claim about it.

## What we already have vs. what's missing

| Component | Status | Gap |
|-----------|--------|-----|
| `ship_receipt.py` | ✅ exists, mechanically verifies tests/lint/types/docs | Doesn't verify LLM-judgment fields — trusts the agent |
| Stop hooks | ✅ Grok Build supports them | No Stop hook checks for ship receipt existence |
| `/check` receipt output | ❌ /check writes a verdict to session output but not to a receipt file | Needs to write a structured receipt file |
| `/review` receipt output | ✅ /review writes FINDINGS.md to a run_dir | Already file-based — ship_receipt.py could read it |
| Work-trail validator | ❌ doesn't exist | `ship_receipt.py` could be extended to validate receipt files |
| CI gate | ❌ no CI on this workspace | Not applicable for local-only work |

## Reference

- Agentic OS `validate.sh` pattern: the work trail is the evidence, not the
  agent's report. This is the core transferable idea.
- Crosley's enforcement hierarchy: CLAUDE.md (probabilistic) → skills
  (probabilistic) → permissions (declarative) → hooks (guaranteed). Our /ship
  receipt is currently at the "skills" layer — it needs to move to "hooks."
- Claude Code `Stop` hook: exit 2 or `decision: "block"` prevents session end.
  The `stop_hook_active` flag prevents infinite loops (8-block cap).
- Daz (practitioner): "Anything that can be checked mechanically is enforced
  via hooks or automated verification steps, not by instructing the LLM."
