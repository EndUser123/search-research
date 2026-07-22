---
thread_id: f2aeee3e-7664-45d6-a56e-275c9c8825d8
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-21T23:30:00Z
status: open
handoff_type: implementation
assigned_to: unassigned
accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: Stop hook for fabrication enforcement

## 1. Objective (one sentence)

Build a `Stop` hook that mechanically blocks responses containing causal claims without verification receipts, replacing the 5 advisory rules that have repeatedly failed to prevent fabrication.

## 2. Status

**Not started.** Root cause identified and fix designed this session. No implementation.

## 3. What's verified (with receipts)

**The problem is structural, not informational:**

| Anti-fabrication mechanism | Built when | Prevented DiffusionGemma fabrication? |
|---|---|---|
| Verification receipt rule (AGENTS.md) | 2026-07-20 | ❌ No |
| `/tp` Mode 7 (fabricated causal chain) | 2026-07-20 | ❌ No |
| Wiki concept `fabricated-causal-chain-receipt-required.md` | 2026-07-21 | ❌ No |
| Testing methodology `both-outcomes-informative.md` | 2026-07-21 | ❌ No (written and violated in same session) |
| Evidence-first default rule | 2026-07-20 | ❌ No |

Five advisory mechanisms failed to prevent a single fabrication incident. The pattern: documentation-layer fixes for an enforcement-layer problem.

**The specific incident that triggered this handoff:**
- I tested DiffusionGemma via `spawn_subagent` → got 400 empty-content errors
- Concluded "DiffusionGemma fails on real tasks" (stated as fact, no layer isolation)
- This conclusion was wrong — the model works fine via direct API
- It took user pushback ("you should not be getting api errors") to trigger the isolation test
- ~3 hours of session time lost between false conclusion and correction
- The false conclusion prevented me from building batch mode (eliminated it from possibility space)

## 4. The designed fix

**A `Stop` hook** that scans the response before it ships:

**Detection:** regex or LLM-based scan for causal claims:
- "X causes Y"
- "X fails on"
- "X doesn't work"
- "The problem is X"
- "Root cause: X"
- "X is broken"

**Verification check:** for each detected causal claim, check the preceding 3 turns for:
- A tool call (read_file, grep, run_terminal_command) whose output directly confirms the claim
- A file citation with line number
- A command output

**Enforcement:**
- If causal claim + receipt found → allow (PASS)
- If causal claim + no receipt → block, require either:
  - A receipt (cite the tool call/file/command), OR
  - A relabel (`[INFERENCE]` or `[UNKNOWN]` instead of stated-as-fact)
- If no causal claims → allow (PASS, no overhead)

**Why a hook, not another rule:** hooks are mechanical enforcement — they can't be skipped in the moment. Rules are advisory — they are routinely skipped under context pressure or when the conclusion "feels right."

## 5. Implementation notes

**Hook type:** `Stop` (runs before the response is shown to the user)
**Location:** `P:/.claude/hooks/` (Claude-side) or `~/.grok/hooks/` (Grok-side)
**Host:** This must work on Grok Build. Check `~/.grok/docs/user-guide/` for the Stop hook shape on this host.

**Key design decisions for the implementer:**
1. **Regex vs LLM for detection:** regex is faster but misses paraphrased claims; LLM is more accurate but adds latency and cost. Start with regex for the obvious patterns, add LLM for ambiguous cases.
2. **Receipt lookup:** the hook needs access to the conversation's tool-call history. Check how other Stop hooks (e.g., `Stop_diagnostic_analysis_quality_gate`) access this.
3. **Block vs warn:** the user's preference (from session evidence) is enforcement, not advisory. The hook should block (exit code 2), not just warn.
4. **Whitelist:** some causal claims are legitimately inferential (e.g., "this pattern suggests X"). The hook should allow claims explicitly labeled `[INFERENCE]` or `[UNKNOWN]`.

## 6. Resumption protocol

1. Read `P:/.data/wiki/concepts/fabricated-causal-chain-receipt-required.md` for the receipt rule's full specification
2. Read `P:/.data/wiki/concepts/testing-methodology-both-outcomes-informative.md` for the layer-isolation principle
3. Read `~/.grok/AGENTS.md` "Verification receipt rule" section
4. Check existing Stop hooks in `P:/.claude/hooks/` for the hook shape and patterns
5. Design the detection regex/LLM prompt
6. Implement the hook
7. Test with a fabricated claim (should block) and a verified claim (should pass)
8. Follow the plugin mutation checklist if this becomes a plugin hook

## 7. Related artifacts

- Plan: none (design is in this handoff)
- Wiki concepts: `fabricated-causal-chain-receipt-required.md`, `testing-methodology-both-outcomes-informative.md`
- AGENTS.md rules: "Verification receipt rule", "Mandatory Preflight"
- Existing hooks to reference: `Stop_diagnostic_analysis_quality_gate`, `StopHook_unverified_stance`, `Stop_fake_done_detector`

## 8. Open questions

- Should the hook use regex-only (fast, cheap, misses paraphrases) or regex+LLM (accurate, adds latency)?
- Should it scan ALL responses or only responses that contain trigger phrases?
- How does it access tool-call history on Grok Build specifically? (Need to verify hook API)
- Should it be a Claude-side hook (`.claude/hooks/`) or Grok-native (`~/.grok/hooks/`)?
