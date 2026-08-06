---
title: "Existing Infrastructure Bypass Pattern"
created: 2026-08-02
source: session-019fc313
tags: [failure-mode, design-pattern, enforcement, hook-design, structural-fix]
summary: >
  When building a new enforcement mechanism, the agent invents a parallel system
  without checking whether existing infrastructure already solves the problem
  (partially or fully). The new system is structurally weaker than what already
  exists. Root cause: the agent didn't run observe-before-propose (grep for
  existing implementations before building). This is the enforcement-mechanism
  analog of "replacement-before-investigation."
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/inference-in-code-blind-spot.md
    type: related
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: instance-of
---

# Existing Infrastructure Bypass Pattern

## The pattern

When asked to design or build an enforcement mechanism (hook, gate, linter), the agent:

1. Designs a new system from scratch
2. Implements it with novel mechanisms (new annotation contracts, new state files, new detection logic)
3. Does NOT check whether existing workspace infrastructure already provides the same capability
4. Ships the new system as a parallel path alongside the existing one

The result: two systems doing the same job, one weaker than the other. The weaker system (the new one) gets used because it was the one just built, while the stronger system (the existing one) continues to be ignored.

## Reference incident (2026-08-02)

The verify-before-write PreToolUse hook was designed to enforce receipt-checking for external-sourced code constants. It invented an inline-annotation contract (`# verified:`, `# ESTIMATED`) that is an **assertion** — the agent claims a receipt exists, but the hook cannot verify the claim.

The workspace already has `verification_receipt_writer.py` (PostToolUse) → `quality_gate.py` (Stop) — an **authoritative** receipt pipeline that produces file-fingerprint-bound `VERIFICATION_SUCCEEDED` records. The new hook bypassed this entirely.

The existing pipeline doesn't cover config constants today, but the extension is ~15-30 lines (add `pwm usage` to the pattern catalog, have the hook consume receipts instead of annotations). The new hook is 265 lines.

**The /tp fresh-lens subagent found this by reading the hooks directory — something neither the design author nor the 7 red-team specialists did.** No specialist was scoped to ask "does existing infrastructure already solve this?"

## Why this happens

1. **Design-first instinct** — the agent starts designing before observing. The `observe-before-propose` rule exists but doesn't fire for "build me X" requests.
2. **No preflight for hooks** — the preflight skill checks for existing implementations, callers, registrations. But it wasn't run before designing the hook.
3. **Specialist scope allocation** — red-team specialists are scoped by attack surface (correctness, security, performance, etc.). None are scoped to ask "does the workspace already have this capability?" That's a discovery/preflight question, not an adversarial-review question.

## How to prevent it

1. **Run `/preflight` before designing any enforcement mechanism.** The preflight inventory would have surfaced `verification_receipt_writer.py` because it's registered in `quality-gate.json` and the grep would find "verify" + "receipt" patterns.
2. **Add a "reuse check" to the design process.** Before proposing a new mechanism, grep the hooks directory and scripts directory for related capabilities. This is the same rule as `observe-before-propose` but scoped to enforcement infrastructure.
3. **Scope a red-team specialist to "existing infrastructure."** One specialist should ask: "does the workspace already have a system that does this? Is the proposed system reinventing it?"

## What this catches

- Any new hook/gate/linter that duplicates existing enforcement
- Any new annotation contract that duplicates existing receipt/state infrastructure
- Any new detection logic that duplicates existing scanner/validator patterns

## What this does NOT apply to

- Greenfield capabilities (no existing infrastructure to bypass)
- Cases where the existing infrastructure was checked and explicitly rejected (cite the rejection reason)

## Falsifier

This concept is wrong if:
- The existing infrastructure is always insufficient for new use cases (the bypass is justified)
- Preflight before hook design doesn't change the outcome (the existing system is still bypassed)
- The pattern is session-specific and doesn't recur

## Sources

- Session 2026-08-02: verify-before-write hook design
- /tp critique session 2026-08-02: fresh subagent found `verification_receipt_writer.py`
- See handoff: `docs/handoffs/verify-before-write-hook-design-review-20260802/HANDOFF.md`
