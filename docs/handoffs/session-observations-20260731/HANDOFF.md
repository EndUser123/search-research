---
current_session_id: 019fb3a8-42b6-7e81-91c9-1fad5f4130e6
parent_handoff_path: none
status: CLOSED
---

# Session Observations — 2026-07-30/31

## Observations

1. **The meta-improvement loop works but requires operator challenges.** Each structural fix this session was triggered by an operator challenge. The framing check pattern mechanizes the most common challenge type (conflation check), but cannot replace the operator's judgment entirely. The agent cannot reliably challenge its own framing.

2. **"Ignore if not relevant" was a permission to dismiss.** Removing it changed the agent's behavior pattern — observations are now surfaced with confidence, not preemptively dismissed. Small wording change, large behavioral shift.

3. **Dual-stream routing is a generalizable pattern.** The knowledge/improvement split in /capture applies to any system that produces both durable findings and actionable items. Conflating them buries improvements in knowledge bases. This is the framing check's output-check question made concrete.

4. **Ship receipt automation is the next bottleneck.** The 15-field receipt template was too complex for reliable manual execution — this session produced duplicate lines, dangerous rollback commands, and N/A where "always runs" was specified. The mechanical receipt generator (ship_receipt.py) is the structural fix; it's specified but not built.

5. **Pattern reorder by specificity beats highest-match.** The /tp critique correctly identified that highest-match creates a gaming surface. Specificity ordering is simpler, safer, and sufficient. The fresh-lens critique was wrong about gaming (exit-code gate handles it) but right about the approach.

6. **The session spanned 2 calendar days and 2 git repos.** This is a common pattern on this host. The multi-repo ship detection (Phase 0 step 5) was added because this session shipped across P:\ and ~/.grok without structural coordination.

7. **Code-output passthrough: prose rules don't bind the generation pathway.** The agent was corrected 6+ times for narrating over script output. After /why + /tp analysis, three prose fixes were implemented and committed. The very next invocation narrated again. The structural fix was a PowerShell `quota` alias that bypasses the LLM entirely. See wiki concept `code-output-passthrough-narration-over-script-output.md`.

8. **The `quota` terminal alias is now the primary /model-quota invocation path.** Added `function quota { python "$env:USERPROFILE/.grok/skills/model-quota/scripts/fleet_quota.py" @args }` to the PowerShell profile. The skill SKILL.md remains for documentation and LLM-invoked use, but the terminal alias is the reliable path with ANSI colors and no narration.
