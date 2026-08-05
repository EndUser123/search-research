# Dream — 2026-08-04 (Session 019fcb53)

**Corpus window:** 2026-08-02 to 2026-08-04 (3 days)
**Corpus size:** 10+ handoffs, 1 AAR, 32+ www-ledger entries, 860+ wiki concepts, 5+ ADRs
**Scope:** host:grok
**Prior dream:** 2026-08-02-dream.md (patterns 1-4 captured there)
**Model:** parent Grok (single-pass)

## Pass 1 — Candidate additions

### Candidate 1: "Agent emits data, code renders" — display reliability pattern

- **Pattern:** when an LLM generates structured output as markdown prose, formatting is unreliable (line breaks eaten, list items merged). The structural fix is to separate evaluation (LLM builds data structures) from rendering (Python function guarantees format). This applies to any skill with structured output.
- **Instances:**
  - Session 019fcb53 (2026-08-04): `/todo` RNS output merged items into one paragraph. Fixed by `format_plain_rns()` in `render_rns.py`.
  - Prior sessions: `/close` summary output, `/aar` report formatting — same fragility, same manual fix each time
- **Evidence:** `/www` research (2026-08-04) confirmed this is industry-wide: parsia.net documents 8 failure modes, Anthropic redirects to Structured Outputs, Salesforce Agentforce converts LLM text to UI components
- **Wiki coverage:** `adaptive-risk-assessment-single-pass-first-architecture.md` documents this briefly under "Display reliability" but doesn't have a standalone concept. The pattern deserves its own page because it applies fleet-wide, not just to `/risk`.
- **Receipt:** `C:/Users/brsth/.grok/skills/todo/__lib/render_rns.py` lines 97-141 (format_plain_rns); `/www` research subagent output (2026-08-04)
- **Status:** ALREADY PROMOTED as part of the adaptive-risk-assessment wiki concept. No separate concept needed — the pattern is captured. Skip.

### Candidate 2: "Config disabled-list bare-name collision" — recurring structural hazard

- **Pattern:** Grok Build's `[skills] disabled` list uses bare skill names that match globally. When a native skill shares a name with a plugin skill, disabling the plugin version also kills the native. This has now caused TWO incidents in the same session.
- **Instances:**
  - Session 019fcb53 (2026-08-04): `"handoff"` in disabled list killed native `/handoff` (intended to suppress Pocock plugin version)
  - Session 019fcb53 (2026-08-04, same session): `"diagnosing-bugs"` and `"grill-me"` in disabled list would have killed the newly-created native skills — caught before damage
- **Evidence:** `grok inspect` output showing `[disabled]` tags; config.toml lines 169-180 (before and after fix)
- **Wiki coverage:** `agent-config-directory-taxonomy.md` documents the dedup-failure class but not the disabled-list collision specifically. The collision pattern is more specific and more dangerous — it's an active-kill, not a display duplicate.
- **Receipt:** git commit `fc4731d` (config: disable 7 duplicate skills — the original commit that caused the handoff kill); git commit `9a24ade` (cleaned disabled list — caught grill-me/diagnosing-bugs collision)
- **Status:** NOT YET IN WIKI. Candidate for promotion.

### Candidate 3: "Bounded-set enumeration before analysis" — over-generalization defense

- **Pattern:** when the operator specifies a bounded set of items (rename these 2 files, delete these 3), the agent generalizes from the stated items to unstated items, proposes changing things the operator didn't ask for, then argues against its own incorrect generalization. The structural fix: enumerate the exact mapping (current → proposed) before any analysis.
- **Instances:**
  - Session 019fcb53 (2026-08-04): operator said "rename codebase-design to design-codebase, and frontend-design to design-frontend." Agent generalized to "rename the entire design skill family" and argued against renaming `/design` — which was never in scope.
  - This is the same failure class as "false choices" and "premature scope expansion" — the agent invents a larger scope than stated.
- **Evidence:** the AGENTS.md trigger added this session (bounded-set enumeration trigger case); operator correction "renaming /design was never the goal"
- **Wiki coverage:** the trigger was added to AGENTS.md directly. No wiki concept exists. May warrant a concept page if the pattern recurs.
- **Status:** captured in AGENTS.md trigger case. Single instance so far — below the 2-instance floor for auto-promotion.

### Candidate 4: "Plugin skill migration: port, absorb, or retire" — skill lifecycle decision framework

- **Pattern:** when disabling a plugin that provides skills, each skill needs a disposition decision: port (copy natively with version tracking), absorb (extract technique into existing skill), or retire (capability covered elsewhere). The version-tracking via `source_plugin` + `source_commit` frontmatter + `check_vendored_skills.py` enables upstream drift detection.
- **Instances:**
  - Session 019fcb53 (2026-08-04): mattpocock-skills plugin → 10 ported, 4 absorbed (techniques extracted), 28 retired (duplicates or not applicable)
- **Evidence:** git commits `9a24ade` (port), `bf6e7dd` (graph fix); `check_vendored_skills.py` output showing all 11 vendored skills at `up_to_date`
- **Wiki coverage:** no concept for plugin migration methodology. The technique is transferable — any future plugin migration would follow the same port/absorb/retire + version-track pattern.
- **Receipt:** `C:/Users/brsth/.grok/scripts/check_vendored_skills.py`; the 10 ported SKILL.md files with `source_plugin: mattpocock-skills` frontmatter
- **Status:** NOT YET IN WIKI. Single instance — the methodology is sound but may be one-off. Monitor for recurrence before promoting.

## Pass 2 — Contradictions

### Contradiction 1: `/risk` vs `/red-team` trigger overlap

- **New claim:** `/risk` description says "Use for 'what could go wrong', 'is this safe', 'stress test', 'risk check'"
- **Existing claim:** `/red-team` description says "Use when: red-team, stress-test, pre-mortem, adversarial review, 'is this safe', 'what could go wrong'"
- **Type:** overlaps (same trigger phrases)
- **Resolution:** `/risk` is the lightweight entry point; `/red-team` is the heavy specialist workflow. `/risk` delegates to `/red-team` when escalation fires. The trigger overlap is intentional — `/risk` should fire first for quick checks. But the model needs to know which to invoke. `/ask` routing should prefer `/risk` for "what could go wrong?" and `/red-team` only when "full adversarial review" or "break this" is the intent.
- **Action needed:** update `/red-team` description to clarify it's the heavy mode, or add routing guidance to `/ask`.

### Contradiction 2: pre-mortem embedded in 3 skills vs standalone `/risk` premortem mode

- **Existing state:** pre-mortem is embedded in `/tp` (domain 5), `/design` (Step 5.5), `/red-team` (deep mode)
- **New state:** `/risk` now provides standalone pre-mortem as part of its scan phase
- **Type:** refines (not contradicts) — the embedded versions serve their parent skills; the standalone version serves the "just do a quick risk check" use case
- **Resolution:** no conflict. The embedded versions stay. `/risk` is the entry point when you want pre-mortem without the parent skill's overhead.

## Pass 3 — Retirements (DORMANT)

**Status:** dormant. Wiki is ~1 month old. Activation conditions not met.

## Pass 4 — Operator profile proposals

**Profile age:** check `operator-collaboration-style-and-leverage.md` mtime needed.
**Drift signals detected:**
- Operator pushed back on magic numbers ("I hate this magic number. Is there a good reason for it?") — signal that arbitrary thresholds need justification, not tradition
- Operator asked "why didn't you think about this more?" after an over-generalization error — signal that the bounded-set enumeration trigger is the right structural fix
- Operator requested code-based solutions over prose instructions ("why wouldn't you do that in code?") — reinforces the "agent emits data, code renders" preference

No formal profile update proposed — these signals are consistent with the existing profile's emphasis on structural fixes over behavioral rules.

## Pass 5 — Skill edit proposals

### Proposal 1: `/red-team` — clarify trigger vs `/risk`

- **Skill:** `P:/.grok/skills/red-team/SKILL.md`
- **Motivated by:** Contradiction 1 above — trigger phrase overlap between `/risk` and `/red-team`
- **Current text:** description line 8: "Use when: red-team, stress-test, pre-mortem, adversarial review, 'is this safe', 'what could go wrong'"
- **Proposed edit:** add a routing note: "For quick risk checks, use `/risk` — it starts light and escalates here if warranted. Use `/red-team` directly when you need full specialist verification."
- **Confidence:** medium (1 instance — the overlap was created this session)
- **Net size change:** +1 line
- **Operator decision needed:** promote via direct edit, or let `/ask` handle routing

## Receipts audit

- Candidate 1: ✅ receipted (render_rns.py source, /www research output)
- Candidate 2: ✅ receipted (git commits fc4731d, 9a24ade, grok inspect output)
- Candidate 3: ✅ receipted (AGENTS.md trigger case, operator correction quote)
- Candidate 4: ✅ receipted (check_vendored_skills.py, 10 ported SKILL.md files)
- Contradiction 1: ✅ receipted (both SKILL.md description lines cited)
- Contradiction 2: ✅ receipted (three embedded versions + /risk scan phase)

Receipts missing: 0.

## Operator promotion checklist

- [ ] Review Candidate 2 (config disabled-list collision) — promote via `/wiki` write flow if the pattern is worth a standalone concept
- [ ] Review Candidate 4 (plugin migration methodology) — promote if transferable, defer if one-off
- [ ] Resolve Contradiction 1 — update `/red-team` description or `/ask` routing
- [ ] Review Pass 5 Proposal 1 — edit `/red-team` SKILL.md to add routing note
