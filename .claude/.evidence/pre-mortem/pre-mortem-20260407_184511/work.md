skill-guard fix: Modified P:/packages/skill-guard/src/skill_guard/skill_forced_eval.py line 561

Changed from:
  return HookResult(context=instruction, tokens=token_count, priority=0.5)

Changed to:
  return HookResult(context={'systemContext': instruction}, tokens=token_count, priority=0.5)

Purpose: Hide 'SKILL EVALUATION REQUIRED' enumeration from users while preserving forced evaluation mechanism for LLM. The enumeration is internal guidance for skill selection (84% activation rate vs 20% without).

Context: User complained about seeing verbose skill enumeration. Investigation revealed the enumeration was meant for LLM, not user. Fix uses systemContext field (internal-only) instead of additionalContext (user-visible).

Also restored P:/.claude/hooks/UserPromptSubmit_modules/skill_metadata_advisory.py from .disabled status.
