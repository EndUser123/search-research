---
title: "Here's part of a chat history talking about how to improve plans:
'
● Unified Semantic Daemon uses 2 databases:
  Data"
date: "2026-02-05"
mode: "COPILOT"
uuid: "bb58547a-cefa-4d03-836b-5b54ef6ccee3"
entry_count: 7
---

## Human

Here's part of a chat history talking about how to improve plans:
"
● Unified Semantic Daemon uses 2 databases:
  Database: CKS
  Path: P:/__csf/data/cks.db
  Purpose: Constitutional Knowledge System (memories, patterns, code, knowledge)
  ────────────────────────────────────────
  Database: Chat History
  Path: P:/__csf/data/chat_history.db
  Purpose: CHS - Chat History Search (conversation context)
  Plus:
  - FAISS Index: P:/__csf/data/chat_history_faiss_with_text - Semantic embeddings for chat search

  Note: The health check found CKS at P:\\data\\cks.db but the daemon uses P:/__csf/data/cks.db. These are
  different locations - possibly a legacy vs current path issue.

  Want me to investigate the P:\\data\\cks.db location vs P:/__csf/data/cks.db?

❯ yes, only one should be current.

● Understanding the CKS location discrepancy. I'll investigate to determine which location should be the
  single source of truth.

● Explore(Explore CKS database locations)
  ⎿  Done (29 tool uses · 85.7k tokens · 4m 3s)

● Excellent investigation. Key findings:

  - Active CKS: P:\\__csf\\data\\cks.db (7 MB, 2082 entries, recently updated)
  - Legacy CKS: P:\\data\\cks.db (61 KB, minimal usage)

  Let me write the consolidation plan:

● Updated plan
  ⎿  /plan to preview
  ⎿  User rejected Claude's plan:
     ╭──────────────────────────────────────────────────────────────────────────────────────────╮
     │ Plan: Consolidate CKS Database to Single Location                                        │
     │                                                                                          │
     │ Problem                                                                                  │
     │                                                                                          │
     │ Two CKS database paths exist, causing confusion:                                         │
     │ - P:\\__csf\\data\\cks.db (7 MB) - Active, authoritative                                    │
     │ - P:\\data\\cks.db (61 KB) - Legacy, minimal usage                                         │
     │                                                                                          │
     │ Solution                                                                                 │
     │                                                                                          │
     │ Standardize on P:\\__csf\\data\\cks.db as single source of truth.                           │
     │                                                                                          │
     │ Phase 1: Verify Data (READ-ONLY)                                                         │
     │                                                                                          │
     │ 1. Check if P:\\data\\cks.db contains any unique entries not in P:\\__csf\\data\\cks.db       │
     │   - Compare entry counts between both databases                                          │
     │   - If unique data exists, migrate it first                                              │
     │ 2. Verify no active components depend on P:\\data\\cks.db                                  │
     │                                                                                          │
     │ Phase 2: Create Path Constant                                                            │
     │                                                                                          │
     │ Create single source of truth for CKS path:                                              │
     │                                                                                          │
     │ File: P:\\__csf\\src\\knowledge\\systems\\cks\\__init__.py                                     │
     │                                                                                          │
     │ from pathlib import Path                                                                 │
     │                                                                                          │
     │ # Single source of truth for CKS database location                                       │
     │ CKS_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "cks.db"             │
     │ # Resolves to: P:/__csf/data/cks.db                                                      │
     │                                                                                          │
     │ Phase 3: Update Core Components                                                          │
     │                                                                                          │
     │ Update files to use the centralized constant:                                            │
     │                                                                                          │
     │ 1. P:\\.claude\\skills\\_tools\\cks_health_check.py                                          │
     │   - Change: CKS_DB_PATH = Path(r'P:/__csf/data/cks.db')                                  │
     │   - To: from __csf.src.knowledge.systems.cks import CKS_DB_PATH                          │
     │ 2. P:\\__csf\\src\\daemons\\daemon_client.py                                                 │
     │   - Update fallback path resolution to use constant                                      │
     │ 3. P:\\__csf\\src\\daemons\\unified_semantic_daemon.py                                       │
     │   - Verify uses constant or relative resolution                                          │
     │                                                                                          │
     │ Phase 4: Handle Legacy Database                                                          │
     │                                                                                          │
     │ Option A: Archive P:\\data\\cks.db (if no unique data)                                     │
     │ - Rename to P:\\data\\cks.db.legacy.backup                                                 │
     │                                                                                          │
     │ Option B: Delete if confirmed obsolete                                                   │
     │                                                                                          │
     │ Phase 5: Update Documentation                                                            │
     │                                                                                          │
     │ 1. P:\\__csf\\src\\knowledge\\systems\\cks\\CLAUDE.md                                          │
     │   - Update any outdated path references                                                  │
     │ 2. P:\\.claude\\docs\\** - Fix any remaining old path references                            │
     │                                                                                          │
     │ Files to Modify                                                                          │
     │ ┌──────────┬────────────────────────────────────────────────┬──────────────────────────┐ │
     │ │ Priority │                      File                      │          Change          │ │
     │ ├──────────┼────────────────────────────────────────────────┼──────────────────────────┤ │
     │ │ High     │ P:\\__csf\\src\\knowledge\\systems\\cks\\__init__.py │ Add CKS_DB_PATH constant │ │
     │ ├──────────┼────────────────────────────────────────────────┼──────────────────────────┤ │
     │ │ High     │ P:\\.claude\\skills\\_tools\\cks_health_check.py   │ Import constant          │ │
     │ ├──────────┼────────────────────────────────────────────────┼──────────────────────────┤ │
     │ │ Medium   │ P:\\__csf\\src\\daemons\\daemon_client.py          │ Use constant             │ │
     │ ├──────────┼────────────────────────────────────────────────┼──────────────────────────┤ │
     │ │ Low      │ Documentation files                            │ Update references        │ │
     │ └──────────┴────────────────────────────────────────────────┴──────────────────────────┘ │
     │ Verification                                                                             │
     │                                                                                          │
     │ 1. Run health check: python P:\\.claude\\skills\\_tools\\main_health.py                      │
     │ 2. Verify CKS queries work: /cks skill                                                   │
     │ 3. Verify daemon works: Check semantic_daemon_discovery.json                             │
     │                                                                                          │
     │ Risk: Low [R:1]                                                                          │
     │                                                                                          │
     │ - Path consolidation is reversible                                                       │
     │ - Most code already uses correct path                                                    │
     │ - Legacy database appears to be minimal/stale                                            │
     ╰──────────────────────────────────────────────────────────────────────────────────────────╯

❯ /exit
  ⎿  Goodbye!

❯ /duf
  ⎿  UserPromptSubmit hook error

● Quick DUF check for this session:

  Reading transcript to identify actual changes...

● Bash(tail -50 "P:\\.claude\\session_data\\session_transcript.jsonl" 2>/dev/null | grep -o '"tool":"[EW].*?"' |
      sort | uniq -c || echo "No transcript found")
  ⎿  (No content)
  ⎿  Running PostToolUse hooks…
  ⎿  PostToolUse:Bash hook error

● Let me check the actual session changes more directly:

● Bash(git diff --stat HEAD 2>/dev/null | head -20 || echo "No git changes or not in git repo")
  ⎿   .claude/hooks/skill_execution_state.py             | 26 +++++-----
      .claude/settings.json                              |  2 +-
      __csf/src/modules/chat_search/chat_search.py       | 56 ++--------------------
     … +2 lines (ctrl+o to expand)
  ⎿  Running PostToolUse hooks…

● DUF Analysis: Session Changes

  Classification: Moderate (4 files, ~80 lines changed)
  Checks Run: Pre-mortem, Rollback, Secret Leak, Blast Radius, Barrier

  Findings

  - Pre-mortem: chat_search.py removed 56 lines - verify core search functionality wasn't broken
  - Rollback: All changes are in git - safe to revert
  - Secret Leak: No credential patterns found in changed files
  - Blast Radius: skill_execution_state.py change affects all skill execution - verify skill routing still
  works
  - Barrier: PreCompact_checkpoint_capture.py changes modify checkpoint capture - verify checkpoints still
  work

  Action Items

  1 - Verify chat search still works after 56-line removal in chat_search.py
  2 - Test skill execution with modified skill_execution_state.py terminal detection
  3 - Confirm checkpoint capture/restore works with modified PreCompact_checkpoint_capture.py
  0 - none (changes are safe linter/refactor updates)

  Assessment: Safe to proceed

  Note: Changes appear to be linter/formatting updates (settings.json) and code refactors. The line removal in
   chat_search.py should be verified but likely safe.

✻ Cooked for 49s

❯ add action items to the plan.
  ⎿  UserPromptSubmit hook error

● Let me check for the active plan file:

● Read 2 files (ctrl+o to expand)
  ⎿  Loaded .claude\\CLAUDE.md

● Adding action items to the plan based on DUF analysis and recent changes:

● Update(.claude\\plans\\checkpoint_inprocess_hooks.md)
  ⎿  Added 14 lines
      454
      455  ---
      456
      457 +## Action Items (from DUF Analysis)
      458 +
      459 +Based on recent session changes (2026-02-05), add these verification action items:
      460 +
      461 +1. **Verify PreCompact_checkpoint_capture.py** - Recent modifications to checkpoint capture
          +hook require verification that capture/restore still works correctly after changes
      462 +2. **Verify chat_search.py functionality** - 56 lines removed; confirm core search functiona
          +lity remains intact
      463 +3. **Test skill execution routing** - `skill_execution_state.py` terminal detection changes
          +may affect skill routing; verify skills still execute correctly
      464 +4. **Checkpoint integration test** - Run full checkpoint create/restore/validate cycle to co
          +nfirm no regressions
      465 +5. **Performance baseline measurement** - Establish current checkpoint hook latency before i
          +n-process implementation (for comparison)
      466 +
      467 +**Priority:** Items 1-3 are immediate (from recent changes). Items 4-5 are for Phase 3 valid
          +ation.
      468 +
      469 +---
      470 +
      471  ## References
      472
      473  - `hook_system_improvements.md` - Original in-process implementation for PreToolUse hooks
  ⎿  Running PostToolUse hooks…

● Added action items to the plan:

  File: P:\\.claude\\plans\\checkpoint_inprocess_hooks.md

  New Action Items section added:

  1. Verify PreCompact_checkpoint_capture.py - Recent modifications require verification
  2. Verify chat_search.py functionality - 56 lines removed; confirm search still works
  3. Test skill execution routing - Terminal detection changes may affect routing
  4. Checkpoint integration test - Full create/restore/validate cycle
  5. Performance baseline measurement - Establish latency before in-process implementation

  Priority breakdown:
  - Immediate (1-3): Verify recent session changes didn't break anything
  - Phase 3 (4-5): For validation period after in-process implementation

  Plan status remains: PLANNING (not yet started)

✻ Cogitated for 58s

❯ /ask what skills(s) should we use to review a plan to make it better?
  ⎿  UserPromptSubmit hook error

● STEP 0: TRIAGE → Reversibility: 1.25 (FAST PATH - help query)

  STEP 4: ROUTE DECISION → Intent: Plan review/improvement

  Recommended skills for plan review:
  Skill: /plan reviewer
  Purpose: Primary choice - Validates plan quality, finds gaps, checks dependencies
  When to Use: Comprehensive plan quality review
  ────────────────────────────────────────
  Skill: /duf
  Purpose: Pre-mortem analysis - finds blind spots before implementation
  When to Use: Before executing plan
  ────────────────────────────────────────
  Skill: /arch
  Purpose: Architecture review - validates design decisions
  When to Use: Plans involving structural changes
  ────────────────────────────────────────
  Skill: /analyze --focus quality
  Purpose: Code quality analysis of implementation
  When to Use: After implementation starts
  ────────────────────────────────────────
  Skill: /adversarial-review
  Purpose: 7-perspective parallel review
  When to Use: High-stakes or complex plans
  ────────────────────────────────────────
  Skill: /opt
  Purpose: Solution optimization review
  When to Use: Improving existing solutions
  Execution:

  Primary recommendation: Use /plan reviewer for comprehensive plan validation.

  For the checkpoint_inprocess_hooks.md plan you just edited:

  /plan reviewer P:\\.claude\\plans\\checkpoint_inprocess_hooks.md

  Or combine with DUF for pre-mortem:

  /duf --plan P:\\.claude\\plans\\checkpoint_inprocess_hooks.md

  Quick start:
  1. /plan reviewer - Full plan quality review (gaps, dependencies, risks)
  2. /duf --plan - Pre-mortem cognitive checks
  3. /arch - Design validation for architectural changes

  Want me to execute /plan reviewer on your checkpoint plan?

❯ what about /strat, /q, /ask-olymp , others?
  ⎿  UserPromptSubmit hook error

● Analysis: Skills for plan review beyond /plan reviewer
  Skill: /strat
  Best For: Strategic thinking
  Plan Review Use Case: Evaluate approach alternatives, identify missed opportunities
  ────────────────────────────────────────
  Skill: /q
  Best For: Quality validation
  Plan Review Use Case: Check plan against standards, find structural issues
  ────────────────────────────────────────
  Skill: /ask-olymp
  Best For: Multi-LLM perspectives
  Plan Review Use Case: Get diverse opinions on plan strategy
  ────────────────────────────────────────
  Skill: /llm-debate
  Best For: Decision alignment
  Plan Review Use Case: Debate plan tradeoffs from multiple angles
  ────────────────────────────────────────
  Skill: /adversarial-review
  Best For: 7-perspective analysis
  Plan Review Use Case: Security, performance, quality, testing, etc.
  ────────────────────────────────────────
  Skill: /duf
  Best For: Pre-mortem
  Plan Review Use Case: Find blind spots before implementation
  ────────────────────────────────────────
  Skill: /opt
  Best For: Optimization
  Plan Review Use Case: Improve existing solutions
  ────────────────────────────────────────
  Skill: /nse
  Best For: Next steps
  Plan Review Use Case: Get concrete recommendations from the plan
  For your checkpoint_inprocess_hooks.md plan:

  Stack these skills based on what you want:

  Strategic alternatives → /strat
  Quality standards check → /q
  Multi-perspectives → /ask-olymp
  Comprehensive review → /adversarial-review
  Pre-mortem → /duf
  Next steps → /nse

  Recommended combinations:
  ┌──────────────────────┬─────────────────────────────────────────────┐
  │         Goal         │               Skill Sequence                │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ Find gaps & improve  │ /plan reviewer → /strat → /duf              │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ Validate quality     │ /q → /plan reviewer                         │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ Get diverse opinions │ /ask-olymp → /llm-debate                    │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ Comprehensive review │ /adversarial-review → /plan reviewer → /duf │
  └──────────────────────┴─────────────────────────────────────────────┘
  For your checkpoint plan specifically:

  1. /strat - Could evaluate if in-process execution is the right strategic approach vs alternatives
  2. /q - Would check if the plan follows solo-dev standards and best practices
  3. /duf - Already covered - pre-mortem for implementation risks

  Execution options:

  # Strategic analysis of approach
  /strat "Evaluate this plan: checkpoint in-process execution. What alternatives exist?"

  # Quality check
  /q P:\\.claude\\plans\\checkpoint_inprocess_hooks.md

  # Multiple LLM perspectives
  /ask-olymp "Review this plan and suggest improvements: checkpoint_inprocess_hooks.md"

  Which aspect of plan review do you want to focus on?

❯ I'm trying to figure out what our best practice should be.  If we decomposed all those skills or hook,
  and could mix them any way we want, what would we want?
  ⎿  UserPromptSubmit hook error

● Ideal Plan Review Workflow - Decomposed

  If we could atomic-ify all those skills into composable components, here's the optimal stack:

  Essential Perspectives (No Redundancy)
  ┌──────────────┬─────────────────────────┬──────────────────────────────┐
  │ Perspective  │    Atomic Component     │      Why Irreplaceable       │
  ├──────────────┼─────────────────────────┼──────────────────────────────┤
  │ Structural   │ Completeness checker    │ Required sections present?   │
  ├──────────────┼─────────────────────────┼──────────────────────────────┤
  │ Strategic    │ Alternative generator   │ Is this the right approach?  │
  ├──────────────┼─────────────────────────┼──────────────────────────────┤
  │ Risk         │ Pre-mortem analyzer     │ What blind spots exist?      │
  ├──────────────┼─────────────────────────┼──────────────────────────────┤
  │ Quality      │ Standards validator     │ Solo-dev compliant?          │
  ├──────────────┼─────────────────────────┼──────────────────────────────┤
  │ Multi-view   │ Perspective synthesizer │ What would X say about this? │
  ├──────────────┼─────────────────────────┼──────────────────────────────┤
  │ Optimization │ Gap finder              │ What could be better?        │
  └──────────────┴─────────────────────────┴──────────────────────────────┘
  Ideal Workflow (Sequential, Parallel Where Possible)

  ┌─ Phase 1: FAST (<10s) ──────────────────────────────────────┐
  │ 1. Completeness Scan          # structural validation      │
  │ 2. Standards Check            # solo-dev compliance        │
  └──────────────────────────────────────────────────────────────┘
                ↓ (if passes)
  ┌─ Phase 2: PARALLEL (<60s) ─────────────────────────────────┐
  │ 3. Dependency Analysis        # what must exist first?     │
  │ 4. Alternative Generation    # what else could we do?      │
  │ 5. Multi-Perspective Review  # diverse opinions            │
  └──────────────────────────────────────────────────────────────┘
                ↓
  ┌─ Phase 3: DEEP (<5min) ────────────────────────────────────┐
  │ 6. Pre-Mortem Analysis        # blind spots                │
  │ 7. Gap Finding               # what's missing?             │
  │ 8. Opportunity Scan          # what could be better?       │
  └──────────────────────────────────────────────────────────────┘
                ↓
  ┌─ Phase 4: SYNTHESIS ───────────────────────────────────────┐
  │ 9. Action Item Generation    # specific next steps         │
  │ 10. Risk Report              # what could go wrong?        │
  └──────────────────────────────────────────────────────────────┘

  Atomic Components We'd Want
  ┌─────────────────────────┬───────────────┬───────────────────────┬──────────────────────────┐
  │        Component        │     Input     │        Output         │         Replaces         │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ check_sections()        │ Plan markdown │ Missing sections list │ /plan reviewer (partial) │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ check_standards()       │ Plan text     │ Violations list       │ /q (partial)             │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ map_dependencies()      │ Plan tasks    │ Dependency graph      │ /plan reviewer (partial) │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ generate_alternatives() │ Plan approach │ 2-3 alternatives      │ /strat (Lite mode)       │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ premortem_check()       │ Plan plan     │ Failure scenarios     │ /duf (checks 1-10)       │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ multi_perspective()     │ Plan plan     │ Diverse opinions      │ /ask-olymp, /llm-debate  │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ find_gaps()             │ Plan text     │ Missing items list    │ /duf (check 17)          │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ scan_opportunities()    │ Plan text     │ Improvement ideas     │ /opt (partial)           │
  ├─────────────────────────┼───────────────┼───────────────────────┼──────────────────────────┤
  │ generate_actions()      │ All above     │ Specific tasks        │ All skills (final step)  │
  └─────────────────────────┴───────────────┴───────────────────────┴──────────────────────────┘
  Redundancy to Eliminate
  ┌────────────────────────────┬────────────────────────────────────────────────┐
  │         Redundant          │                    Because                     │
  ├────────────────────────────┼────────────────────────────────────────────────┤
  │ /strat + /llm-debate       │ Both do multi-perspective, just different LLMs │
  ├────────────────────────────┼────────────────────────────────────────────────┤
  │ /q + /plan reviewer        │ Both check completeness/standards              │
  ├────────────────────────────┼────────────────────────────────────────────────┤
  │ /duf + /adversarial-review │ Overlap on security, quality, testing          │
  └────────────────────────────┴────────────────────────────────────────────────┘
  Best Practice Recommendation

  For a NEW plan (before implementation):

  Phase 1 (FAST): /q --plan        # 10s - standards check
  Phase 2 (PARALLEL):
    - /strat --lite                # 30s - alternatives
    - /ask-olymp "review this plan" # 60s - multi-LLM opinions
  Phase 3 (DEEP): /duf --plan       # 60s - pre-mortem
  Phase 4: Synthesize into action items

  For an EXISTING implementation (after code exists):

  Phase 1: /vdate-quality          # code quality check
  Phase 2: /adversarial-review     # 7-perspective code review
  Phase 3: /duf                    # pre-mortem on changes
  Phase 4: Generate action items

  Atomic Skill Architecture (Ideal):

  # Each check is independent, composable
  plan_checks = [
      CompletenessCheck(),
      StandardsCheck(),
      DependencyCheck(),
      AlternativeCheck(),
      PreMortemCheck(),
      MultiPerspectiveCheck(),
      GapCheck(),
      OpportunityCheck(),
  ]

  # Run any combination based on context
  results = [check.run(plan) for check in plan_checks]
  action_items = synthesize_action_items(results)

  This gives us:
  - Single source of truth for each check type
  - Composable workflows (mix and match)
  - No overlap between skills
  - Parallel execution where independent

  Want me to design this atomic skill architecture?"

---

## Assistant

You already have almost exactly what you were asking for: that last answer you got (“Ideal Plan Review Workflow – Decomposed”) is basically v0 of the atomic model that the `plan_review_guide.md` then turns into a concrete skill stack and workflows.[1]

Here’s how they line up and where to tighten:

## 1. Map your “ideal atomic stack” to existing skills

From the decomposed answer in the chat plus the guide, the mapping is:

- **Structural / completeness checker** → `plan` (7‑section format) plus `q`’s issue detection for missing sections.[1]
- **Standards validator (quality)** → `q` as adaptive quality gate.[1]
- **Dependency / risk / pre‑mortem** → `duf` (19 checks, Mode B plan quality and Mode A implementation vs plan).[1]
- **Strategic / alternative generator** → `strat` (lite vs heavy).[1]
- **Multi‑perspective** → `strat --mode heavy` and `adversarial-review` (7 technical sub‑agents). `ask-olymp` is deprecated in the guide and replaced by `strat --mode heavy`.[1]
- **Gap finder / opportunity scanner** → combination of `duf` gap analysis plus `opt`’s optimization scan.[1]
- **Action‑item generator** → `nse` and `dne` (DUF→NSE pipeline).[1]
- **Truth / completion** → `finalize` for plan status and truth checks.[1]
- **AI‑skeptic filter** → `skeptic` for plans and diffs that came from an AI step.[1]

That’s almost 1:1 with the “Atomic Components We’d Want” table in the chat, just realized as skills instead of explicit functions.

## 2. What best practice should be, given that decomposition

Your own guide’s “Atomic Components – What Each Skill Uniquely Contributes” and “Redundancy to Avoid” tables are already the best‑practice policy, just not labeled that way.  If you want a crisp rule‑set for “if we could mix and match components arbitrarily, what do we actually want?”, it’s:[1]

- **Always enter via `q` for work that already exists.** It’s the adaptive gate: 0 issues → strategic; 1–6 → fixes + plan; ≥7 → stop and fix first.[1]
- **Use `plan` and `design` only for creation.**
  - `plan` for direct implementation plans.
  - `design` for research‑heavy / exploratory work that feeds into a `plan`.[1]
- **Use `duf --plan` as the canonical “plan correctness + pre‑mortem” engine.**
  - Mode A: implementation vs plan.
  - Mode B: plan quality.[1]
- **Use exactly one “big strategic engine”: `strat`.**
  - Lite for “quick strategic alt + opportunity”.
  - Heavy for the full multi‑persona, multi‑framework grind instead of `llm-debate`/`ask-olymp`.[1]
- **Use exactly one “big technical engine”: `adversarial-review`.**
  - That’s your 7‑perspective technical stack; don’t layer other “omni‑review” skills on top unless you’re after optimization (`opt`).[1]
- **Separate “what to do next” from “is it safe”:**
  - “Is it safe / what did I forget?” → `duf` / `dne`.[1]
  - “What next?” → `nse` (standalone) or the NSE phase inside `dne`.[1]
- **Always run the SoloDevConstitutionalFilter before emitting actions.**
  - That’s the enforcement layer the guide calls out explicitly.[1]

That’s essentially the “Atomic Skill Architecture (Ideal)” in prose, and it’s already encoded in the quick‑reference tables at the end of the guide.[1]

## 3. Where to refine your current guide vs the chat ideal

There are three gaps between the chat‑answer ideal and the current guide:

1. **Explicit “atomic components” interface.**  
   The guide describes skills, but not the conceptual primitives (`check_sections`, `map_dependencies`, etc.). The “ideal” answer names those explicitly; you could mirror that by:
   - Adding a short section that defines each atomic check (even if implemented via existing skills).
   - Linking each check to a specific skill or mode.[1]

2. **Redundancy resolution is half‑there.**  
   You already document “Redundancy to Avoid” (e.g., `duf` + `dne`, `strat` + `llm-debate`, `q` + `duf --minimal`).  The chat ideal adds a bit more:[1]
   - Treat `ask-olymp` as deprecated in practice, not just historically.
   - Treat `llm-debate` as conceptually folded into `strat` heavy mode for future workflows.[1]

3. **Composition diagrams vs “atomic runs”.**  
   The chat answer is very explicit about phases (FAST, PARALLEL, DEEP, SYNTHESIS). Your guide has those same phases in the “Plan lifecycle phases” and “Quality gates flow”, but it’s not framed as “this is the canonical best‑practice pipeline”.  You could:[1]
   - Call those flows out as the **canonical** sequences for NEW plan vs EXISTING plan vs QUICK vs COMPREHENSIVE reviews.[1]
   - Tie each phase to the atomic checks from the chat answer (completeness, standards, alternatives, pre‑mortem, gaps, opportunities, actions).

## 4. If you want a single “Best Practice” block to copy into CLAUDE.md

Something like this is consistent with both the chat answer and the current guide:[1]

- New plan:
  - `plan` (or `design` → `plan`) → `duf --plan` → `adversarial-review` → `skeptic` (if AI‑authored) → `tdd` for implementation → `nse`/`finalize`.[1]
- Existing plan + code:
  - `duf --plan` (Mode A) → `adversarial-review` → `q` as final gate → `nse`/`finalize`.[1]
- Fast gate before committing:
  - `q` (adaptive gate) → if issues, `nse` and `duf`; if clean, optional `strat --mode lite`.[1]
- Deep review on high‑stakes work:
  - `q` → `strat --mode heavy` → `adversarial-review` → `duf` (full) → `opt` → `nse` / `dne`.[1]

That’s the “what would we want if everything was fully decomposed and recomposable” answer, reconciled with the concrete skill set you have in the guide.

## Human

what from repos would we want to add?

## Assistant

From the repo side, the ideal is: every atomic plan‑check should be backed by concrete signals pulled from code, tests, and history, not just text. You already have some of this in the guide (search, TDD, artifact‑audit hooks); what’s missing is treating them as first‑class “inputs” into the atomic checks.

Here’s what is worth adding as explicit, composable repo‑sourced components.

***

## 1. Tests and verification artefacts

Atomic components:

- **check_tests_exist_for_plan_sections(plan, repo)**
  - Map each implementation phase / major task in the plan to:
    - Existing tests that cover it.
    - Or a missing‑tests list.
  - Pulls from:
    - `tests/`, `*_test.py`, `test_*` patterns.
    - TDDSYSTEM conventions (e.g., how you name tests that correspond to features).
  - Feeds:
    - `CompletenessCheck` (is there executable verification?).
    - `GapCheck` (sections with zero test coverage).

- **check_tests_status(plan, repo)**
  - Run the relevant test subset on demand (no continuous monitoring).
  - Report:
    - Failing tests tied to plan scope.
    - Flaky tests already in the blast radius.
  - Feeds:
    - `RiskCheck` / `PremortemCheck` (known brittle areas).
    - `ActionItems` (“fix failing test X before implementing step Y”).

***

## 2. Existing implementation & duplication discovery

You already have “Existing implementation discovery” in the plan format, but make it an explicit, reusable primitive:

- **discover_existing_implementations(plan, repo)**
  - Use code search + embeddings to detect:
    - Similar functionality already implemented.
    - Old versions of the same feature.
  - Output:
    - Candidate files/modules per plan section.
    - “Probable duplicates / near‑duplicates.”
  - Feeds:
    - `DependencyCheck` (what you must not break).
    - `OpportunityCheck` (reuse/refactor instead of net‑new).

- **check_orphaned_plans(repo)**
  - Scan repo for:
    - Plans without corresponding code (never implemented).
    - Code that appears to implement features without any plan nearby.
  - Feeds:
    - Session‑level `GapCheck` (“this feature was done with no plan / no verification doc”).

***

## 3. Architecture & contract alignment

Hook in repo‑encoded constraints, not just textual reasoning:

- **load_architecture_constraints(repo)**
  - Read:
    - ADRs / `arch/` docs.
    - Module boundaries (e.g., package layout, “do not call across this boundary” rules).
    - Public API contracts (OpenAPI / protobuf / JSON schemas).
  - Feeds:
    - `DependencyCheck` (does the plan respect existing boundaries?).
    - `RiskCheck` (contracts being changed, clients impacted).

- **check_schema_and_migration(plan, repo)**
  - If the plan touches DB / schemas:
    - Scan migrations directory.
    - Find related migrations, pending migrations, or patterns.
  - Feeds:
    - `BlastRadiusCheck` (data, backward compat).
    - `RollbackCheck` (is rollback plausible with current migration infra?).

***

## 4. Git history, churn, and ownership

Turn repo history into structured signals for the premortem:

- **analyze_change_history(plan, repo)**
  - For files/modules in the plan’s blast radius:
    - Churn (commits over last N days).
    - Bug density markers (files often in bug‑fix commits).
    - “Hotspots” that correlate with incidents.
  - Feeds:
    - `RiskCheck` (touching fragile code vs stable).
    - `AssumptionAudit` (are we assuming stability where history says otherwise?).

- **check_code_ownership(plan, repo)**
  - Even in solo‑dev, some files are “familiar” vs “unfamiliar” based on your own commit history.
  - Tag tasks as:
    - “Familiar area” vs “cold area”.
  - Feeds:
    - `EffortEstimate` inside NSE.
    - `RiskCheck` (more careful testing in unfamiliar modules).

***

## 5. Static analysis, linters, and type systems

Make tool outputs first‑class inputs:

- **collect_static_analysis_findings(repo, scope)**
  - Run or read:
    - Linters, type checkers, security scanners.
  - Filter to the files / modules referenced in the plan.
  - Feeds:
    - `QualityCheck` (existing technical debt).
    - `OpportunityCheck` (low‑hanging refactors to fold into the plan).

- **check_style_and_conventions(plan, repo)**
  - Compare plan’s proposed structure/filenames/APIs against:
    - Existing naming conventions.
    - Folder layout standards.
  - Feeds:
    - `StandardsCheck` (consistency with repo norms).

***

## 6. Config, feature flags, and runtime toggles

Without continuous monitoring, you still want config awareness:

- **discover_feature_flags_and_config(plan, repo)**
  - Scan for:
    - Config files.
    - Feature flags related to the plan’s area.
  - Output:
    - Which flags would gate this work.
    - Any unsafe defaults.
  - Feeds:
    - `BlastRadiusCheck` (can we roll out safely via flags?).
    - `RollbackCheck` (can we disable via config instead of revert?).

***

## 7. Issues, TODOs, and local “problem markers”

Use in‑repo markers as extra context:

- **collect_local_issues_and_todos(plan, repo)**
  - Grep / parse:
    - `TODO`, `FIXME`, `HACK`, `XXX` within the blast radius.
  - Feeds:
    - `GapCheck` (pre‑existing known issues intersecting the plan).
    - `OpportunityCheck` (fold nearby cleanups into the implementation phase if cheap).

***

## 8. How this plugs into your atomic plan‑review model

Conceptually, each of your atomic checks from the earlier answer gets a second argument (`repo_context`) and delegates to these primitives:

- `CompletenessCheck`:
  - `check_sections(plan_text)`
  - `check_tests_exist_for_plan_sections(plan, repo)`
- `StandardsCheck`:
  - `check_standards(plan_text)`
  - `check_style_and_conventions(plan, repo)`
- `DependencyCheck`:
  - `map_dependencies(plan_tasks)`
  - `discover_existing_implementations(plan, repo)`
  - `load_architecture_constraints(repo)`
- `PreMortemCheck`:
  - `analyze_change_history(plan, repo)`
  - `check_schema_and_migration(plan, repo)`
  - `discover_feature_flags_and_config(plan, repo)`
- `GapCheck`:
  - `check_tests_status(plan, repo)`
  - `collect_local_issues_and_todos(plan, repo)`
  - `check_orphaned_plans(repo)`
- `OpportunityCheck`:
  - `collect_static_analysis_findings(repo, scope)`
  - `discover_existing_implementations(plan, repo)` (for reuse/refactor)
- `ActionItems`:
  - Synthesizes all of the above, then runs through `SoloDevConstitutionalFilter` before surfacing anything.

That gives you a clean story: the “skills” (`q`, `duf`, `strat`, `adversarial-review`, `opt`, `nse`, `dne`, `finalize`) orchestrate the atomic checks, and the atomic checks are backed not just by plan text, but by concrete repo signals (tests, history, architecture, static analysis) in a way that still respects your solo‑dev constitutional constraints.

## Human

so the review skill becomes an orchstrator for other skills or resources or subagents?  Like how /v does it?

## Assistant

Yes – the plan review skill should be an **orchestrator**, but its orchestration model should look more like `q` + `v` combined than like a monolithic analyzer.

### How it should behave

1. **Plan‑level meta‑orchestrator (like `q`)**  
   - The plan review skill itself stays thin: it inspects the plan + context and decides which *checks* to run, not how to do each check.[1]
   - It routes to:
     - Cognitive checks: `strat` (strategic/alternatives), `duf --plan` (pre‑mortem, Mode A/B), `skeptic`.[1]
     - Technical checks: repo‑backed primitives (tests, integration, churn) and, when code exists, `adversarial-review` or even selected `vdate-*` stages.[2][1]

2. **Atomic sub‑agents / resources do the real work (like `v` stages)**  
   - `v` is a strict sequential pipeline of 16 concrete stages (syntax, quality, security, adversarial, tests, coverage, CVEs, deploy), each implemented as its own script or validator.[2]
   - Your plan review skill should mirror that pattern conceptually:
     - Structural/format check (7‑section `plan` structure).[1]
     - Standards/completeness check (`q` + custom section checker).[1]
     - Risk / pre‑mortem (`duf --plan`).[1]
     - Strategic alternatives (`strat`).[1]
     - Multi‑perspective technical review (`adversarial-review`, when code exists).[1]
     - Optimization pass (`opt`).[1]
     - Next steps (`nse`/`dne`).[1]

3. **Halt‑gate semantics for plans, inspired by `v`**  
   - `v` introduces mandatory halt gates: CRITICAL/HIGH from certain stages stop the pipeline until fixed.[2]
   - For plans, you want similar policy:
     - HALT if: missing 7‑section structure, no plan/code linkage (like `v`’s Stage 2.5 “NO REFERENCE FAIL”), or critical DUF risks not addressed.[2][1]
     - WARN if: optimization / opportunity findings only.  
   - That keeps the plan review skill in charge of **whether you may proceed**, while sub‑skills provide evidence.

4. **Session‑ and repo‑aware routing**  
   - `q` already behaves as a meta‑orchestrator that adapts behavior based on “issue count” and writes context used by other skills.[1]
   - The plan review skill should:
     - Read WTSESSION + repo signals (plans near code, tests, history).[1]
     - Choose which “stages” apply: for a brand‑new, code‑less plan, skip adversarial/code stages; for existing code + plan, pull in `duf --plan` Mode A and possibly a subset of `v`’s verifications.[2][1]

5. **Clear separation of concerns**

- Plan review skill:
  - Decides: which phases run, in what order, and what constitutes HALT vs WARN vs PASS.  
  - Aggregates: all findings into a unified view + action items, then runs SoloDevConstitutionalFilter.[1]

- Sub‑agents / resources:
  - Implement: each atomic check, whether that’s a cognitive check (DUF/strat), a technical review (`adversarial-review`, vdate‑quality), or a repo primitive (tests, churn, integration).[2][1]

So yes: the “review” skill should be an orchestrator whose **interface** looks like `q` (adaptive, context‑aware, multi‑skill) and whose **guts** are closer to `v` (explicit stages, some blocking, some informational), but applied to plans instead of code.

## Human

/export the plan-review skill solution.

## Assistant

Proposed **`plan-review`** skill design, ready to drop into your guides as the canonical solution.

***

## 1. Purpose and Trigger

**Skill:** `plan-review`  
**Purpose:** Meta‑orchestrator that validates and improves plans by routing through atomic plan checks, other skills, and repo‑backed signals, with halt‑gates for unsafe plans.  
**Trigger:** `plan-review plan-file.md` (or with chat context only).

***

## 2. High‑level Behavior

- Treat `plan-review` as the **plan equivalent of `v`**:
  - Sequential phases with explicit PASS/WARN/HALT semantics.
  - Each phase delegates to existing skills or repo primitives.
- Behaves like `q`:
  - Adaptive: chooses which phases to run based on plan age, presence of code, and issue severity.
  - Writes a structured result object (`plan_review_result.json`) for downstream skills.

***

## 3. Phases and Halt Gates

### Phase 0 – Context and Discovery (Non‑blocking)

Inputs:
- `plan-file.md` (or chat plan text).
- WTSESSION + repo context (nearest code, tests, git history, ADRs).

Checks:
- Locate associated code (plan co‑location, search, CHS, same priority ladder as v Stage 2.5 integration).[1][2]
- Detect whether implementation exists (files mentioned in plan, git history, etc.).[1]

Output:
- `context.plan_has_code` (bool).
- `context.plan_age`, `context.implementation_age`.

Gate:
- Never HALT here; just annotate context.

***

### Phase 1 – Structural & Standards Check (Blocking if missing)

Delegates:
- Plan structure: internal `check_sections(plan)` implementing the 7‑section format.[1]
- Standards/quality: `q --plan plan-file.md` (or internal reuse of its checks).[1]

Checks:
- 7 sections present and non‑empty.
- Required meta (title, date, status, owner).
- No obvious “should work” claims without verification slots.

Results:
- `issues.structure_missing`, `issues.standards_violations`.

Gate:
- **HALT** if:
  - Critical sections missing (Problem, Implementation, Risk, Success).
  - `q` reports ≥ N “problem mode” level issues for the plan.[1]
- **WARN** if:
  - Only minor formatting / naming issues.

***

### Phase 2 – Dependency, Existing Code, and Tests (Blocking for unknown dependencies)

Delegates:
- Existing implementation discovery: repo search + embeddings, as in the plan guide’s “Existing implementation discovery” step.[1]
- Test discovery: `tdd`’s discover step, limited to plan scope.[1]

Checks:
- Does each major step reference concrete modules or files where possible?
- Are there known integration points / dependent modules identified?
- Are there existing tests for affected areas, or test‑gaps recorded?

Results:
- `dependency_graph`.
- `existing_implementations`.
- `test_discovery.gaps`.

Gate:
- **HALT** if:
  - Plan introduces cross‑module changes with **no** dependencies documented.
- **WARN** if:
  - Dependencies documented but tests missing.

***

### Phase 3 – Risk & Pre‑Mortem (Blocking for critical unmitigated risks)

Delegates:
- `duf --plan plan-file.md` in Plan Quality Mode (Mode B) for a pure plan; Mode A if code exists.[1]

Checks:
- 19 DUF checks as applied to plan scope (pre‑mortem, rollback, blast radius, assumptions, barrier checks).[1]

Results:
- `risk.critical`, `risk.high`, `risk.mitigations`.

Gate:
- **HALT** if:
  - Any CRITICAL risk with no mitigation listed in the plan.
- **WARN** if:
  - HIGH risks present but mitigation steps are at least sketched.

***

### Phase 4 – Strategic Alternatives & Multi‑Perspective Review (Non‑blocking, improvement‑focused)

Delegates:
- `strat --mode lite` by default; `--mode heavy` if plan is high‑stakes or prior phases flagged many issues.[1]
- Optional: `adversarial-review plan-file.md` when the plan is tightly coupled to specific code modules and you want technical perspectives on the approach.[1]

Checks:
- Is this the right approach vs simpler alternatives?
- What alternative options exist, and what are their trade‑offs?

Results:
- `alternatives` (A/B/C with pros/cons).
- `strategic_insights`.

Gate:
- Never **HALT** here.
- Produce suggestions and possible restructurings only.

***

### Phase 5 – Gap & Opportunity Scan (Non‑blocking)

Delegates:
- `duf` gap findings related to completeness.[1]
- `opt` for optimization opportunities when implementation already exists or is tightly specified.[1]

Checks:
- Missing elements vs ideal 7‑section plan.
- Over‑engineered or under‑specified parts that could be simplified.

Results:
- `gaps` (missing tasks, dependencies, tests, docs).
- `opportunities` (simplifications, reuse, small refactors to fold into implementation).

Gate:
- **WARN** only; folds into action items.

***

### Phase 6 – Action Items & Status Recommendation (Blocking if constitution violated)

Delegates:
- `nse` logic for next steps synthesis.[1]
- SoloDevConstitutionalFilter.[1]

Steps:
1. Synthesize all issues from phases 1–5 into normalized action items:
   - Category: `fix-structure`, `add-dependencies`, `add-tests`, `add-mitigations`, `simplify`, `clarify-success`, `document`, etc.
   - Effort estimate and confidence.
2. Run every action through `SoloDevConstitutionalFilter` and drop anything that violates constraints (no lock ordering, no continuous monitoring, no autonomous execution, etc.).[2][1]
3. Derive a **status recommendation**:
   - `BLOCKED` – plan must be revised; HALT in earlier phases.
   - `REVISION-REQUIRED` – non‑fatal issues but recommend rework.
   - `READY-FOR-IMPLEMENTATION` – no HALT, only optional improvements.
   - `POST-HOC-REVIEW` – for already implemented/legacy plans.

Output:
- `plan_review_result.json`:
  - `status`, `halt_phase`, `issues_by_phase`, `action_items`, `recommendations`.

Gate:
- **HALT** at this final stage if:
  - No constitution‑compliant path forward for a CRITICAL risk (e.g., the only “fix” would involve prohibited patterns).
- Otherwise, return with status and actions.

***

## 4. How `plan-review` Uses Other Skills

**Direct orchestration targets:**

- `q` – structural/standards/issue counting used in Phase 1.[1]
- `duf --plan` – pre‑mortem, Mode A/B, Phase 3.[1]
- `strat` – strategic alternatives and deep thinking, Phase 4.[1]
- `adversarial-review` – optional multi‑perspective technical review of plans tightly tied to code, Phase 4.[1]
- `opt` – optimization and simplification for existing/strongly specified plans, Phase 5.[1]
- `nse` (internals) – action‑item structure and prioritization, Phase 6.[1]
- `tdd` (discover step) – test discovery for dependency / verification checks, Phase 2.[1]
- `skeptic` – optional AI‑authored plan verification that can be inserted after Phase 3 or 4 for plans generated by AI.[1]

**Repo primitives** (not separate skills, but callable helpers inside `plan-review`):

- Plan ↔ code linkage (like v Stage 2.5’s plan discovery order).[2]
- Existing implementation search, test discovery, git churn, architecture/ADR loading.

***

## 5. Usage Patterns

### For new plans (no implementation yet)

- Command:
  - `plan-review plan-YYYYMMDD-feature.md`
- Expected orchestration:
  - Phase 0 → 1 → 2 → 3 → 4 → 5 → 6.
  - Skip code‑dependent adversarial and test execution in early iterations; focus on structure, risk, strategy, and gaps.

### For existing implementation + plan

- Command:
  - `plan-review plan-YYYYMMDD-feature.md`
- Expected orchestration:
  - Phase 0 detects code present.
  - Phase 2 goes deeper into dependency + existing implementation.
  - Phase 3 uses `duf --plan` Mode A (implementation vs plan).[1]
  - Phase 4 may include `adversarial-review` over changed modules.[1]
  - Phase 5 uses `opt` to suggest improvements.[1]

***

## 6. Contract / Output Shape

Canonical output (simplified):

```json
{
  "plan_path": "P:/.../plan-20260205-checkpoint_hooks.md",
  "status": "REVISION-REQUIRED | BLOCKED | READY-FOR-IMPLEMENTATION | POST-HOC-REVIEW",
  "halt_phase": null,
  "phases": {
    "structure": { "pass": true, "issues": [...] },
    "dependencies": { "pass": false, "issues": [...] },
    "risk": { "pass": true, "critical": 0, "high": 1, "mitigations_missing": 0 },
    "strategy": { "alternatives": [...] },
    "gaps": { "items": [...] }
  },
  "action_items": [
    {
      "id": "PR-001",
      "category": "add-dependencies",
      "summary": "Explicitly document integration points with chat_search subsystem.",
      "effort": "S",
      "priority": 1,
      "constitutional_ok": true
    }
  ]
}
```

This gives you a `v`‑style, sequential, halt‑aware orchestrator for plans that reuses your existing skill ecosystem and repo signals, instead of re‑implementing any of the heavy lifting those skills already do.

## Human

please create the file for export for easy drop in use.

## Assistant

```markdown
TITLE Plan Review Skill - Sequential Plan Validation Orchestrator

Version: 1.0.0  
Status: DRAFT – Proposed design for implementation

---

## Purpose

**Skill:** `plan-review`  
**Goal:** Validate and improve plans by orchestrating atomic plan checks, existing review skills, and repo-backed signals, with explicit halt-gates for unsafe or incomplete plans.  
**Triggers:**  

- `plan-review plan-file.md`
- `plan-review` (uses most recent plan in context or chat buffer)

This skill is the **plan-level equivalent of `v`** (sequential pipeline with halt gates) and behaves like **`q`** as a meta-orchestrator that routes to other skills based on issues detected. [file:1][file:2]

---

## High-Level Behavior

- Sequential phases with PASS/WARN/HALT semantics.
- Delegates to existing skills (`q`, `duf --plan`, `strat`, `adversarial-review`, `opt`, `nse`, `tdd`, `skeptic`) and repo helpers.
- Produces a structured JSON result for downstream skills: `plan_review_result.json`. [file:1]

---

## Phases Overview

1. Context & Discovery (Phase 0 – non-blocking)  
2. Structural & Standards Check (Phase 1 – blocking if missing)  
3. Dependencies, Existing Code, and Tests (Phase 2 – blocking on unknown deps)  
4. Risk & Pre-Mortem (Phase 3 – blocking on unmitigated critical risks)  
5. Strategic Alternatives & Multi-Perspective Review (Phase 4 – non-blocking)  
6. Gap & Opportunity Scan (Phase 5 – non-blocking)  
7. Action Items & Status Recommendation (Phase 6 – blocking only for constitutional violations)  

Each phase can emit issues, but only designated phases can HALT the plan review. [file:1][file:2]

---

## Phase 0 – Context and Discovery (Non-Blocking)

**Inputs:**

- `plan-path` (file) or plan text from chat.
- WTSESSION context and repo root.

**Steps:**

- Locate plan file if only chat text is given (session transcript, CHS search).
- Discover associated code:
  - Co-located files (same directory as plan).
  - Central `.claude/plans` index if present.
  - References in plan sections (modules, files, APIs). [file:1]
- Determine:
  - `plan_has_code`: whether there is existing implementation.
  - `plan_age` and `implementation_age` via git history (optional).  

**Output:**

```json
"context": {
  "plan_path": "P:/.../plan-YYYYMMDD-feature.md",
  "plan_has_code": true,
  "plan_age_days": 0,
  "implementation_age_days": 3
}
```

**Gate:** Cannot HALT. Context only. [file:1]

---

## Phase 1 – Structural & Standards Check (Blocking if Missing)

**Delegates:**

- Internal `check_sections(plan_text)` for 7-section structure. [file:1]
- `q --plan plan-path` or `q` with plan in context. [file:1]

**Checks:**

- 7-section format present and non-empty:
  - PROBLEM, CONTEXT (including reversibility, blast radius, assumptions), EXISTING IMPLEMENTATION DISCOVERY, TEST DISCOVERY, PROPOSED SOLUTION, IMPLEMENTATION PLAN, RISK, SUCCESS, DEPENDENCIES. [file:1]
- Required metadata present (title, status, date).
- `q` issue count / severity for the plan. [file:1]

**Outputs (example):**

```json
"phase_structure": {
  "pass": false,
  "issues": [
    { "id": "STRUCT-001", "type": "missing-section", "section": "RISK" },
    { "id": "STRUCT-002", "type": "missing-section", "section": "SUCCESS" }
  ],
  "q_summary": {
    "issues": 5,
    "mode": "Mixed",
    "notes": "Missing risk and success criteria."
  }
}
```

**Gate:**

- HALT when:
  - Any core section is missing: PROBLEM, IMPLEMENTATION, RISK, SUCCESS. [file:1]
  - `q` reports “Problem” mode for the plan (issue threshold exceeded). [file:1]
- WARN when only minor formatting or optional sections are missing.

---

## Phase 2 – Dependencies, Existing Code, and Tests (Blocking on Unknown Dependencies)

**Delegates / Helpers:**

- `discover_existing_implementations(plan, repo)` – search & embeddings. [file:1]
- `tdd` discovery logic for tests touching plan scope. [file:1]

**Checks:**

- For each major implementation step:
  - Are referenced modules/files identified?
  - Are integration points noted (APIs, daemons, hooks)?
- Test discovery:
  - Existing unit/integration/regression tests in relevant modules.
  - Explicit test gaps.

**Outputs (example):**

```json
"phase_dependencies": {
  "pass": false,
  "dependency_graph": [...],
  "existing_implementations": [...],
  "test_discovery": {
    "has_tests": true,
    "missing_for_sections": ["Phase 2 - daemon changes"]
  },
  "issues": [
    {
      "id": "DEP-001",
      "type": "missing-dependency",
      "section": "Implementation Phase 2",
      "detail": "No integration points documented for unified_semantic_daemon."
    }
  ]
}
```

**Gate:**

- HALT when:
  - Plan spans multiple modules/services but does not document any dependencies or integration points.
- WARN when:
  - Dependencies documented but tests are missing; add required test tasks instead of blocking.

---

## Phase 3 – Risk & Pre-Mortem (Blocking on Unmitigated Critical Risks)

**Delegates:**

- `duf --plan plan-path`:
  - Mode B (Plan Quality Review) when no implementation exists.
  - Mode A (Implementation vs Plan) when code exists. [file:1]

**Checks:**

- 19 DUF checks:
  - Pre-mortem, inversion, second-order effects, blast radius, rollback, assumptions, barriers, etc. [file:1]
- Count CRITICAL and HIGH risks and whether plan includes mitigation steps.

**Outputs (example):**

```json
"phase_risk": {
  "pass": false,
  "critical": [
    {
      "id": "RISK-CRIT-001",
      "description": "No rollback path for DB migration.",
      "mitigated": false
    }
  ],
  "high": [],
  "issues": [...]
}
```

**Gate:**

- HALT when:
  - Any CRITICAL risk is unmitigated (no concrete rollback, monitoring, or test strategy).
- WARN when:
  - HIGH risks exist but mitigation tasks are present in the plan.

---

## Phase 4 – Strategic Alternatives & Multi-Perspective Review (Non-Blocking)

**Delegates:**

- `strat --mode lite` by default; `strat --mode heavy` when:
  - The plan is high-stakes, or
  - Previous phases surfaced many issues. [file:1]
- Optional: `adversarial-review plan-path` when plan references concrete code modules and you want technical perspectives on the approach. [file:1]

**Checks:**

- Is the chosen approach reasonable vs simpler alternatives?
- Are there clearly better patterns given existing architecture?
- Strategic trade-offs (performance, complexity, risk). [file:1]

**Outputs (example):**

```json
"phase_strategy": {
  "alternatives": [
    { "id": "ALT-A", "summary": "Use CKS constant only; no fallback path.", "pros": [...], "cons": [...] },
    { "id": "ALT-B", "summary": "Centralize path in env var, use default constant.", "pros": [...], "cons": [...] }
  ],
  "recommendation": "ALT-A"
}
```

**Gate:**

- Cannot HALT.  
- All findings are suggestions and optional improvements.

---

## Phase 5 – Gap & Opportunity Scan (Non-Blocking)

**Delegates:**

- DUF gap findings for completeness. [file:1]
- `opt` for optimization opportunities (simplification, reuse, efficiency). [file:1]

**Checks:**

- Missing items relative to ideal 7-section plan (e.g., no explicit success metrics, no test strategy).
- Over-engineering or under-specified steps that could be simplified.
- Nearby refactor/cleanup opportunities that are cheap to fold in.

**Outputs (example):**

```json
"phase_gaps": {
  "gaps": [
    { "id": "GAP-001", "type": "missing-success-criteria", "detail": "No measurable success metrics." }
  ],
  "opportunities": [
    { "id": "OPT-001", "type": "simplification", "detail": "Reuse existing chat_search index builder." }
  ]
}
```

**Gate:**

- WARN only. All items feed into action items but do not block.

---

## Phase 6 – Action Items & Status Recommendation (Blocking for Constitutional Violations Only)

**Delegates:**

- `nse` pattern for action item structuring. [file:1]
- SoloDevConstitutionalFilter. [file:1][file:2]
- Optional `skeptic` when the plan was AI-generated or heavily AI-edited. [file:1]

**Steps:**

1. Aggregate issues from Phases 1–5 into normalized action items:
   - Categories: `fix-structure`, `add-dependencies`, `add-tests`, `add-mitigations`, `simplify`, `clarify-success`, `document`, etc.
   - Include effort estimates (S/M/L) and priority (1–5).
2. Run each proposed action through `SoloDevConstitutionalFilter` and drop any that violate SoloDev constraints (no lock ordering, no continuous monitoring, no autonomous execution, no enterprise-grade scaling patterns, etc.). [file:1][file:2]
3. Derive a status recommendation:
   - `BLOCKED`
   - `REVISION-REQUIRED`
   - `READY-FOR-IMPLEMENTATION`
   - `POST-HOC-REVIEW`

**Output Shape (`plan_review_result.json`):**

```json
{
  "plan_path": "P:/.../plan-20260205-checkpoint_hooks.md",
  "status": "REVISION-REQUIRED",
  "halt_phase": "phase_dependencies",
  "phases": {
    "context": { ... },
    "structure": { ... },
    "dependencies": { ... },
    "risk": { ... },
    "strategy": { ... },
    "gaps": { ... }
  },
  "action_items": [
    {
      "id": "PR-001",
      "category": "add-dependencies",
      "summary": "Document integration with unified_semantic_daemon and chat_search subsystems.",
      "effort": "S",
      "priority": 1,
      "constitutional_ok": true
    },
    {
      "id": "PR-002",
      "category": "add-mitigations",
      "summary": "Add rollback steps for CKS path change in case daemon fails to start.",
      "effort": "M",
      "priority": 1,
      "constitutional_ok": true
    }
  ]
}
```

**Gate:**

- HALT here only if:
  - No constitution-compliant actions exist to resolve a CRITICAL risk (e.g., the only fix would involve a prohibited pattern).
- Otherwise:
  - Return status and action items; no further blocking.

---

## Integration with Other Skills

**Plan-review orchestrates but does not replace:**

- `plan` – for creating the 7-section plan it reviews. [file:1]
- `design` – for research-heavy features before a full plan. [file:1]
- `q` – adaptive quality gate used in Phase 1. [file:1]
- `duf --plan` – pre-mortem and plan quality/implementation checks in Phase 3. [file:1]
- `strat` – strategic alternatives and deeper thinking in Phase 4. [file:1]
- `adversarial-review` – technical perspectives on code and tightly-bound implementation plans. [file:1]
- `opt` – optimization passes for existing or detailed plans. [file:1]
- `nse`/`dne` – next steps and session-level past-to-future analysis; `plan-review` can feed them via its JSON output. [file:1]
- `tdd` – test discovery and TDD workflow after plan approval. [file:1]
- `skeptic` – AI output validation when the plan was AI-generated. [file:1]

All plan review actions must pass through SoloDevConstitutionalFilter before being suggested. [file:1][file:2]

---

## Usage Patterns

### New Plan (No Implementation Yet)

```bash
plan implement checkpoint in-process hooks
plan-review plan-20260205-checkpoint_hooks.md
```

- Expected phases: 0 → 1 → 2 → 3 → 4 → 5 → 6.
- Skip code-execution tests; focus on structure, risk, dependencies, and clarity.

### Existing Plan + Code

```bash
plan-review plan-20260201-chat_search_refactor.md
```

- Phase 0 detects implementation.
- Phase 2 goes deeper on dependencies and existing implementations.
- Phase 3 uses `duf --plan` Mode A (implementation vs plan). [file:1]
- Phase 4 may call `adversarial-review` for relevant modules. [file:1]
- Phase 5 uses `opt` for optimization suggestions. [file:1]

---

## Quick Reference Table

| Aspect                  | Plan-Review Behavior                                               |
|-------------------------|--------------------------------------------------------------------|
| Type                    | Sequential plan validation orchestrator                           |
| Inputs                  | Plan file or chat text, WTSESSION, repo context                   |
| Blocking Phases         | Structure (1), Dependencies (2), Risk (3), Final constitutional gate (6) |
| Non-Blocking Phases     | Context (0), Strategy (4), Gaps & Opportunities (5)               |
| Main Skills Used        | `q`, `duf --plan`, `strat`, `adversarial-review`, `opt`, `nse`, `tdd`, `skeptic` |
| Output                  | `plan_review_result.json` with status + action items              |
| Constitutional Filter   | Required for all action items                                     |


```

## Human

Any thoughts about this?
"  Step 1: Analyze Current State

  What is the current architecture pattern?
  - Sequential phase orchestrator (0→6 phases)
  - Each phase: Inputs → Delegates → Outputs → Gate decision
  - Blocking vs non-blocking phases
  - JSON state accumulation across phases

  Documented pain points:
  - None explicitly stated, but design implies problems with current plan review (manual, inconsistent)
  - Reference to file:1 and file:2 suggests existing precedent to follow

  Constraints:
  - Must integrate with existing skills (cannot modify their APIs)
  - Solo-dev context (constitutional filtering required)
  - Must produce structured JSON output

  ---
  Step 2: Identify Python-Specific Issues

  Analysis of the design:

  1. State management pattern (UNSPECIFIED): Design doesn't specify how state flows between phases. In Python,
   this could be:
    - In-memory dict (simple, but lost on crash)
    - JSON file write per phase (persistent, enables resume)
    - File I/O without proper locking → race condition risk
  2. Skill invocation (UNCLEAR): "Delegates to existing skills" but doesn't specify:
    - Skill() tool invocation (in-process, shares context)
    - Bash CLI invocation (subprocess, clean isolation)
    - Risk: Mixing invocation patterns leads to inconsistent behavior
  3. Error handling (MISSING): No mention of what happens when:
    - Semantic daemon is down (Phase 0 CHS search dependency)
    - Sub-skill fails (e.g., q --plan returns error)
    - Plan file not found
  4. Type safety (ABSENT): JSON output shape shown but no Pydantic models or type hints. Without schema
  validation:
    - Typos in JSON keys go undetected
    - Missing fields cause downstream crashes
    - No IDE autocomplete for consumers
  5. Resource leaks (POTENTIAL): If using file-based state:
    - No mention of cleanup for partial reviews
    - No mention of file locking for concurrent access

  ---
  Step 3: Recommend Improvements

  Issue 1: Missing Implementation Architecture [CRITICAL]

  The design describes behavior but not implementation. Cannot build from this spec.

  Recommendation: Add explicit implementation section:
  # State management: File-based with atomic writes
  state_file = Path(plan_path).with_suffix(".review.state.json")

  # Phase execution: Sequential with checkpoint after each phase
  for phase in phases:
      result = phase.execute(state)
      state.append(phase.name, result)
      atomic_write(state_file, state)  # Use checkpoint package's atomic_write

      if result.halt:
          break

  Evidence: References file:1 and file:2 suggest existing precedent. Check those for implementation patterns.

  ---
  Issue 2: Ambiguous "Repo Helpers" [HIGH]

  Phase 2 mentions discover_existing_implementations(plan, repo) with no concrete implementation.

  Recommendation: Either:
  - Remove "repo-backed signals" language (too vague)
  - Specify: "Uses Grep/Glob to find files matching module names from plan sections"

  Example:
  def discover_existing_implementations(plan_text: str, repo_root: Path) -> list[Path]:
      # Extract module/file references from plan
      references = extract_references(plan_text)  # e.g., "unified_semantic_daemon"

      # Search codebase
      found = []
      for ref in references:
          found.extend(glob.glob(f"**/*{ref}*.py", root_dir=repo_root, recursive=True))

      return found

  ---
  Issue 3: Daemon Dependency Without Fallback [MEDIUM]

  Phase 0 relies on CHS search via semantic daemon. Design doesn't address daemon unavailability.

  Recommendation: Add fallback path:
  def locate_plan_file(query: str) -> Path | None:
      # Try CHS search first
      try:
          results = semantic_daemon.search(query)
          if results:
              return results[0].path
      except DaemonUnavailable:
          pass

      # Fallback: Glob pattern
      candidates = list(Path(".claude/plans").glob("plan-*.md"))
      if not candidates:
          return None  # Prompt user for explicit path

      # Return most recent
      return max(candidates, key=lambda p: p.stat().st_mtime)

  ---
  Issue 4: No Type Schema for JSON Output [MEDIUM]

  plan_review_result.json structure shown but no Pydantic model.

  Recommendation: Add Pydantic schema:
  from pydantic import BaseModel
  from typing import Literal

  class PlanReviewStatus(BaseModel):
      plan_path: str
      status: Literal["BLOCKED", "REVISION-REQUIRED", "READY-FOR-IMPLEMENTATION", "POST-HOC-REVIEW"]
      halt_phase: str | None
      phases: dict[str, PhaseResult]
      action_items: list[ActionItem]

  class ActionItem(BaseModel):
      id: str
      category: str
      summary: str
      effort: Literal["S", "M", "L"]
      priority: int  # 1-5
      constitutional_ok: bool

  Rationale: Pydantic provides:
  - Runtime validation (catch bugs early)
  - JSON serialization (guarantees valid output)
  - IDE autocomplete (better DX)
  - Documentation (schema is documentation)

  ---
  Issue 5: No Test Strategy [MEDIUM]

  Design describes behavior but not how to verify it.

  Recommendation: Add testing section with fixtures:
  # tests/fixtures/plans/good_plan.md
  # Should PASS all phases

  # tests/fixtures/plans/missing_risk.md
  # Should HALT at Phase 1 (structure)

  # tests/fixtures/plans/unmitigated_critical.md
  # Should HALT at Phase 3 (risk)

  def test_phase_1_halt_on_missing_sections():
      plan = load_fixture("missing_risk.md")
      result = execute_phase_1(plan)
      assert result.pass == False
      assert result.halt == True
      assert any(i.type == "missing-section" for i in result.issues)

  ---
  Final Output Block

  Decision: The design concept is sound (sequential orchestrator with appropriate delegation), but
  implementation details are missing. Add an "Implementation Architecture" section covering state management,
  skill invocation protocol, and error handling before building.

  Rationale:
  1. Phase separation is correct — Each phase has clear inputs/outputs/gates, preventing feature creep
  2. Delegation is appropriate — Reuses q, duf, strat instead of reimplementing
  3. Constitutional filtering is critical — Prevents suggesting enterprise patterns for solo dev
  4. Implementation is underspecified — No details on state management, skill invocation, or error handling

  Alternatives Considered:
  - Extend /v instead of separate skill: Rejected because /v is code-focused, plan validation is semantically
  different
  - Implement as hook: Rejected because reviews should be opt-in, not enforced
  - Use in-memory state only: Rejected because file-based state enables resume after failures

  Risk: [R:2] Moderate. Design is architecturally sound but missing implementation details creates risk of:
  - Race conditions in state file writes (no locking specified)
  - Crashes when semantic daemon is down (no fallback specified)
  - Inconsistent skill invocation patterns (no protocol specified)

  Next Action: Add the following section to the design document before implementation:

  ## Implementation Architecture

  ### State Management
  - Phase state stored in `<plan_path>.review.state.json` (co-located with plan)
  - Each phase appends results atomically using checkpoint package's `atomic_write()`
  - File locking via `portalocker` for concurrent access safety

  ### Skill Invocation Protocol
  - Sub-skills invoked via `Skill()` tool (in-process, shares context)
  - Example: `Skill("q", args=f"--plan {plan_path}")`
  - Errors from sub-skills caught and added to phase issues list

  ### Error Handling & Fallbacks
  - Semantic daemon unavailable → Fall back to glob pattern matching for plan discovery
  - Plan file not found → Prompt user for explicit path (do not guess)
  - Sub-skill failure → Log error, continue to next phase (non-blocking)

  ### Testing Strategy
  - Unit tests for each phase's validation logic
  - Integration tests with mock plan fixtures
  - Fixtures: good_plan.md (PASS), missing_risk.md (HALT Phase 1), unmitigated_critical.md (HALT Phase 3)

  ### Type Safety
  - Pydantic models for all JSON output shapes
  - Runtime validation before writing results
  - Schema exported for downstream consumers

  ---
  Python template execution complete."

## Assistant

It’s a solid first review pass; I’d keep ~80% of it and tighten a few things.

## What’s strong

- It correctly identifies the **big missing pieces**: implementation architecture, state management, invocation protocol, error handling, schema, and tests. Those are exactly the gaps in the current spec.  
- The **Implementation Architecture** block at the end is the right kind of concrete: state location, atomic writes, locking, invocation style, fallbacks, and fixtures are all the things you’ll forget under pressure.  
- The suggestion to use **Pydantic models for the JSON output** is spot on; it matches how `v`/`verify` think in terms of tiered validation and schema’d outputs.[1]

## What I’d adjust or clarify

1. **“Issue 1: Missing Implementation Architecture [CRITICAL]” is a bit overstated.**  
   For a design doc, “underspecified implementation” is expected; I’d reword:  
   - From “Cannot build from this spec”  
   - To “Implementation cannot be made consistent across terminals/skills without specifying these details.”  
   That keeps the tone less absolute but still urgent.

2. **Be explicit about mirroring `v`’s patterns.**  
   You already reference file:2 implicitly; I’d make it explicit in the Implementation Architecture section:  
   - State file naming and storage: align with `v`’s `P:\.claude\state\vstate.json` patterns (terminal‑aware if needed).[1]
   - Hook patterns: if you ever add hooks around `plan-review`, reuse the `v` pattern (pre‑/post‑ phase enforcement).[1]

3. **Skill invocation protocol: commit to one model.**  
   The review currently lists options then recommends `Skill()` only at the end. I’d move that earlier and make it a rule:  
   - “All delegations from `plan-review` to other skills MUST go through the in‑process Skill() tool, not Bash CLIs, to avoid duplicated WTSESSION handling.”  
   You can still keep CLI examples for documentation, but the engine should be unambiguous.

4. **Repo helper recommendation might be too narrow.**  
   The “just use glob” suggestion is fine as a baseline, but you’ll probably want:  
   - Grep + glob + simple AST import analysis (e.g., find modules imported in the plan’s mentioned files).  
   I’d phrase it as “Minimum implementation MUST at least: glob by name; SHOULD enhance with search/AST later”.

5. **Daemon fallback: specify severity.**  
   Right now you say “fall back to glob; if none, return None.” I’d add a policy:  
   - “If daemon is down and plan cannot be found, `plan-review` MUST HALT before Phase 1 with a clear ‘no plan found’ error, not silently downgrade.”  
   That keeps the failure mode explicit.

6. **Tie test strategy to `q`/`v` style.**  
   The fixture idea is good; I’d add:  
   - At least one “good but not perfect” fixture where the plan passes structure but gets WARN at later phases, mirroring how `v` has non‑blocking stages.[1]

## Where it fits in your stack

- This review is effectively the **“Implementation Architecture” chapter** you said was missing from the `plan-review` spec.  
- Dropped into the design file, it gives you a direct path from the conceptual orchestrator to a concrete Python module with:
  - State structure.
  - Error semantics.
  - Invocation discipline.
  - Test plan.

If you want, next step would be to collapse this into an “Implementation Architecture” section with headings only (State, Invocation, Error Handling, Schema, Tests) and turn the code blocks into minimal reference snippets instead of full commentary.

## Human

yes please

## Assistant

Here’s a tightened “Implementation Architecture” section you can drop in.

***

## Implementation Architecture

### State Management

- Store phase state in a file co-located with the plan:  
  - `<plan_path>.review.state.json`
- After each phase:
  - Update an in-memory `state` dict.
  - Write the full state back using atomic writes (checkpoint package or equivalent).
- Use file locking (e.g., `portalocker`) to avoid concurrent write corruption if multiple terminals touch the same plan.

***

### Skill Invocation Protocol

- All delegations from `plan-review` to other skills MUST use the in-process `Skill()` tool, not Bash CLIs.
  - Example: `Skill("q", args=f"--plan {plan_path}")`
- `plan-review` is responsible for:
  - Passing plan path or text explicitly.
  - Capturing and normalizing sub-skill outputs into its own phase result shape.
- Any CLI examples in docs are for direct user use, not for internal orchestration.

***

### Error Handling & Fallbacks

- **Plan discovery:**
  - If a plan path is given and not found → HALT with a clear “plan not found” error.
  - If only a query/context is given:
    - Try CHS / semantic daemon first.
    - On daemon failure, fall back to:
      - Co-located plans near current repo path.
      - `.claude/plans/plan-*.md` glob (most recent).
    - If still not found → HALT before Phase 1 with “no plan found” status.
- **Sub-skill failures:**
  - Catch errors from `Skill()` calls.
  - Record them as issues in the current phase (with `severity="error"`).
  - For blocking phases:
    - If a critical sub-skill fails (e.g., `duf --plan`), mark the phase as HALT with an explicit “sub-skill failure” reason.
- **Daemon / external dependency failures:**
  - Never crash; always degrade to documented fallback or HALT with a specific error issue.

***

### Type Safety & JSON Schema

- Define Pydantic models for:
  - Top-level `PlanReviewStatus` (plan_path, status, halt_phase, phases, action_items).
  - Per-phase result types (e.g., `StructureResult`, `DependencyResult`, `RiskResult`).
  - `ActionItem` (id, category, summary, effort, priority, constitutional_ok).
- Validate instances before writing `plan_review_result.json`:
  - If validation fails, log an internal error and HALT with a “schema validation failed” issue.
- Export the JSON schema (via `model.model_json_schema()`) for downstream consumers and docs.

***

### Testing Strategy

- Unit tests for each phase function:
  - `execute_phase_1_structure`, `execute_phase_2_dependencies`, etc.
  - Verify PASS/WARN/HALT behavior given synthetic inputs.
- Integration tests that run the full pipeline on fixtures:
  - `good_plan.md` → READY-FOR-IMPLEMENTATION, no HALT.
  - `missing_risk.md` → HALT at Phase 1 (structure).
  - `unmitigated_critical.md` → HALT at Phase 3 (risk).
  - “Existing implementation” plan → exercises Mode A `duf --plan`.
- Mock `Skill()` invocations where appropriate:
  - Simulate `q`, `duf`, `strat`, etc., returning known shapes.
- Include regression tests for:
  - Schema changes (breaking vs non-breaking).
  - Error/fallback paths (daemon down, missing plan, sub-skill error).

***

### File Layout & Naming

- Place implementation under a dedicated module, e.g.:  
  - `__csf/src/plan_review/plan_review.py`
- State and result files:
  - `<plan_path>.review.state.json` – internal phase-by-phase state.
  - `<plan_path>.review.result.json` – final `PlanReviewStatus` output.
- Optionally add a thin CLI wrapper:
  - `plan-review plan-path` → calls Python entrypoint and prints a summary plus path to the result JSON.
