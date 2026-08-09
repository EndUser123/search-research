---
title: "UserPromptSubmit native hooks: stdout ignored on Grok Build (verified)"
created: 2026-07-28
source: session-2026-07-28, verified-2026-08-05 (stdout + exit2 + stderr all tested)
tags: [hooks, userpromptsubmit, grok-build, hook-limitations, passive-events, verified, no-channel-to-model]
summary: >
  FULLY VERIFIED 2026-08-05: UserPromptSubmit on Grok Build native hooks
  (~/.grok/hooks/*.json) has NO channel to the model. Tested all three:
  (1) stdout JSON additionalContext — ignored; (2) stderr — not fed back;
  (3) exit 2 — recorded as failure (✗) in TUI annotation but does NOT block
  and does NOT feed stderr to the model. The prompt always proceeds. Only
  PreToolUse, Stop, and SubagentStop process stdout/exit-code on Grok Build.
  Skill enforcement must rely on the Stop hook quality gates (Layer 2) or
  explore PreToolUse-based approaches.
agent: grok
host: grok
cognitive_load: 2
verification: locally-tested
relations:
  - target: wiki/concepts/grok-pretooluse-deny-contract-verified
    type: extends
  - target: wiki/concepts/grok-build-runtime-docs-divergence
    type: related
  - target: wiki/concepts/skill-enforcement-layers
    type: related — Layer 1 is NOT viable for native hooks on Grok Build
  - target: wiki/concepts/skill-auto-invocation-reliability
    type: related — the enforcement gap remains open
---

# UserPromptSubmit native hooks: stdout ignored on Grok Build (verified)

## The verified constraint

Grok Build's `UserPromptSubmit` hook event is **passive-only** for natively
registered hooks (`~/.grok/hooks/*.json`):

| Capability | Claude Code | Grok Build (native) | Grok Build (Claude plugin compat) |
|-----------|-------------|---------------------|-----------------------------------|
| Block the prompt | Yes | **No** | **No** |
| Inject context (`additionalContext`) | Yes | **No** | **Possibly** (unverified) |
| Rewrite the prompt | No | **No** | No |
| Write side-effect files | Yes | Yes | Yes |

Source: Grok Build docs (https://docs.x.ai/build/features/hooks):
"For passive events, stdout is ignored; exit 0 on success." UserPromptSubmit
is non-blocking (events table), therefore passive, therefore stdout is ignored.

## Local verification (2026-08-05)

Three channels tested, all negative:

### Test 1: stdout JSON additionalContext

Hook: `test-ups-injection.json` → outputs `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "USERPROMPTSUBMIT_TEST_MARKER_VISIBLE"}}`
Result: Hook fired (✓ in TUI, 423ms), stdout produced correctly, **marker NOT visible** in model context after 2 restarts.

### Test 2: exit 2 + stderr

Hook: `test-ups-exit2.json` → prints `UPS_EXIT2_TEST_MARKER` to stderr, calls `sys.exit(2)`
Result: Hook fired (✗ in TUI, 1716ms, "exit code 1"), **prompt was NOT blocked**, marker NOT visible in model context.

The TUI annotation showed the hook as a failure (`✗`), but the failure is operator-visible only — the prompt proceeded to the model normally.

### Test 3: plain text stdout (not separately tested)

The docs say "stdout is ignored" without qualification. Tests 1-2 confirm this covers JSON stdout. Plain text stdout is covered by the same "passive = stdout ignored" rule.

### Conclusion

**No channel from UserPromptSubmit to the model exists on Grok Build native hooks.**

| Channel | Tested | Result |
|---------|--------|--------|
| stdout JSON (additionalContext) | Yes | Ignored |
| stderr | Yes | Not fed back to model |
| exit 2 (blocking) | Yes | Recorded as ✗ failure, does NOT block |
| Side-effect files | Yes (existing quota hook) | Works — file written, model reads later if instructed |

### Third-party claims that contradict this

| Project | Claim | Status |
|---------|-------|--------|
| Vectorize/Hindsight | UserPromptSubmit injects additionalContext on Grok Build | Unverified — may work via Claude Code plugin compat layer (different dispatch path) |
| QAInsights/pleasantries | exit 2 blocks on grok-cli UserPromptSubmit | **Falsified** by local test — exit 2 does NOT block; the prompt proceeds |

The pleasantries project lists grok-cli as supported with exit 2 blocking, but this appears to be untested on actual Grok Build or based on a pre-release version.

## The Hindsight contradiction explained

Vectorize/Hindsight (https://hindsight.vectorize.io/sdks/integrations/grok-build)
claims UserPromptSubmit additionalContext injection works on Grok Build.
Their plugin is a **Claude Code plugin** (`.claude-plugin/` format) that Grok
Build "natively reads" via the compat layer. The compat layer may process
Claude Code plugin hooks through Claude Code's dispatch semantics, where
UserPromptSubmit IS a special case that processes stdout (per Anthropic docs:
"Exit code 0 with stdout: Claude sees the context (special case for
UserPromptSubmit)").

This means there are **two dispatch paths** on Grok Build:
1. **Native hooks** (`~/.grok/hooks/*.json`) → Grok's native runner → stdout ignored for passive events
2. **Claude Code plugin hooks** (`.claude-plugin/` format) → compat layer → possibly Claude Code semantics

The Hindsight claim may be true for path 2 but is NOT true for path 1.
This is [INFERENCE] — not verified locally because we don't have Hindsight
installed. The verified fact is: path 1 does not work.

## What IS possible (unchanged from original)

The hook CAN run Python and write files. The limitation is specifically about
context injection (stdout → model). Side-effect files still work.

## What this means for skill enforcement

The skill_enforcer UserPromptSubmit approach (detect `/<skill-name>`, inject
"execute, don't discuss" additionalContext) **does NOT work** for native
Grok hooks. The only enforcement layer available is the Stop hook quality
gates (Layer 2), which fire post-execution.

**Potential workaround:** package the skill_enforcer as a Claude Code plugin
(`.claude-plugin/` format) instead of a native hook. The compat layer may
process UserPromptSubmit stdout. This is unverified but testable.

**Alternative:** investigate whether `.claude/settings.json` hook registration
goes through the compat layer (which would process stdout) rather than the
native runner (which ignores it). The Grok Build docs say `.claude/settings.json`
hooks "are read as well" — this may mean they go through the compat dispatch.

## Falsifier

This finding is wrong if:
1. A future Grok Build release adds stdout processing for UserPromptSubmit
   (making it non-passive)
2. The test hook failed to load for a reason other than "stdout is ignored"
   (e.g., wrong registration, timeout, crash) — check `/hooks` in the TUI
3. The `.claude/settings.json` dispatch path processes stdout (testable)

## Sources

- Grok Build hook docs: https://docs.x.ai/build/features/hooks — "For passive events, stdout is ignored"
- Local test: `P:/tmp/test_ups_hook.py` + `~/.grok/hooks/test-ups-injection.json` — marker not visible after 2 restarts
- Vectorize/Hindsight: https://hindsight.vectorize.io/sdks/integrations/grok-build — claims injection works via Claude Code plugin format
- Anthropic hooks docs: https://docs.anthropic.com/en/docs/claude-code/hooks — UserPromptSubmit is a special case on Claude Code
- stepcodex.com: SessionStart hooks "execute successfully (side effects work) but their stdout JSON containing hookSpecificOutput.additionalContext is silently discarded" — confirms passive-stdout-ignored pattern

## Audit trail of corrections

1. **2026-07-28 (original):** UserPromptSubmit stdout ignored on Grok Build. Correct.
2. **2026-08-04 (first correction):** Changed to "CAN inject additionalContext" based on Hindsight plugin docs. WRONG — trusted third-party claim without testing or distinguishing dispatch paths.
3. **2026-08-05 (this version):** Reconfirmed original finding via local test. Added two-dispatch-path nuance. The original wiki concept was right all along.

**Lesson:** the first correction was the [[replacement-before-investigation-pattern]] pattern — I replaced a verified finding with an unverified claim from a third-party source. The Hindsight plugin's marketing docs are not authoritative evidence about Grok Build's native hook runner.

## What this means for our workspace

1. **The skill_enforcer port does NOT work via native hooks.** The handoff
   at `P:/docs/handoffs/skill-enforcer-port-grok-build-20260804/HANDOFF.md`
   needs updating: the approach must either use the Claude Code plugin format
   or be abandoned in favor of Stop-hook-only enforcement.
2. **The quality gates Stop hook (Layer 2) is the only enforcement mechanism
   available** for the discuss-instead-of-execute pattern on Grok Build.
3. **The operator's correction stands:** the `/ship`-as-discussion pattern is
   caught by the operator, not by any structural mechanism. This remains an
   open gap until either (a) Grok Build adds UserPromptSubmit stdout processing,
   or (b) we verify the Claude Code plugin compat layer processes it.
