# Handoff: Premature recommendation pattern — investigate before replacing

**Status:** OPEN — behavioral pattern, not yet mechanically enforced  
**Created:** 2026-08-01  
**Source session:** 019fb177-e5d5-7520-92f5-0158f87639c9  
**Severity:** High — recurring across 13+ handoffs

## Objective

The agent has a recurring behavioral pattern: when encountering a tool/feature that doesn't work perfectly on first use, it recommends replacing it with an alternative rather than investigating why it failed or trying workarounds. This wastes operator time, produces unreliable recommendations, and erodes trust.

The specific instance that triggered this handoff: agy (Antigravity CLI) timed out at 300s on long analytical prompts during /tp parallel panel reviews. The agent immediately recommended:
1. Increasing the timeout (treating the symptom)
2. Replacing agy with direct Gemini API calls (bypassing the paid subscription)
3. Dropping agy entirely

Before trying:
- `--output-format stream-json` (avoids the broken polling mechanism)
- `--effort medium` (reduces thinking block length)
- A Python wrapper around the stream (preserves context firewall)
- Verifying whether the bug actually triggers on structured markdown prompts (vs high-entropy garbage)

The agent also fabricated a claim ("Gemini API free tier has lower context length limits") to justify the replacement, then admitted it was wrong when challenged.

## Evidence this is a recurring pattern

13 handoffs contain related patterns (premature conclusions, unverified assumptions, replacement-before-investigation):

- `anti-fawning-opportunity-20260726` — agent manufactured urgency
- `diagnostic-claim-gate-20260725` — agent claimed without verification
- `session-observations-20260720-019f7e24` — assumed without testing
- `why-skill-enhancement-20260725` — recommended before investigating
- Plus 9 others with similar language

Related wiki concepts:
- `[[fabricated-causal-chain-receipt-required]]`
- `[[behavioral-compliance-gap-agent-skips-instructed-steps-without-verifying]]`

## Acceptance criteria

1. The pattern has a name and is documented in a wiki concept
2. There is a mechanical check (hook or skill instruction) that fires when the agent recommends replacing a tool before exhausting investigation of the current one
3. The /tp SKILL.md or AGENTS.md contains a standing rule: "before recommending replacement, enumerate what workarounds have been tried"
4. The agy stream-json wrapper is built and tested (the concrete deliverable)

## Tasks

### Task 1: Build agy stream-json wrapper
**File:** `~/.grok/skills/tp/__lib/agy_lens.py`  
**Pattern:** Same as `dgemma_read.py` — Python subprocess captures agy's stream-json output, extracts `agent_message` text, writes to file. Context firewall preserved.  
**Test:** Run a /tp-sized prompt (30K+ tokens) through the wrapper. Verify it completes without timeout and produces clean critique output.  
**Status:** Not started

### Task 2: Document the behavioral pattern as a wiki concept
**File:** `P:/.data/wiki/concepts/replacement-before-investigation-pattern.md`  
**Content:** The pattern, evidence (this session + 13 related handoffs), falsifier, and the standing rule. Cross-reference to `[[fabricated-causal-chain-receipt-required]]` and `[[behavioral-compliance-gap-agent-skips-instructed-steps-without-verifying]]`.  
**Status:** Not started

### Task 3: Add standing rule to AGENTS.md or /tp SKILL.md
**Content:** "Before recommending that a tool, service, or skill be replaced with an alternative, enumerate: (1) what was tried with the current tool, (2) what workarounds exist that haven't been tested, (3) whether the failure was verified on our actual workload vs a different context. If any of these is unanswered, the recommendation is premature."  
**Status:** Not started

### Task 4: Audit the 13 related handoffs
**Content:** Cluster by root cause. Check whether prior fixes addressed the cluster or just individual instances. Goal: does the pattern trend down after each fix?  
**Status:** Not started

## Constraints

- Do NOT recommend replacing agy with direct API. Use agy properly first.
- The stream-json approach is the primary fix. Direct API is a fallback, not a replacement.
- The behavioral pattern is the meta-issue; the agy wrapper is one instance of it.
