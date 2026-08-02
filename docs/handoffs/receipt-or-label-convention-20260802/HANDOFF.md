# Handoff: Verify-Before-Write Gate for Code Constants

## Status
OPEN — design + implementation needed

## Created
2026-08-02
## Revised
2026-08-02 (after /tp critique reframed the primary fix)

## Assignee
grok (fresh session)

## Problem

When the agent writes external-sourced numeric values into code (pool sizes, rate limits, thresholds from documentation), it treats "I read it in a SKILL.md" as equivalent to "I verified it with a tool call." The tools are always available — the failure is the decision not to use them. This caused 4 rounds of operator correction on the Perplexity quota integration (session 2026-08-02).

A /tp critique (2026-08-02) established that the originally-proposed fix (receipt-or-label comment convention) addresses the write layer but NOT the decision layer. The agent would write `# ESTIMATED` and move on — the label doesn't trigger research. The root-cause fix must target the decision: verify before writing.

## Two-track scope

### Track A: Primary fix — verify-before-write behavioral gate

**Rule:** Before writing an external-sourced value into code, the agent must have a tool-call receipt from the current session. If not, run the verification command first.

**Implementation options:**

1. **AGENTS.md hard rule** — add to "Hard rules" section: "Before writing external-sourced numeric values into code, verify with a tool call this session." Low enforcement, high coverage, immediate.

2. **PreToolUse hook on write/search_replace** — structural version of the rule. When a write contains a new numeric constant in a config-like context (dict literal, assignment), check whether the agent has a recent verification receipt for that value. If not, block with "This value appears to be from an external source. Have you verified it with a tool call this session?" High enforcement, needs design.

3. **Skill-step in /go or /preflight** — when implementing code that involves external data sources, the skill requires running the data source's CLI/API first and deriving all values from actual output. This was the "verify-before-code step" identified in the original meta-analysis (Change 2).

**Selection criterion:** optimal long-term — the solution that catches the most inference-in-code instances at the decision layer (not the write layer) with the least false-positive rate.

### Track B: Secondary fix — receipt-or-label convention

The comment convention stays as a visibility improvement for future readers. It does NOT replace Track A.

**Implementation:** AGENTS.md convention: "External-sourced numeric constants in code should cite `# verified: <tool+date>` or be labeled `# ESTIMATED — verify via: <command>`."

## Acceptance criteria

- [ ] AGENTS.md rule added (verify-before-write behavioral gate)
- [ ] AGENTS.md convention added (receipt-or-label for secondary visibility)
- [ ] PreToolUse hook designed (if option 2 is selected for Track A)
- [ ] `fleet_quota.py` audited — all POOLS constants have receipts or ESTIMATED labels
- [ ] Wiki concept `inference-in-code-blind-spot.md` updated (DONE — revised 2026-08-02 after /tp)

## Key files

- `C:/Users/brsth/.grok/AGENTS.md` — where the rule and convention go
- `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet_quota.py` — the file that triggered this
- `P:/.data/wiki/concepts/inference-in-code-blind-spot.md` — wiki concept (revised)
- `C:/Users/brsth/.grok/skills/go/SKILL.md` — if Track A option 3 (skill-step)

## Context

See session 2026-08-02 transcript, wiki concept `[[inference-in-code-blind-spot]]`, and the /tp critique that reframed the primary fix from write-layer to decision-layer.
