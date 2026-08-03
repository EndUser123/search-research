---
title: "Inference-in-Code Blind Spot"
created: 2026-08-02
source: session-2026-08-02
tags: [failure-mode, verification, code-quality, receipt-rule, structural-fix, behavioral-gate]
summary: >
  When writing external-sourced values into code, the agent treats "I read it
  in a document" as equivalent to "I verified it with a tool call." This is the
  same pattern as plausible-narratives-substitute-for-verification, but applied
  to data instead of narrative. Root cause: the agent chose not to use available
  tools, not missing tools or missing conventions. Primary fix: verify-before-write
  behavioral gate. Secondary fix: receipt-or-label convention for visibility.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/perplexity-quota-structure-pro-plan-2026.md
    type: related
  - target: wiki/concepts/tool-fallbacks.md
    type: related
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: related
---

# Inference-in-Code Blind Spot

## Decision context

**The problem:** when adding Perplexity to the fleet quota dashboard, I wrote pool sizes (300/25/25/25) and reset schedules into `fleet_quota.py` directly from the `perplexity-web-mcp` SKILL.md, which uses tilde-qualified estimates. I had `pwm usage` available — the authoritative CLI tool — and didn't run it before writing code. Each debugging round patched the display symptom instead of the data-source cause. It took 4 rounds of operator correction before actual research happened.

**The root cause (revised after /tp critique):** the tools needed (`pwm usage`, DDG search, Reddit MCP) were all available at the point of first writing the code. The failure wasn't missing capabilities — it was the agent's decision to treat "I read it in a SKILL.md" as equivalent to "I verified it with a tool call." This is the same pattern as `[[plausible-narratives-substitute-for-verification]]` but applied to data instead of narrative. Speed optimization (writing the guess is faster than running the command) reinforced this choice at each round.

## The failure pattern

1. Read a source with approximate numbers (SKILL.md says "~300/week")
2. Pattern-match to "I know this" — the tilde qualifier is dropped
3. Write the number into code as a bare constant — **this is the decision point**
4. When the output looks wrong, patch the display (remove fake bars) instead of verifying the data
5. Repeat until operator forces research

**Each patch is faster than research, so speed optimization selects against verification.** The decision not to verify happens at step 3, not at step 1. The fix must target step 3.

## Primary fix: verify-before-write behavioral gate

**Rule:** Before writing an external-sourced value into code, the agent must have a tool-call receipt from the current session that confirms the value. If it doesn't, it runs the verification tool first.

This targets the decision layer (step 3), not the write layer (post-write labeling). The receipt-or-label convention below is a secondary visibility improvement.

**How it would have caught the Perplexity incident:** before writing `pool = 300`, the agent would need a `pwm usage` receipt. Running `pwm usage` shows "Pro Search: 200 remaining" — the pool is 200, not 300. The error is caught at the write, not 4 rounds later.

**Implementation as AGENTS.md rule:** add to the hard rules section:

> Before writing an external-sourced numeric value into code (config constants, pool sizes, rate limits, thresholds from documentation), the agent must have verified that value with a tool call in the current session. If no verification receipt exists, run the verification command first. This is the code equivalent of the "Claims require receipts" rule.

## Secondary fix: receipt-or-label convention

Even with the behavioral rule, some values will be written without verification (time pressure, large code volumes). The receipt-or-label convention makes these visible:

**(a) Cite a verification receipt:**
```python
# verified: pwm usage --refresh, 2026-08-02 + wellstsai.com annual-plan report
POOLS = {"Pro Search": {"pool": 200, "reset": "rolling"}}
```

**(b) Be labeled as estimated with an upgrade path:**
```python
# ESTIMATED — from SKILL.md "~300/week". Verify via: pwm usage --refresh
POOLS = {"Pro Search": {"pool": 300, "reset": "weekly"}}
```

This is a visibility improvement, not a root-cause fix. It helps future readers (including future agent sessions) see which constants are verified and which are guesses.

## What this catches

- Pool sizes written from documentation without running the actual CLI
- Timeout values written from "common practice" without testing
- Rate limits written from blog posts without checking the API
- Any external-sourced constant that might be stale or wrong

## Broader instances (added 2026-08-03, session 019fbf77)

The pattern extends beyond code constants to **any artifact built on unverified external data**:

| Instance | Artifact type | What was unverified | Operator corrections needed |
|----------|--------------|---------------------|---------------------------|
| Perplexity quota (2026-08-02) | Code constants | Pool sizes from SKILL.md estimates | 4 rounds |
| Model notes UI (2026-08-03) | UI display data | 12 of 15 model notes from recall, not from picker table data that existed | 1 catch (all 12 fixed at once) |
| Reddit app (2026-08-03) | Capability claim | "Never registered" — the app existed at reddit.com/prefs/apps | 1 correction |
| upload_file CDP (2026-08-03) | Capability claim | "Blocked" — repeated from stale docs, never tested | 1 challenge |
| Grok Heavy (2026-08-03) | Feature assertion | "Available" — not on operator's subscription | 1 correction |

**The meta-pattern:** the agent treats "I recall this" or "I read this in docs" as equivalent to "I verified this with a tool call." The failure is the same whether the artifact is a code constant, a UI label, a capability claim, or a feature assertion — the decision to skip verification happens before the artifact is built.

**The picker-table incident is the most costly instance:** the verified data existed at `~/.grok/skills/model-web/SKILL.md` (Chrome DevTools picker inspection from 2026-08-01). The agent built the entire UI layer from inferred/recalled data instead of reading the verified source. 12 of 15 entries were wrong. The operator caught it in one pass, but the fix required re-doing the entire display layer.

## What this does NOT apply to

- Constants defined by the code's own logic (array sizes, loop bounds)
- Constants from the language spec or standard library (math.pi, sys.maxsize)
- Constants the developer authoritatively sets (config defaults they chose)

## Why the receipt convention alone is insufficient

A /tp critique (2026-08-02) identified that the receipt-or-label convention alone would NOT have prevented the Perplexity incident. The agent would write `# ESTIMATED` next to `pool = 300`, then move on. The label doesn't trigger research — it just labels the gap. The operator would still see wrong output and have to force research.

The primary fix (verify-before-write) catches the decision. The secondary fix (receipt-or-label) improves visibility for future readers. Both are needed; neither alone is sufficient.

## What this means for our workspace

1. **The AGENTS.md rule is the actionable output.** The "verify-before-write" behavioral gate should be added to the Hard Rules section. This is the structural fix that catches the decision, not just the symptom.

2. **fleet_quota.py should be audited.** All POOLS constants should either have `# verified:` receipts or `# ESTIMATED` labels. As of 2026-08-02, the Perplexity POOLS dict has verified values but no inline receipts — they're in the docstring.

3. **The /www confidence-gap mode concept extends to code.** When /www scans for `[INFERENCE]`/`[UNKNOWN]` items, the same concept applies to code writes: an unverified numeric constant is an implicit `[CODE_INFERENCE]`. A future hook could catch these mechanically.

4. **No new tools or skills are needed.** The failure was not missing capabilities — the tools (`pwm usage`, DDG, Reddit MCP) were available the entire time. The fix is behavioral, not infrastructural. See [[model-as-orchestrator]] for the agent-decision framing and [[research-applicability-checking-dont-cite-without-verifying-assumptions]] for the related verification gate concept.

## Receipts

- **Perplexity incident (4 rounds):** [FACT] Session transcript 019fbf77, turns L256-L491. The operator's corrections are visible in the user_query blocks. `pwm usage` was available from the start.
- **Root cause diagnosis:** [FACT] /tp critique inline session 2026-08-02. The critique identified that the tools were available but unused — grounded in conversation evidence.
- **Receipt-or-label insufficiency:** [INFERENCE] — the claim that the convention alone would not have prevented the incident is reasoned from the failure pattern, not empirically tested. The falsifier section acknowledges this.
- **Model notes incident (12/15 wrong):** [FACT] Session 019fbf77, commits 0e51f15 through b8391c0. The picker table data existed at `~/.grok/skills/model-web/SKILL.md` from 2026-08-01 DevTools inspection. The agent built the UI from recall instead of reading the verified source.
- **Reddit app "never registered":** [FACT] Session 019fbf77, operator corrected: the app existed at reddit.com/prefs/apps (Arindam200-mcp). The agent asserted non-existence without checking.
- **upload_file "blocked" claim:** [FACT] Session 019fbf77, agent repeated stale-doc claim without testing the CDP upload path. Marked [UNVERIFIED] after operator challenge.
- **Pattern identification:** [FACT] /tp improve session 019fbf77, 2026-08-03. The 4-dimension analysis identified this as the session's dominant failure pattern across efficiency, effectiveness, and thought-partnership dimensions.

## Falsifier

This concept is wrong if:
- The verify-before-write rule is consistently ignored in practice (no behavioral change)
- Code constants are never actually wrong (the pattern doesn't produce real bugs)
- A hook would be more effective than a behavioral rule (the rule is insufficient without enforcement)

## Sources

- Session 2026-08-02: Perplexity quota integration (4 rounds of operator correction)
- /tp critique session 2026-08-02: reframed the primary fix from write-layer to decision-layer
- AGENTS.md § "Claims require receipts" — the prose version of this rule
