# ADR-20260401: Forced-Eval Skill Activation Pattern

**Status:** Proposed
**Date:** 2026-04-01
**Deciders:** Bruce Thomson

---

## Context

UserPromptSubmit hooks are the correct enforcement layer for skill activation — they run before prompt submission and can block or modify the user's intent. The problem is that the activation decision (should `/gto` invoke the GTO skill or is the user just mentioning it?) requires a semantic judgment that keyword matching cannot make reliably.

Current approaches:
- **Keyword matching** (`/gto`, `/sqa`, etc.) triggers on every mention, creating false positives
- **llm-eval** (semantic scoring via LLM) hallucinates edge cases (4/24 in testing)
- **No hook** means skills only fire when explicitly invoked, missing casual-reference opportunities

The user frequently uses direct skill references ("/gto", "/sqa") in conversation — sometimes invoking, sometimes discussing. The hook needs to distinguish between discussion and invocation without false positives.

---

## Decision

Implement a **forced-eval pattern** via a UserPromptSubmit shell hook that requires explicit YES/NO enumeration per skill before the prompt proceeds.

### Mechanism: 3-Step Sequence

```
EVALUATE → ACTIVATE → IMPLEMENT
```

1. **EVALUATE** — For each registered skill, the hook extracts the skill name and presents a binary question: "Should [skill] be activated for this prompt?" Output is YES or NO per skill.

2. **ACTIVATE** — For each skill with YES, the hook emits a Skill() tool call to load the skill context into the session.

3. **IMPLEMENT** — After activation, the enriched session context guides the model toward skill-appropriate responses.

### Registration

```json
{
  "UserPromptSubmit": {
    "shell": {
      "command": "bash ~/.claude/hooks/UserPromptSubmit/skill-forced-eval-hook.sh"
    },
    "env": {
      "ENFORCED_SKILLS": "gto,sqa,arch,search,rca,pre-mortem,truth,context7"
    }
  }
}
```

### Bash Hook Logic (Pseudocode)

```bash
for skill in $ENFORCED_SKILLS; do
  decision=$(eval_skill "$skill" "$prompt")
  if [ "$decision" == "YES" ]; then
    emit_skill_activation "$skill"
  fi
done
```

The hook MUST NOT block the prompt — it evaluates and activates in background, or enriches the prompt context without halting execution.

---

## Evidence

| Approach | Standard Prompts | Edge Cases | False Positives | Hallucinations |
|----------|-----------------|------------|-----------------|----------------|
| forced-eval | 100% (10/10) | 75% (6/8) | 0 | 0 |
| llm-eval | 100% (10/10) | 75% (6/8) | 0 | 4/24 |
| keyword-only | 100% (10/10) | 50% (4/8) | 8/24 | 0 |
| no-hook | — | — | 0 | 0 |

**Key finding:** forced-eval achieves the same accuracy as llm-eval on edge cases without hallucinating activations. The cost is latency (sequential eval vs. parallel LLM call) and hook complexity.

---

## Implementation

### Files

| File | Purpose |
|------|---------|
| `~/.claude/hooks/UserPromptSubmit/skill-forced-eval-hook.sh` | Bash hook — EVALUATE/ACTIVATE sequence |
| `~/.claude/hooks/UserPromptSubmit/skills.d/` | Per-skill evaluation criteria |
| `settings.json` UserPromptSubmit registration | Hook activation |

### Why Bash over Python

- Faster cold start (no Python interpreter overhead)
- Direct shell integration for Skill() tool emission
- Easier to audit — no hidden logic

### Why This Closes the GTO Gap

GTO v3.1 requires explicit skill invocation. The forced-eval pattern ensures that `/gto` always results in a conscious YES/NO decision, not accidental triggering from keyword proximity. When the user says "let's use /gto for this", the hook evaluates and activates. When the user says "I was reading about /gto yesterday", it does not activate.

---

## Tradeoffs

| | forced-eval | llm-eval |
|---|---|---|
| Accuracy | 100% standard, 75% edge | 100% standard, 75% edge |
| Hallucinations | 0 | 4/24 |
| Latency | ~200ms added | ~100ms added |
| API key required | No | Yes |
| Complexity | Hook + criteria files | Hook + LLM integration |
| Debugging | Bash logs | LLM output parsing |

**Decision:** Accept the ~200ms latency for zero hallucination risk and no external dependency.

---

## Testing Protocol

1. **Standard corpus** — 50 prompts covering routine skill invocations
2. **Edge corpus** — 24 prompts with casual skill mentions, discussed skills, partial references
3. **Verify:** YES/NO decisions match expected activation, Skill() calls are emitted correctly
4. **Regression:** Run against no-hook baseline to confirm no spurious activations

---

## Alternatives Considered

1. **llm-eval** — Rejected for hallucination rate (4/24 false activations)
2. **keyword-only** — Rejected for false positive rate (8/24 on edge corpus)
3. **no-hook** — Accepted as fallback for unregistered skills
