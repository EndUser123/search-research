---
created: '2026-04-12'
sources:
- C:\Users\brsth\Downloads\solo_operator_adr_best_practices.md
summary: ''
tags: []
---


# ADR BEST PRACTICES FOR SOLO OPERATORS
## (Stakeholder Roles Don't Apply; Decision Lifecycle & Future-Self Do)

---

## The Core Problem with Standard ADR Guidance

Enterprise ADR frameworks (Microsoft, AWS, TOGAF) assume:
- Multiple stakeholders (need role clarity: Driver, Approver, Consulted, Informed)
- Governance gates (need approval workflows)
- Team handoffs (need explicit accountability)
- Organizational compliance (need audit trails)

**None of this applies to you.**

You are solo. This changes what matters.

---

## What DOES Matter for Solo ADRs

### 1. Decision Shelf Life (Critical for Solo)

**The Problem**: As a solo operator, you make 100+ decisions per year. In 12 months, you'll forget:
- Why you chose Bifrost over LiteLLM
- What problem was being solved
- What alternatives you rejected and why
- What assumptions were in place

**When you revisit the decision 8 months later**, you'll waste 2-3 hours re-discovering your own reasoning.

**Solution: Document shelf life explicitly**

```toml
# ADR #1: Bifrost vs. LiteLLM

Status: Accepted
Created: 2026-04-12
Shelf Life: 6 months (mark for review: 2026-10-12)
Context Window: When reviewing, check:
  - LiteLLM security status (was compromised March 24, 2026)
  - Bifrost performance benchmarks
  - New gateway entrants (any new tools since April?)
```

**Why 6 months?** Long enough that you'll have actual usage data. Short enough that you haven't forgotten why.

### 2. Assumptions at Risk (Critical for Solo)

**The Problem**: Assumptions break silently. You make a decision based on 6 assumptions, and if 1 breaks, the whole decision becomes invalid. But you won't remember the assumptions were there.

**Solution: Explicit "If X changes, revisit this ADR"**

```toml
# ADR #1: Bifrost Routing

Assumptions (if any break, revisit this decision):
  ✓ ASSUMPTION: LiteLLM remains compromised (security signal)
    IF: LiteLLM releases clean version + fixes audit, THEN: reconsider
    Likelihood: Low (but check monthly)

  ✓ ASSUMPTION: Bifrost stays <15ms latency overhead
    IF: Bifrost pushes >50ms overhead, THEN: switch to direct API routing
    Likelihood: Low (Go binary is performant)
    Monitor: Run latency benchmark quarterly

  ✓ ASSUMPTION: You have 6+ providers to manage
    IF: You consolidate to 1-2 providers, THEN: Bifrost complexity not justified
    Likelihood: Medium (budget constraints may force consolidation)
    Action: Track provider spend monthly

  ✓ ASSUMPTION: Windows 11 + PowerShell stays your primary environment
    IF: You migrate to Linux, THEN: Ollama becomes primary (Bifrost still works)
    Likelihood: Low (stated no WSL/Docker preference)
    Action: Document any OS migration implications
```

### 3. Temporal Decay (Critical for Solo)

**The Problem**: Decisions decay over time. A decision made in April 2026 is still valid in May. By August, it's questionable. By December, it might be obsolete.

**Solution: Explicit "review on date X" + "versioning for context"**

```toml
# ADR #1: Bifrost Routing

Created: 2026-04-12
Next Review: 2026-10-12 (6 months)
Review Triggers:
  - Quarterly latency benchmark (check if <15ms still holds)
  - Whenever Google/Mistral/Anthropic change pricing (breaks cost model ADR)
  - If you encounter Bifrost crashes (2+ in a month = revisit reliability)
  - New gateway tool released (evaluate once per quarter)

Version History:
  v1.0 (2026-04-12): Initial decision (Bifrost chosen over LiteLLM)
    - Context: LiteLLM compromised 2026-03-24
    - Confidence: High (security signal is clear)

  [v2.0 would go here if decision is revisited and changed]
```

### 4. Personal Debugging (Critical for Solo)

**The Problem**: Solo operators need to debug their own decisions. If something breaks (Bifrost crashes, costs explode, `/vibe` command fails), you need to know:
- Was this foreseeable?
- Is this a known risk?
- What's the immediate fallback?
- Do I need to revisit this ADR?

**Solution: Explicit "known failure modes" + "fallback strategy"**

```toml
# ADR #1: Bifrost Routing

Known Failure Modes:
  1. Bifrost daemon crashes
     - Detection: Gemini CLI throws "connection refused"
     - Recovery: net stop Bifrost && net start Bifrost (30s, manual)
     - Permanent fix: Check Windows Task Scheduler logs
     - Temporary fallback: Use direct API (slower, set ANTHROPIC_BASE_URL to api.anthropic.com)
     - Acceptable duration: <5 min per incident. If >2 incidents/month, revisit

  2. API key expires or gets revoked
     - Detection: Bifrost logs show "401 Unauthorized" from provider
     - Recovery: Re-enter key in Bifrost web UI (localhost:8080)
     - Temporary fallback: Use Ollama local model (zero API calls)
     - Acceptable duration: Know these by heart. Will happen every 90 days

  3. Bifrost routing sends request to wrong provider (config error)
     - Detection: Model output doesn't match expected model style
     - Recovery: Check ~/.bifrost/config.yaml, verify model aliases
     - Root cause: Usually typo in alias name
     - Acceptable duration: 5-10 min to debug, embarrassing but non-critical

Cost Explosion Scenario:
  - Trigger: Monthly bill jumps from $30/mo to $150/mo
  - Likely cause: Accidentally using Gemini 3 Pro (expensive) instead of Flash (cheap)
  - Detection: Check which model you've been invoking
  - Recovery: Reset GEMINI_MODEL environment variable
  - Prevention: Document which models are "expensive" vs. "cheap" in this doc
```

### 5. Cost Tracking (Critical for Solo - Budget Conscious)

**The Problem**: You operate on a fixed budget. ADRs that recommend "$20/mo Gemini Pro + $50/mo API budget" need to be **monitored continuously** because if costs drift 20% over, the entire cost-model ADR becomes invalid.

**Solution: Explicit cost tracking + monthly review process**

```toml
# ADR #4: Hybrid Subscription + BYOK Cost Model

Budget: $50-100/mo (target: $75/mo average)

Monthly Tracking (1st of every month):
  Review file: ~/.gemini/cost_log.txt
  Check:
    - Gemini Pro $20/mo (fixed)
    - OpenRouter spend (check dashboard)
    - Groq spend (usually $0, free tier)
    - Cohere spend (check API usage)
    - Ollama spend (always $0, local)
    - Total: sum all above

  Decision rules:
    - IF total < $60/mo: Continue as-is (under budget)
    - IF $60-80/mo: Continue as-is (on target)
    - IF $80-100/mo: Yellow flag. Review which task types are expensive. Consider:
      * Switch more tasks to Ollama (local, free)
      * Use cheaper models (Claude Haiku instead of Claude Opus)
      * Reduce agentic loop frequency
    - IF >$100/mo: Red flag. Revisit ADR #4 entirely. Possible actions:
      * Pause Claude API, use Gemini Pro only
      * Cut OpenRouter, use Groq free tier only
      * Increase Ollama usage (might need hardware upgrade)

Actual Spend History (fill in monthly):
  2026-04: $72 (initial setup month, likely higher)
  2026-05: $__ (track after Phase 1 complete)
  2026-06: $__ (track after Phase 2 complete)
  2026-07: $__ (track after Phase 3 complete)
  ...

If actual > predicted by 20%, document why:
  - Did you use more agentic loops than expected?
  - Did a provider raise pricing?
  - Did your task mix change (more expensive tasks)?
```

### 6. Reversibility (Critical for Solo)

**The Problem**: If a decision goes wrong and you need to revert, solo operators can't call a meeting—you just need to know how to quickly undo it.

**Solution: Explicit "how to revert" instructions**

```toml
# ADR #1: Bifrost Routing

How to Revert (if decision fails):
  Scenario: Bifrost becomes unreliable (>2 crashes/month)

  Step 1: Keep Gemini CLI, remove Bifrost
    - Set environment variables back to defaults:
      $env:ANTHROPIC_BASE_URL = ""  (clear override)
      $env:ANTHROPIC_AUTH_TOKEN = "sk-ant-..."  (direct Anthropic key)
      $env:ANTHROPIC_MODEL = "claude-3-7-sonnet"

  Step 2: Remove Bifrost from Windows Service Manager
    - sc delete Bifrost

  Step 3: Stop relying on hot-swap (use CLI flags instead)
    - Instead of: gemini (uses cached model)
    - Use: gemini -m openrouter/mistral-large  (explicit per-call)

  Time to revert: 5 minutes, zero data loss

  Cost impact: Revert increases spend (no context caching, per-request pricing), 
              but you're only reverting if Bifrost is broken, so worth it

Partial Revert (if only one component fails):
  - If Bifrost crashes but Ollama is fine:
    Use Ollama as sole provider (free, local, temporary)
    Gives you time to fix Bifrost without rush
```

---

## What to Actually Include in Your ADRs (Solo Version)

### Essential (Do This)
- [ ] **Problem**: What was the trigger?
- [ ] **Options**: What did you consider? (2-3 is fine, don't over-analyze)
- [ ] **Decision**: What did you choose and why?
- [ ] **Shelf Life**: When should you revisit? (6-12 months typical)
- [ ] **Assumptions at Risk**: What would make this decision invalid? (4-6 items)
- [ ] **Known Failure Modes**: What breaks, and what's the quick fix?
- [ ] **How to Revert**: If this fails, what's the undo?

### Nice-to-Have (Do If Easy)
- [ ] **Cost Impact**: Does this affect your budget?
- [ ] **Confidence Level**: How sure are you? (High/Medium/Low)
- [ ] **Timeline**: Any phases/milestones?

### Skip (Not Relevant to Solo)
- ✗ Stakeholder roles (Driver, Approver, Consulted, Informed)
- ✗ Governance gates / approval workflows
- ✗ Compliance audit trails
- ✗ Enterprise change management processes
- ✗ Formal communication plans

---

## Quick Template for Solo ADRs

```markdown
# ADR #X: [Decision Title]

## Problem
[What drove this decision? What was broken or missing?]

## Options Considered
- **Option A**: [Name] - Pros: [...] Cons: [...]
- **Option B**: [Name] - Pros: [...] Cons: [...]
- **Option C**: [Name] - Pros: [...] Cons: [...]

## Decision
**Chosen**: Option [X]
**Why**: [1-2 sentences of core reasoning]

## Shelf Life & Review Triggers
- Next Review: [Date 6-12 months from now]
- Revisit IF:
  - [Assumption 1 breaks]
  - [Assumption 2 breaks]
  - [Assumption 3 breaks]

## Assumptions at Risk
1. **Assumption**: [What must be true for this decision to hold?]
   - Likelihood: [High/Medium/Low that it breaks]
   - Monitor: [How do you detect breakage?]

2. **Assumption**: [...]

## Known Failure Modes
1. **If [X happens]**: 
   - Quick fix: [do this]
   - Temporary fallback: [use this]
   - Permanent fix: [investigate this]

## How to Revert
[Step-by-step if this decision fails]

## Cost Impact (if applicable)
[Estimated cost, budget tracking, review frequency]

## Confidence Level
[High/Medium/Low — and why]
```

---

## Why This Matters for Solo Operators

1. **Future-Self Archaeology**: In 6 months, you'll forget why you chose Bifrost. This doc lets future-you reconstruct the reasoning in 2 minutes instead of 2 hours.

2. **Quick Reversibility**: If something breaks, you need a fast undo. "How do I get back to working?" should be <5 minutes to answer.

3. **Assumption Tracking**: Your decisions have hidden dependencies. When one breaks, you need to catch it before you waste time debugging the wrong thing.

4. **Cost Discipline**: Solo operators operate on fixed budgets. ADRs that ignore cost tracking become invalid fast.

5. **Shelf-Life Discipline**: Decisions have expiration dates. Marking them for review prevents zombie decisions (you forgot why you made them, but you keep following them anyway).

---

## Example: Your `/vibe` ADR Refined for Solo

```markdown
# ADR #5: Custom `/vibe` Slash Command for Mistral Integration

## Problem
Want to invoke Mistral Vibe from within Gemini CLI, capture output to file, 
and let Gemini review it—without leaving the terminal or switching windows.
Ensemble approach requires pulling in second opinions without breaking flow.

## Options Considered
- **Option A: Tab Switching**: Mistral in one tab, Gemini in another
  - Pros: Native experience, zero config
  - Cons: Manual context switching, output lost between tabs

- **Option B: Bifrost Full Proxy**: Route all Gemini requests through Bifrost to Mistral
  - Pros: Unified interface
  - Cons: Loses Gemini's planning capabilities (you want Mistral *assisting*, not *replacing*)

- **Option C: Custom `/vibe` TOML Slash Command** ← CHOSEN
  - Pros: No background services, leverages Gemini CLI native features, output persisted
  - Cons: Not officially documented (pioneering), requires shell piping knowledge

## Decision
**Chosen**: Option C (Custom `/vibe` TOML command)
**Why**: Lowest complexity, zero new infrastructure, captures ensemble goal (second opinion without replacing Gemini's planning)

## Shelf Life & Review Triggers
- Next Review: 2026-10-12 (6 months)
- Revisit IF:
  - Mistral Vibe CLI is deprecated (watch mistralai/mistral-vibe repo)
  - Gemini CLI removes TOML custom command support (unlikely)
  - You stop using Mistral (usage pattern changes)

## Assumptions at Risk
1. **Assumption**: Mistral Vibe CLI remains actively maintained
   - Likelihood: Medium (Mistral is competitive, but market could shift)
   - Monitor: Watch mistralai/mistral-vibe GitHub repo. If no commits for 3 months, flag it
   - Trigger: If Mistral deprecates Vibe, fallback to Option A (tab switching)

2. **Assumption**: Gemini CLI's TOML custom command feature stays documented
   - Likelihood: High (core feature)
   - Monitor: No active monitoring needed, would break immediately if deprecated
   - Trigger: If Gemini CLI breaks TOML support, revert to manual invocation

3. **Assumption**: You invoke `/vibe` ≥2 times per week (justifies complexity)
   - Likelihood: Medium (depends on your workflow)
   - Monitor: Track /vibe invocations. If <1 per week, Option A (tab switching) is simpler
   - Trigger: If usage drops, simplify to Option A

4. **Assumption**: Shell piping (tee command) works reliably
   - Likelihood: High (PowerShell tee is stable)
   - Monitor: No active monitoring needed
   - Trigger: If tee fails on output capture, debug TOML syntax

## Known Failure Modes
1. **If `/vibe` command fails to execute**:
   - Detection: Gemini CLI throws "Command not found: /vibe"
   - Quick fix: Verify ~/.gemini/commands/vibe.toml exists and is valid TOML
   - Root cause: Usually file not in right directory or TOML syntax error
   - Fallback: Use tab switching (Option A) while debugging
   - Time to fix: 5 minutes (check file permissions, TOML syntax)

2. **If Mistral Vibe hangs or times out**:
   - Detection: `/vibe` command blocks for >30 seconds
   - Quick fix: Ctrl+C to cancel, try again
   - Root cause: Mistral API is slow or your prompt is too complex
   - Fallback: Use cheaper model (Gemini Flash instead of Mistral Large)
   - Time to fix: Immediate (no config change needed)

3. **If vibe_output.md file is corrupted or lost**:
   - Detection: Gemini CLI can't read vibe_output.md
   - Quick fix: Invoke `/vibe` again to regenerate
   - Prevention: Keep backups of vibe_output.md if output is important
   - Time to fix: 2 minutes

## How to Revert
If `/vibe` skill becomes unreliable (>50% failure rate):

1. Delete the TOML file:
   ```powershell
   rm ~/.gemini/commands/vibe.toml
   ```

2. Fall back to Option A (tab switching):
   ```powershell
   # Terminal 1: Gemini CLI
   gemini

   # Terminal 2: Mistral Vibe
   vibe
   ```

3. No config changes needed. Gemini CLI still works normally.

Time to revert: 30 seconds. Zero data loss.

## Cost Impact
- `vibe` invocation: Uses Mistral API (pay-per-token)
- Estimate: ~$0.02-0.05 per `/vibe` invocation (depends on prompt length)
- Usage: Assume 2x/week = 8x/month = ~$0.30-0.40/month
- Impact: Negligible (<1% of total budget)
- Monitoring: Track vibe_output.md timestamps to see actual usage

## Confidence Level
**Medium-High (70%)**
- Why not higher? `/vibe` is a pioneering workflow (not officially documented)
- Why not lower? Underlying tech (TOML commands, shell piping) is proven
- Flag: First 10 invocations should validate stability
- Trigger: If first 10 work, upgrade confidence to High
```

---

## Putting It Together: Solo-Focused ADR Set

Your full document should have:

1. **ADR #1: Bifrost Routing**
   - Shelf life: 6 months (quarterly latency check)
   - Key risk: LiteLLM security (check status monthly)
   - Quick revert: 5 minutes (set env vars back to defaults)

2. **ADR #2: Gemini CLI + Aider Harness**
   - Shelf life: 12 months (Gemini still new, evaluate maturity)
   - Key risk: Gemini reasoning might lag Claude for complex work
   - Quick revert: Swap to Claude Code ($100/mo instead of $20/mo)

3. **ADR #3: Ollama Local Execution**
   - Shelf life: 6 months (evaluate TurboQuant integration when released)
   - Key risk: Windows 11 OS migration would make this moot
   - Quick revert: Uninstall Ollama, delete models, revert to cloud-only

4. **ADR #4: Hybrid Subscription + BYOK Cost Model**
   - Shelf life: 3 months (cost tracking is continuous)
   - Key risk: Provider pricing changes (check quarterly)
   - Quick revert: Switch to Gemini Pro only if budget tightens

5. **ADR #5: Custom `/vibe` Skill**
   - Shelf life: 6 months (Mistral Vibe is new, monitor for deprecation)
   - Key risk: Low adoption (if <1x/week usage, option A is simpler)
   - Quick revert: Delete TOML file, use tab switching

---

## Solo ADR Workflow (Ongoing)

### Monthly
- [ ] Review ADR #4 (cost tracking) - check actual vs. budget

### Quarterly
- [ ] Run latency benchmark for ADR #1 (Bifrost still <15ms?)
- [ ] Check provider pricing (any changes that break cost model?)
- [ ] Review GitHub for Ollama/Mistral Vibe/Gemini CLI news

### Every 6 Months (Shelf Life Review)
- [ ] Pull up each ADR
- [ ] Ask: "Are the assumptions still valid?"
- [ ] Ask: "Has the context changed?"
- [ ] If yes to either, schedule deep review

### When Something Breaks
- [ ] Check "Known Failure Modes" section first
- [ ] If not there, add it (for next time)
- [ ] Decide: Can I fix quickly (10 min)? Or does this invalidate the decision?
- [ ] If invalidates, trigger full ADR review

### Yearly (Broader Review)
- [ ] Step back. Are these 5 ADRs still the right decisions?
- [ ] Any new tools / providers since April 2026?
- [ ] Is the ensemble approach still working? Are you actually using `/vibe`?
- [ ] Are costs staying in budget?
- [ ] Any regrets?

---

## Bottom Line for Solo Operators

**Skip everything enterprise ADRs recommend about:**
- Stakeholder roles
- Approval gates
- Change management workflows
- Compliance documentation

**Focus on everything enterprise ADRs get right about:**
- Problem clarity
- Option analysis
- Decision reasoning
- Assumption tracking
- Reverting quickly

**Add solo-specific stuff that enterprise misses:**
- Shelf life + review triggers
- Failure modes + quick fixes
- Revert instructions
- Cost tracking (personal budget discipline)
- Future-self archaeology (make it easy to rediscover why you decided this)

Your ADRs are for **you, in 6 months, trying to remember why you're running Bifrost**.
Make that conversation easy.
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
