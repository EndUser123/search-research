<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# What domains are being expressed in these decomposed functions?

❯ does /nse or /q consider what should be finished or any gaps in what we have done or discovered that
should be addressed?
⎿  UserPromptSubmit hook error

● Searched for 4 patterns (ctrl+o to expand)

● Bash(cd "P:\\.claude\\skills" \&\& ls -1 | grep -i nse)
⎿  nse/
response-atomicity/
⎿  Running PostToolUse hooks…
⎿  PostToolUse:Bash hook error

● Bash(cd "P:\\.claude\\skills" \&\& ls -1 | grep -i "^q")
⎿  q/
quadlet/
query_alias/
quota/
⎿  Running PostToolUse hooks…

● Read 2 files (ctrl+o to expand)

● Analysis: What /nse and /q Cover

/nse (Next Step Engine)

Does:

- Analyzes git state, session activity, conversation history
- Proposes priority-ranked next steps with confidence/effort
- Filters constitutional violations

Does NOT explicitly:

- Review task list (33 pending tasks visible)
- Suggest documenting RCA learnings to CKS
- Identify gaps in investigation coverage

/q (Adaptive Quality Gate)

Does:

- Quick scan: git, session files, artifact audit (PRD, ARD, CHANGELOG, README)
- Active plan detection - checks P:\\.claude\\plans\\ for pending plans
- Adaptive output: Strategic (0 issues) → Mixed (1-6) → Problem (7+)

Does NOT explicitly:

- Review task list backlog
- Suggest CKS documentation of learnings
- Identify gaps from RCA retrospective

---
Gaps Not Covered

Based on today's session:
┌─────────────────────────────────────┬────────────────┐
│                 Gap                 │ Not Covered By │
├─────────────────────────────────────┼────────────────┤
│ 33 pending tasks in task list       │ /nse, /q       │
├─────────────────────────────────────┼────────────────┤
│ RCA learnings should go to CKS      │ /nse, /q       │
├─────────────────────────────────────┼────────────────┤
│ Investigation protocol improvements │ /nse, /q       │
├─────────────────────────────────────┼────────────────┤
│ Hook system documentation updates   │ /nse, /q       │
└─────────────────────────────────────┴────────────────┘
Recommendation: Run /q now to see if it flags pending artifacts or plans, but neither skill explicitly
handles the "retrospective learnings → CKS documentation" workflow that emerged from this RCA.

✻ Worked for 1m 15s

❯ if we decompose all of /nse and /q, what would the list of functions or features or solution
componenets be?
⎿  UserPromptSubmit hook error

● Decomposition: /nse and /q Component Analysis

Based on the skill documentation, here are the functional components:

---
/nse (Next Step Engine) Components
\#: 1
Component: Session Context Reader
Function: Reads WT_SESSION, loads session activity tracker
Dependencies: P:/__csf/.state/session_activities/{session_id}.json
────────────────────────────────────────
\#: 2
Component: Git State Analyzer
Function: Fresh git status --porcelain, git log origin/main..HEAD
Dependencies: Git CLI
────────────────────────────────────────
\#: 3
Component: Conversation History Analyzer
Function: Parses recent work, errors, topics from chat
Dependencies: Transcript/session logs
────────────────────────────────────────
\#: 4
Component: Scope Intersector
Function: Cross-references git files + session files (actual changes)
Dependencies: \#1, \#2
────────────────────────────────────────
\#: 5
Component: Constitutional Filter
Function: Filters prohibited patterns (enterprise, background services)
Dependencies: SoloDevConstitutionalFilter
────────────────────────────────────────
\#: 6
Component: Action Generator
Function: Proposes priority-ranked next steps with confidence/effort
Dependencies: nse_steps.generate_*()
────────────────────────────────────────
\#: 7
Component: Output Formatter
Function: Formats NSE output template
Dependencies: -
External Module: P:/__csf/src/features/nse/nse.py (Python wrapper)
Step Functions: P:/__csf/src/lib/nse_steps/ (Decomposed step functions)

---
/q (Adaptive Quality Gate) Components
\#: 1
Component: Session Activity Reader
Function: Primary source - WT_SESSION-scoped files
Dependencies: Session activity tracker
────────────────────────────────────────
\#: 2
Component: Git State Verifier
Function: Secondary source - fresh git status
Dependencies: Git CLI
────────────────────────────────────────
\#: 3
Component: Conversation Analyzer
Function: Topic-based work detection
Dependencies: Chat history
────────────────────────────────────────
\#: 4
Component: Scope Detector
Function: Auto-detects Code/Topic/Project scope
Dependencies: \#1, \#2, \#3
────────────────────────────────────────
\#: 5
Component: File Existence Checker
Function: Mechanical check - do edited files exist?
Dependencies: File system
────────────────────────────────────────
\#: 6
Component: Syntax Checker
Function: Basic syntax (Python imports, brackets)
Dependencies: AST/parser
────────────────────────────────────────
\#: 7
Component: Artifact Auditor
Function: Checks pending PRD, ARD, CHANGELOG, README
Dependencies: /artifact-audit or lib.q_context
────────────────────────────────────────
\#: 8
Component: Plan Detector
Function: Checks for pending plans in P:\\.claude\\plans\\
Dependencies: File system
────────────────────────────────────────
\#: 9
Component: Issue Counter
Function: Counts issues from Stage 1 checks
Dependencies: \#5, \#6, \#7, \#8
────────────────────────────────────────
\#: 10
Component: Threshold Router
Function: Routes to Strategic/Mixed/Problem mode
Dependencies: \#9
────────────────────────────────────────
\#: 11
Component: DUF Check Orchestrator
Function: Runs adaptive number of DUF checks
Dependencies: /duf, /duf-scan
────────────────────────────────────────
\#: 12
Component: NSE Gap Filler
Function: Fills remaining slots (7 total - issues)
Dependencies: /nse components
────────────────────────────────────────
\#: 13
Component: Strategic Priority Generator
Function: Pre-mortem questions (0 issues mode)
Dependencies: nse_steps.generate_strategic_priorities()
────────────────────────────────────────
\#: 14
Component: Context Writer
Function: Writes q_context.json for strategic skills
Dependencies: lib.q_context.write_context()
────────────────────────────────────────
\#: 15
Component: Output Formatter
Function: Formats adaptive output (Strategic/Mixed/Problem)
Dependencies: -
Delegates To: /duf, /duf-scan, /nse, /dne, /artifact-audit
Context Flow: /q → q_context.json → /strat, /arch, /nse, /duf

---
Shared Components

Both skills use:

- Session Activity Tracker (primary source in multi-terminal)
- Git State Verification (fresh, not cached)
- Constitutional Filter (SoloDevConstitutionalFilter)
- Conversation History Analysis
- Python wrappers (__csf/src/features/)

---
Missing Component (Gap Identified)

Neither skill has:

- Task List Reader - Would read the 33 pending tasks
- CKS Documentation Suggester - Suggest recording learnings after RCA
- Gap Analyzer - Identifies what investigation missed

Potential new component: /retro already exists for "Extract lesson-worthy segments from session" - may cover
the CKS documentation gap, but isn't integrated into /q or /nse workflows.

❯ Please do that same exercise with:

    Complete Skills Matrix
    Skill: /rr
    Category: self-review
    Timing: After session
    Primary Output: Reflection + systemic changes
    Value Analysis?: ✅ Yes (just added)
    ────────────────────────────────────────
    Skill: /retro
    Category: self-learning
    Timing: After session
    Primary Output: SKILL.md lessons
    Value Analysis?: No - lesson extraction
    ────────────────────────────────────────
    Skill: /reflect
    Category: self-learning
    Timing: After session
    Primary Output: Skill improvements
    Value Analysis?: No - signal-based
    ────────────────────────────────────────
    Skill: /duf
    Category: pre-mortem
    Timing: Before changes
    Primary Output: Failure scenarios + actions
    Value Analysis?: No - risk-focused
    ────────────────────────────────────────
    Skill: /think
    Category: meta
    Timing: Before decisions
    Primary Output: Distilled recommendation
    Value Analysis?: No - analysis gate
    ────────────────────────────────────────
    Skill: /analyze
    Category: analysis
    Timing: Before commit
    Primary Output: Risk/gaps/quality/security
    Value Analysis?: No - multi-lens
    ────────────────────────────────────────
    Skill: /value
    Category: strategy
    Timing: Any time
    Primary Output: Value opportunities
    Value Analysis?: ✅ Yes - value patterns
    ────────────────────────────────────────
    Skill: /cks
    Category: knowledge
    Timing: Any time
    Primary Output: Pattern storage/retrieval
    Value Analysis?: No - knowledge system
    ────────────────────────────────────────
    Skill: /chs
    Category: search
    Timing: Any time
    Primary Output: Semantic conversation search
    Value Analysis?: No - retrieval
    Key Insight
    ⎿  UserPromptSubmit hook error

● Read 9 files (ctrl+o to expand)

● Complete Skills Decomposition

/rr (Reflect and Review) Components
\#: 1
Component: Transcript Reader
Function: Reads session transcript for Edit/Write operations
Dependencies: Session transcript file
────────────────────────────────────────
\#: 2
Component: Work Summarizer
Function: Lists files changed, operations count, purpose
Dependencies: \#1
────────────────────────────────────────
\#: 3
Component: Quality Assessor
Function: Identifies what worked/didn't work
Dependencies: \#1
────────────────────────────────────────
\#: 4
Component: Pattern Extractor
Function: Identifies repeat/avoid patterns
Dependencies: \#1, \#3
────────────────────────────────────────
\#: 5
Component: Follow-up Tracker
Function: Notes items for next session
Dependencies: \#1
────────────────────────────────────────
\#: 6
Component: Value Analyzer
Function: Analyzes value created/lost/missed
Dependencies: \#1, \#2
────────────────────────────────────────
\#: 7
Component: Systemic Change Proposer
Function: Suggests CLAUDE.md/hooks/skills changes
Dependencies: \#6
────────────────────────────────────────
\#: 8
Component: CKS Auto-Storage
Function: Executes cks add for patterns automatically
Dependencies: CKS CLI
Key Feature: Value analysis + systemic changes (NEW - not in /retro or /reflect)

---
/retro (Self-Learning) Components
┌─────┬───────────────────────┬───────────────────────────────────────────────┬───────────────┐
│  \#  │       Component       │                   Function                    │ Dependencies  │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 1   │ Retro Script Runner   │ Executes P:/__csf/scripts/misc/retro.py       │ Python script │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 2   │ Segment Extractor     │ Extracts lesson-worthy segments from session  │ \#1            │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 3   │ SKILL.md Reader       │ Reads target SKILL.md Neural Cache section    │ Skill files   │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 4   │ Duplicate Checker     │ Avoids duplicate lesson entries               │ \#2, \#3        │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 5   │ Lesson Quality Filter │ Filters non-obvious, pattern-changing lessons │ Config        │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 6   │ Lesson Synthesizer    │ Creates one-line lesson entries               │ \#2, \#5        │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 7   │ SKILL.md Writer       │ Appends lessons to SKILL.md                   │ \#6            │
├─────┼───────────────────────┼───────────────────────────────────────────────┼───────────────┤
│ 8   │ Write Confirmer       │ Verifies write completed                      │ \#7            │
└─────┴───────────────────────┴───────────────────────────────────────────────┴───────────────┘
Key Feature: Golden Loop (Code → Resolve → Retro → Promote → Apply)

---
/reflect (Skill Improvement) Components
\#: 1
Component: Notification Clearer
Function: Clears lesson notifications before analysis
Dependencies: clear-notifications.py
────────────────────────────────────────
\#: 2
Component: Skill Selector
Function: Identifies which skill to analyze
Dependencies: User input
────────────────────────────────────────
\#: 3
Component: Signal Detector
Function: Detects corrections, successes, edge cases, preferences
Dependencies: Conversation history
────────────────────────────────────────
\#: 4
Component: Signal Classifier
Function: Classifies signals by confidence (HIGH/MEDIUM/LOW)
Dependencies: \#3
────────────────────────────────────────
\#: 5
Component: Change Proposer
Function: Proposes skill changes with confidence levels
Dependencies: \#4
────────────────────────────────────────
\#: 6
Component: Skill File Reader
Function: Reads skill file from P:/.claude/skills/
Dependencies: \#5
────────────────────────────────────────
\#: 7
Component: Change Applier
Function: Applies changes using Edit tool
Dependencies: User approval
────────────────────────────────────────
\#: 8
Component: Git Committer
Function: Runs git add, commit, push
Dependencies: \#7
────────────────────────────────────────
\#: 9
Component: Observation Saver
Function: Saves observations for later review
Dependencies: User declined
Key Feature: Signal-based (corrections HIGH, successes MEDIUM)

---
/duf (Pre-Mortem) Components
\#: 1
Component: Transcript Parser
Function: extract_changed_files() from session
Dependencies: duf_transcript_parser.py
────────────────────────────────────────
\#: 2
Component: Change Classifier
Function: Classifies magnitude (Trivial/Moderate/Significant/Major)
Dependencies: \#1
────────────────────────────────────────
\#: 3
Component: Check Orchestrator
Function: Runs 19 cognitive checks based on classification
Dependencies: \#2
────────────────────────────────────────
\#: 4
Component: Pre-Mortem Check
Function: "What will fail?" scenarios
Dependencies: Config
────────────────────────────────────────
\#: 5
Component: Inversion Check
Function: "What's the obvious risk?"
Dependencies: Config
────────────────────────────────────────
\#: 6
Component: Rollback Check
Function: "How to revert?"
Dependencies: Config
────────────────────────────────────────
\#: 7
Component: Constitutional Filter
Function: Filters prohibited patterns
Dependencies: SoloDevConstitutionalFilter
────────────────────────────────────────
\#: 8
Component: Action Item Generator
Function: Creates WHAT/WHY action items
Dependencies: \#4, \#5, \#6
────────────────────────────────────────
\#: 9
Component: Effectiveness Tracker
Function: Logs outcomes for threshold refinement
Dependencies: duf_effectiveness_tracker.py
Key Feature: Decomposed checks available at P:/__csf/src/lib/duf_checks/

---
/think (Analysis Gate) Components
\#: 1
Component: Context Checker
Function: Checks /q context for staleness
Dependencies: lib.q_context.read_context()
────────────────────────────────────────
\#: 2
Component: Framework Applier
Function: Applies 12-section framework internally
Dependencies: Config
────────────────────────────────────────
\#: 3
Component: Section Selector
Function: Routine (1,3,5,11) vs Architecture (all 12)
Dependencies: \#2
────────────────────────────────────────
\#: 4
Component: Recommendation Distiller
Function: Outputs distilled analysis, not template
Dependencies: \#2, \#3
────────────────────────────────────────
\#: 5
Component: Second-Order Analyzer
Function: Presents what change enables/risks
Dependencies: \#2
────────────────────────────────────────
\#: 6
Component: Complexity Tax Assessor
Function: Justifies analysis for solo dev
Dependencies: \#2
────────────────────────────────────────
\#: 7
Component: Approval Waiter
Function: Waits for user confirmation
Dependencies: All
Key Feature: Framework is INTERNAL scaffolding, outputs distilled recommendation

---
/analyze (Unified Analysis Engine) Components
\#: 1
Component: Target Detector
Function: Auto-detects git diff or accepts file/path
Dependencies: Git CLI
────────────────────────────────────────
\#: 2
Component: Mode Selector
Function: quick (5min), standard (15min), deep (30min), council (45min)
Dependencies: User input/default
────────────────────────────────────────
\#: 3
Component: Focus Lens Selector
Function: risk, gaps, opportunities, quality, security, etc.
Dependencies: Config
────────────────────────────────────────
\#: 4
Component: Phase Orchestrator
Function: Executes phases based on mode
Dependencies: \#2
────────────────────────────────────────
\#: 5
Component: UAF Framework
Function: Unified Analysis Framework logic
Dependencies: analyze_uaf.py
────────────────────────────────────────
\#: 6
Component: Constitutional Filter
Function: Filters prohibited patterns
Dependencies: SoloDevConstitutionalFilter
────────────────────────────────────────
\#: 7
Component: Recommendation Reporter
Function: Presents filtered findings with evidence
Dependencies: \#5, \#6
Key Feature: Consolidates 21 legacy commands (pmgoa, preview, intel, asef, etc.)

---
/value (Value Scanner) Components
\#: 1
Component: Git Diff Scanner
Function: Scans git diff for value patterns
Dependencies: Git CLI
────────────────────────────────────────
\#: 2
Component: Pattern Matcher
Function: Matches Leverage Point, Asymmetric Upside, Network Effect, etc.
Dependencies: Config
────────────────────────────────────────
\#: 3
Component: Impact Assessor
Function: Assesses impact and action required
Dependencies: \#2
────────────────────────────────────────
\#: 4
Component: Opportunity Presenter
Function: Presents value opportunities with recommendations
Dependencies: \#2, \#3
Key Feature: 5 value patterns (Leverage Point, Asymmetric Upside, Network Effect, Optionality, Flywheel)

---
/cks (Knowledge System) Components
┌─────┬───────────────────────┬───────────────────────────────────────────┬────────────────┐
│  \#  │       Component       │                 Function                  │  Dependencies  │
├─────┼───────────────────────┼───────────────────────────────────────────┼────────────────┤
│ 1   │ Daemon Client         │ Primary interface to semantic daemon      │ SemanticClient │
├─────┼───────────────────────┼───────────────────────────────────────────┼────────────────┤
│ 2   │ Content Type Detector │ Auto-detects pattern/memory/code/document │ Regex patterns │
├─────┼───────────────────────┼───────────────────────────────────────────┼────────────────┤
│ 3   │ CKS Ingester          │ Calls CKS.ingest_*() methods              │ cks.unified    │
├─────┼───────────────────────┼───────────────────────────────────────────┼────────────────┤
│ 4   │ Session Extractor     │ Extracts lessons from current session     │ Retro script   │
├─────┼───────────────────────┼───────────────────────────────────────────┼────────────────┤
│ 5   │ FAISS Searcher        │ Vector semantic search                    │ FAISS index    │
├─────┼───────────────────────┼───────────────────────────────────────────┼────────────────┤
│ 6   │ CLI Fallback          │ Direct backend when daemon unavailable    │ cks_cli.py     │
└─────┴───────────────────────┴───────────────────────────────────────────┴────────────────┘
Key Feature: Unified command (replaces /cks-add, /learn, /ingest)

---
/chs (Chat History Search) Components
┌─────┬───────────────────┬────────────────────────────────────────────┬────────────────────────┐
│  \#  │     Component     │                  Function                  │      Dependencies      │
├─────┼───────────────────┼────────────────────────────────────────────┼────────────────────────┤
│ 1   │ Daemon Checker    │ Checks semantic daemon availability        │ Pipe connection        │
├─────┼───────────────────┼────────────────────────────────────────────┼────────────────────────┤
│ 2   │ Semantic Searcher │ FAISS vector search via daemon             │ SemanticClient         │
├─────┼───────────────────┼────────────────────────────────────────────┼────────────────────────┤
│ 3   │ CLI Fallback      │ Falls back to CLI mode (~87s first search) │ chat_history_search.py │
├─────┼───────────────────┼────────────────────────────────────────────┼────────────────────────┤
│ 4   │ Filter Applier    │ Session, context, ranking filters          │ User input             │
├─────┼───────────────────┼────────────────────────────────────────────┼────────────────────────┤
│ 5   │ Result Presenter  │ Ranked results with relevance scores       │ \#2, \#4                 │
├─────┼───────────────────┼────────────────────────────────────────────┼────────────────────────┤
│ 6   │ Drill-Down Offer  │ Suggests /search-more for full content     │ \#5                     │
└─────┴───────────────────┴────────────────────────────────────────────┴────────────────────────┘
Key Feature: 20 smart features, daemon-first with CLI fallback

---
Shared Components Across Skills
┌──────────────────────────┬──────────────────────────────────┐
│        Component         │         Skills Using It          │
├──────────────────────────┼──────────────────────────────────┤
│ Daemon Client            │ /cks, /chs, /nse, /q             │
├──────────────────────────┼──────────────────────────────────┤
│ Git State Verification   │ /nse, /q, /duf, /analyze, /value │
├──────────────────────────┼──────────────────────────────────┤
│ Session Activity Tracker │ /nse, /q, /duf                   │
├──────────────────────────┼──────────────────────────────────┤
│ Constitutional Filter    │ /nse, /q, /duf, /analyze         │
├──────────────────────────┼──────────────────────────────────┤
│ Transcript Parser        │ /rr, /duf, /retro                │
├──────────────────────────┼──────────────────────────────────┤
│ Skill File Reader        │ /reflect                         │
├──────────────────────────┼──────────────────────────────────┤
│ CKS Storage              │ /rr, /cks                        │
├──────────────────────────┼──────────────────────────────────┤
│ Effectiveness Tracking   │ /duf                             │
├──────────────────────────┼──────────────────────────────────┤
│ Context Checker          │ /think, /nse, /q                 │
└──────────────────────────┴──────────────────────────────────┘
---
Missing Integration Gap

Gap: /retro extracts lessons but doesn't auto-store to CKS. /rr does auto-store to CKS but isn't integrated
into /nse or /q workflows.

Current State:

- /rr → CKS auto-storage exists
- /retro → SKILL.md Neural Cache only
- /nse → No CKS integration
- /q → No CKS integration

Potential Integration: Add CKS documentation suggestion to /q strategic mode and /nse next steps.

These decomposed components are spanning several overlapping domains in software engineering and knowledge‑work practice.[^1_1][^1_2][^1_3]

## High‑level domains

- **Execution control / workflow orchestration**: Session readers, scope detectors, mode selectors, phase orchestrators, DUF check orchestrator, NSE gap filler, threshold routers, and output formatters are all about coordinating *when* and *how* analysis or actions run within a session lifecycle.[^1_1]
- **Quality assurance and risk engineering**: /q, /duf, /analyze, and parts of /nse implement pre‑mortem analysis, verification‑style checks, syntax checks, artifact audits, and issue counting, which map to verification, validation, and risk‑management practices in SE (V‑model, pre‑mortems, multi‑level testing/checking).[^1_4][^1_5][^1_2][^1_6][^1_7][^1_8]
- **Retrospective \& continuous improvement**: /rr, /retro, /reflect, and the “systemic change proposer” components are in the post‑mortem / retrospective / process‑improvement domain: reflecting on what happened, extracting lessons, and changing process/skills accordingly.[^1_2][^1_7][^1_9]
- **Strategy \& value analysis**: /value and the value‑analysis parts of /rr and /value are doing product/strategy style work: identifying leverage points, asymmetric upside, optionality, and other value patterns in changes you’ve made.[^1_8][^1_2]
- **Knowledge management \& semantic retrieval**: /cks and /chs components (FAISS index, semantic daemon, ingesters, chat history search) are classic semantic‑search‑backed knowledge‑management: ingesting artifacts, embedding them, and retrieving lessons/patterns later.[^1_10][^1_3][^1_11]
- **Context and decision support / meta‑cognition**: /think, parts of /nse, /q, and /analyze are meta‑decision systems: they read context, apply internal frameworks, and distill recommendations before you commit or decide, which aligns with decision‑support systems and analysis gates in process engineering.[^1_6][^1_1]


## How they cluster conceptually

You can roughly see five “solution areas” emerging from the components:

1. **Pre‑change gates**
    - /duf, /think, /analyze, /value, and the /q “Problem/Mixed” modes are pre‑mortem/risk/quality/value gates that run *before* or right around changes.[^1_7][^1_2][^1_8]
2. **In‑flight navigation**
    - /nse and parts of /q act as navigation systems: reading git/session/chat context and suggesting next steps or checks, similar to adaptive planning and verification planning in SE.[^1_5][^1_4][^1_1]
3. **Post‑session reflection**
    - /rr, /retro, /reflect focus on retrospective analysis, lesson extraction, and skill evolution, which map to post‑mortems and continuous‑improvement disciplines.[^1_9][^1_2][^1_7]
4. **Knowledge capture and reuse**
    - /cks and /chs implement the KM stack: semantic ingestion, retrieval, and reuse of patterns, backed by FAISS and daemon/CLI flows.[^1_3][^1_11][^1_10]
5. **Governance and constraints**
    - The constitutional filters and effectiveness trackers are governance/control‑system pieces: enforcing constraints and tracking whether checks are actually effective, echoing verification \& validation governance in formal SE processes.[^1_12][^1_4][^1_6]

So, in domain terms: you’ve built an integrated system that spans workflow orchestration, quality/risk engineering, retrospectives, strategy/value analysis, and semantic knowledge management, all wrapped in a decision‑support layer rather than any one “single” domain.[^1_11][^1_4][^1_2][^1_3][^1_1]
<span style="display:none">[^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://www.computer.org/resources/software-engineering-process

[^1_2]: https://www.larksuite.com/en_us/topics/project-management-methodologies-for-functional-teams/pre-mortem-for-software-development-teams

[^1_3]: https://deepnote.com/blog/semantic-search-using-faiss-and-mpnet

[^1_4]: https://www.zentao.pm/blog/the-software-development-v-model-1823.html

[^1_5]: https://builtin.com/software-engineering-perspectives/v-model

[^1_6]: https://www.sei.cmu.edu/blog/using-v-models-for-testing/

[^1_7]: https://www.scrum.org/resources/blog/pre-mortem-preventing-product-failure-it-strikes

[^1_8]: https://joshclemm.com/writing/the-premortem-software-engineering-best-practice/

[^1_9]: https://asana.com/resources/premortem

[^1_10]: https://www.linkedin.com/pulse/short-summary-my-exploration-semantic-search-closed-knowledge-qian

[^1_11]: https://kminsider.com/topic/semantic-search-in-knowledge-management/

[^1_12]: https://www.complianceonline.com/resources/software-verification-and-validation-overview-and-must-have-documents.html

[^1_13]: https://www.geeksforgeeks.org/software-engineering/software-engineering-sdlc-v-model/

[^1_14]: https://en.wikipedia.org/wiki/Agile_software_development

[^1_15]: https://www.geeksforgeeks.org/software-engineering/software-engineering-classification-of-software-requirements/


---

# what domains do you think we are missing?

You’re richly covered on technical, quality, reflection, and KM, but light on a few important domains.[^2_1][^2_2][^2_3]

## 1. Delivery, operations, and runtime feedback

You have deep pre‑commit and pre‑mortem checks, but almost nothing on delivery/runtime:

- Deployment and release engineering (pipelines, feature flags, progressive delivery, rollback safety tied to /duf outcomes).[^2_4][^2_5][^2_1]
- Operational telemetry and feedback loops (linking incidents, performance, and production logs back into /rr, /retro, /cks as first‑class signals).

In domain terms: CI/CD, release management, and operability as a closed loop back into your analysis and knowledge systems.[^2_6][^2_4][^2_1]

## 2. Human factors and socio‑technical alignment

Most skills treat “you” as an ideal operator, but there’s no explicit domain for you‑as‑human in the loop:

- Cognitive load, fatigue, and context‑switch cost tracking; “should we stop, simplify, or defer?” gates.
- Socio‑technical design concerns: how your tools, hooks, and rituals impact your attention, error rates, and satisfaction as a solo dev.[^2_7][^2_2][^2_8][^2_9]

This is the human‑factors / socio‑technical‑systems domain applied to a one‑person, many‑agents environment.

## 3. Product / outcome‑level impact

You have value patterns (/value, /rr’s value analysis), but not a full product‑management domain:

- Explicit customer/outcome hypotheses, experiment tracking, and learning objectives linked into /cks.
- Post‑release impact review (“did this actually move the metric or user outcome we intended?”) beyond code‑level value patterns.[^2_3][^2_1]

This is more like continuous discovery and product thinking layered on top of your engineering value analysis.

## 4. Organizational KM and culture (scaled‑down)

CKS/CHS cover the technical side of knowledge, but not the “cultural” practices around it:

- Rituals and incentives for when/how to capture, review, and prune knowledge over time.
- Periodic “knowledge health” checks: stale patterns, fragmentation, duplication.[^2_10][^2_11][^2_3]

That’s the organizational‑knowledge‑management / learning‑organization domain, even if the “organization” is just you plus your tools.

## 5. Governance, compliance, and risk appetite

You have constitutional filters, but not a broader governance domain:

- Explicit risk appetite, compliance constraints, and “non‑negotiables” feeding into /analyze, /duf, and /q (e.g., security, privacy, licensing, regulatory constraints if/when relevant).[^2_12][^2_13][^2_14][^2_4]
- Auditability and traceability of important decisions, not just code changes (a “decision log” integrated with /think and /cks).


## 6. Long‑horizon portfolio / roadmap

Most skills are session‑ or change‑scoped. Missing is a domain for:

- Long‑term portfolio view: themes, epics, and bets over months; prioritization across them.
- Periodic strategic reviews that look at aggregates of /rr, /retro, /value, /cks data to adjust the roadmap, not just the next session.

That’s closer to portfolio management and strategic planning than to per‑session execution.

***

If you want a concrete next move: I’d start by defining a small “ops + socio‑technical” domain that (a) ingests runtime/incident signals and (b) tracks your cognitive load and fatigue, then feeds both into /q, /nse, /rr, and /duf as first‑class inputs.
<span style="display:none">[^2_15]</span>

<div align="center">⁂</div>

[^2_1]: https://articles.mergify.com/continuous-delivery-best-practices/

[^2_2]: https://www.interaction-design.org/literature/topics/socio-technical-systems

[^2_3]: https://www.sinequa.com/resources/blog/knowledge-management-for-engineering-teams-in-the-era-of-data-driven-insights/

[^2_4]: https://www.opsmx.com/blog/6-pitfalls-to-avoid-for-an-effective-continuous-delivery/

[^2_5]: https://www.cto.mil/wp-content/uploads/2023/07/SWE-Guide-April2023.pdf

[^2_6]: https://www.sciencedirect.com/science/article/pii/S0950584916302324

[^2_7]: https://humanisticsystems.com/2017/10/07/four-kinds-of-human-factors-4-socio-technical-system-interaction/

[^2_8]: https://pubmed.ncbi.nlm.nih.gov/16756937/

[^2_9]: https://en.wikipedia.org/wiki/Sociotechnical_system

[^2_10]: https://asem.org/blog/13411293

[^2_11]: https://rosap.ntl.bts.gov/view/dot/78009/dot_78009_DS1.pdf

[^2_12]: https://buildkite.com/resources/blog/securing-our-software-a-look-at-continuous-compliance-and-governance-in-ci-cd/

[^2_13]: https://ijcem.in/wp-content/uploads/2024/09/A-REVIEW-OF-CONTINUOUS-INTEGRATION-AND-CONTINUOUS-DELIVERY-PRACTICES-IN-MODERN-SOFTWARE-DEVELOPMENT.pdf

[^2_14]: https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/engineering-productivity-governance-and-improvement-in-software-delivery

[^2_15]: https://www.youtube.com/watch?v=cdyxr2yu0V8


---

# I'm a solo/ai-assisted dev.  Does that change the analysis?

It does, in a few important ways — some “missing domains” matter *more*, some matter *less*, and one new domain becomes central: managing your own cognitive bandwidth in an AI‑assisted workflow.[^3_1][^3_2][^3_3][^3_4]

## What matters *less* for a solo/AI‑assisted setup

- **Org‑level coordination domains**
    - Classic socio‑technical concerns around team structure, handoffs, ownership boundaries, and cross‑team communication are much weaker constraints when it’s just you.[^3_5][^3_6]
    - Heavy governance layers (formal approvals, multi‑stakeholder decision logs) are mostly unnecessary overhead; your “governance” can be lighter and embodied in constitutions, checklists, and habits.
- **Scaled KM rituals**
    - Organizational KM practices like incentives, formal communities of practice, and cross‑team knowledge curation aren’t needed; you already have CKS/CHS as a personal semantic brain without coordination costs.[^3_7][^3_8]


## What matters *more* because you’re solo

- **Cognitive load and attention management**
    - You are the only human bottleneck, and AI increases the volume and speed of possible work, so managing overload is existential: high load → more bugs, slower debugging, worse decisions, and burnout.[^3_2][^3_3][^3_4][^3_9][^3_1]
    - Domains around task slicing, limiting WIP, context‑switch control, “stop/simplify/park” gates, and fatigue‑aware prompts/skills become first‑class, not “nice to have”.[^3_10][^3_11]
- **Human–AI interaction design**
    - You’re effectively a micro socio‑technical system: one human plus many LLM “agents”.[^3_6][^3_12][^3_5]
    - Missing domain here is *interaction protocol design*:
        - How many parallel agents can you use before your comprehension collapses.
        - How results are summarized/normalized so you don’t drown in divergent outputs.
        - How you prevent over‑trust or over‑reliance on AI suggestions (guardrails on hallucinations, explicit “skeptic” checks).[^3_13][^3_11][^3_14][^3_2]
- **Runway and energy management**
    - A team can smooth over bad days; as a solo dev, your sleep, stress, and motivation directly gate throughput and quality.[^3_3][^3_4][^3_1]
    - A missing domain is a lightweight “ops for the human”: tracking energy, interruptions, and “red flag” states, then adapting /q, /nse, /duf behavior (e.g., stronger safety checks when tired, defaulting to smaller changes).[^3_1][^3_3]


## Domains that stay equally important

- **Delivery and runtime feedback**
    - Even solo, you still need CI/CD, deployment safety, and production feedback loops; the difference is you can automate the policies unilaterally and wire them tightly into your skills without organizational friction.[^3_15][^3_16][^3_17][^3_18][^3_19]
- **Product/value orientation**
    - Being solo doesn’t remove the need for product thinking; it actually heightens it, because you don’t have PMs or peers to sanity‑check whether you’re building valuable things.[^3_8][^3_17]
    - Your /value and /rr value components are on the right track, but a lightweight “product loop” (hypotheses → experiment → measure → feed into CKS) is still a missing domain, just scoped to one person.


## Net effect on your earlier “missing domains”

Reframing the earlier list through the solo/AI lens:

- Still important, but adapt to solo:
    - Delivery/runtime feedback → primarily CI/CD automation and monitoring that *feeds back* into /rr, /retro, /cks.
    - Product/outcome impact → small “AI‑augmented product loop” integrated with /value and /cks.
- Becomes *central*:
    - Cognitive‑load / attention domain, explicitly modeled and wired into /q, /nse, /duf, /think.[^3_4][^3_9][^3_2][^3_3][^3_1]
    - Human–AI interaction design (protocols, limits, skepticism, summarization layers).[^3_11][^3_14][^3_20][^3_2]
- Can be de‑emphasized or simplified:
    - Heavy org‑level governance and multi‑stakeholder KM; you can keep the spirit (traceability, knowledge pruning) but avoid heavyweight process.[^3_21][^3_7][^3_8]

If you want to turn this into concrete work: I’d treat “Cognitive Load \& Human–AI Interaction” as a new top‑level domain and design at least one new skill (or extensions to /q and /nse) that explicitly models your mental state, WIP, and AI‑interaction patterns, then adjusts suggestions and safety checks accordingly.
<span style="display:none">[^3_22][^3_23]</span>

<div align="center">⁂</div>

[^3_1]: https://ona.com/stories/common-bottlenecks-that-impacts-developer-productivity

[^3_2]: https://www.itprotoday.com/software-development/cognitive-load-in-the-age-of-ai-rethinking-developer-workflows

[^3_3]: https://www.agileanalytics.cloud/blog/reducing-cognitive-load-the-missing-key-to-faster-development-cycles

[^3_4]: https://idelsoft.com/blog/tpost/rnno6h72v1-how-cognitive-load-affects-developer-pro

[^3_5]: https://www.uniwriter.ai/software-engineering/exploring-the-software-crisis-and-socio-technical-systems-in-software-engineering/

[^3_6]: https://www.interaction-design.org/literature/topics/socio-technical-systems

[^3_7]: https://asem.org/blog/13411293

[^3_8]: https://www.sinequa.com/resources/blog/knowledge-management-for-engineering-teams-in-the-era-of-data-driven-insights/

[^3_9]: https://www.castsoftware.com/pulse/alleviating-the-cognitive-load-on-software-developers

[^3_10]: https://dev.to/leena_malhotra/a-simple-workflow-that-makes-you-a-faster-developer-3b5l

[^3_11]: https://lucvandonkersgoed.com/2025/02/09/are-humans-the-limiting-factor-in-ai-assisted-software-development/

[^3_12]: https://academic.oup.com/iwc/article/23/1/4/693091

[^3_13]: https://www.shrm.org/topics-tools/flagships/ai-hi/prioritize-human-factors--the-hidden-key-to-ai-project-success

[^3_14]: https://thoughtbot.com/blog/ai-led-or-human-led-coding-you-decide

[^3_15]: https://www.opsmx.com/blog/6-pitfalls-to-avoid-for-an-effective-continuous-delivery/

[^3_16]: https://www.sciencedirect.com/science/article/pii/S0950584916302324

[^3_17]: https://articles.mergify.com/continuous-delivery-best-practices/

[^3_18]: https://ijcem.in/wp-content/uploads/2024/09/A-REVIEW-OF-CONTINUOUS-INTEGRATION-AND-CONTINUOUS-DELIVERY-PRACTICES-IN-MODERN-SOFTWARE-DEVELOPMENT.pdf

[^3_19]: https://www.cto.mil/wp-content/uploads/2023/07/SWE-Guide-April2023.pdf

[^3_20]: https://humanfactors.jmir.org/2025/1/e59961/

[^3_21]: https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/engineering-productivity-governance-and-improvement-in-software-delivery

[^3_22]: https://www.linkedin.com/pulse/reducing-cognitive-load-software-development-ariel-pérez-1pyze

[^3_23]: https://www.reddit.com/r/ExperiencedDevs/comments/1j2mngh/anyone_have_to_leave_engineering_due_to_stress/


---

# show me what you think would be a good skill name for each domain I should have in my claude code skills/workflows?

Here’s a concrete naming pass, tuned for your solo/AI-assisted setup and your existing style (/q, /nse, /duf, etc.).[^4_1][^4_2][^4_3]

## Core execution and navigation

- Workflow orchestration / in‑flight navigation
    - **/nav** – high‑level session navigator (could wrap /nse and /q behaviors).
    - **/route** – routing/threshold logic for which skill to run next (analysis, value, retro, etc.).
- Delivery and runtime feedback
    - **/ship** – deploy/release + CI/CD gate summary.
    - **/pulse** – production/runtime health snapshot that feeds into /rr, /retro, /cks.


## Human–AI and cognitive load domain

- Cognitive load \& attention
    - **/pace** – assesses WIP, context fragmentation, fatigue signals, suggests slowing/slicing/parking work.
    - **/focus** – scopes the active problem and hides/parks non‑essential threads for this block of work.[^4_4][^4_5]
- Human–AI interaction design
    - **/orchestrate** – coordinates multiple agents/skills for a task with a clear plan and roles.[^4_6][^4_7]
    - **/skeptic** – dedicated “red‑team” check on AI outputs (hallucination, overconfidence, missing evidence).


## Product, value, and roadmap

- Product / outcome loop
    - **/bet** – define a hypothesis/bet (goal, metric, expected impact) before doing work.
    - **/impact** – after release, check whether the bet paid off, and write back to /cks.[^4_8][^4_9]
- Long‑horizon portfolio / roadmap
    - **/roadmap** – manage themes/epics and priorities over months.
    - **/portfolio** – periodic review of where time/changes actually went vs. roadmap.


## Knowledge and decision governance

- Knowledge health \& curation
    - **/garden** – prune, merge, and de‑duplicate CKS entries and SKILL.md lessons.
    - **/spotlight** – surface “most important patterns to revisit this week” from CKS/CHS.[^4_9][^4_10]
- Governance / decision logging
    - **/decide** – capture important decisions with context, alternatives, and rationale.
    - **/guardrails** – summarize and check against your current constitutions, non‑negotiables, and risk appetite.[^4_11][^4_12]


## “Ops for the human”

- Energy/runway management
    - **/checkin** – quick self‑status plus objective signals (session length, error rate, rework), then adapt suggested next steps.
    - **/cooldown** – structured end‑of‑day or end‑of‑sprint wind‑down that sets up tomorrow and parks dangling threads.[^4_13][^4_4]

If you want, next step I can help you choose a minimal first batch (e.g., /pace, /skeptic, /impact, /garden, /checkin) and define each skill’s first version of behavior and inputs.
<span style="display:none">[^4_14][^4_15][^4_16][^4_17][^4_18][^4_19][^4_20][^4_21][^4_22][^4_23]</span>

<div align="center">⁂</div>

[^4_1]: https://clig.dev

[^4_2]: https://github.com/leemunroe/cli-style-guide

[^4_3]: https://addyosmani.com/blog/ai-coding-workflow/

[^4_4]: https://ona.com/stories/common-bottlenecks-that-impacts-developer-productivity

[^4_5]: https://idelsoft.com/blog/tpost/rnno6h72v1-how-cognitive-load-affects-developer-pro

[^4_6]: https://dev.to/alexmercedcoder/a-practical-guide-to-ai-assisted-coding-tools-2fh5

[^4_7]: https://www.stefanknoch.com/blog/10-ai-workflows-every-developer-should-know-2025

[^4_8]: https://articles.mergify.com/continuous-delivery-best-practices/

[^4_9]: https://www.sinequa.com/resources/blog/knowledge-management-for-engineering-teams-in-the-era-of-data-driven-insights/

[^4_10]: https://asem.org/blog/13411293

[^4_11]: https://buildkite.com/resources/blog/securing-our-software-a-look-at-continuous-compliance-and-governance-in-ci-cd/

[^4_12]: https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/engineering-productivity-governance-and-improvement-in-software-delivery

[^4_13]: https://www.agileanalytics.cloud/blog/reducing-cognitive-load-the-missing-key-to-faster-development-cycles

[^4_14]: https://smallstep.com/blog/the-poetics-of-cli-command-names/

[^4_15]: https://developer.adobe.com/commerce/php/development/cli-commands/naming-guidelines/

[^4_16]: https://hackmd.io/@arturtamborski/cli-best-practices

[^4_17]: https://www.ibm.com/docs/en/tap/5.0.0?topic=building-workflow-naming-conventions

[^4_18]: https://github.com/aquasecurity/trivy/discussions/8446

[^4_19]: https://engineering.homeoffice.gov.uk/standards/low-code-workflow-naming/

[^4_20]: https://news.ycombinator.com/item?id=24020952

[^4_21]: https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/use-consistent-naming-conventions

[^4_22]: https://news.ycombinator.com/item?id=25304257

[^4_23]: https://doc.nuxeo.com/nxdoc/workflow-naming-conventions/


---

# I do want to cover all the features I already have, but I don't need to keep those header skill names.  Please show a table with the domain, the proposed skill names, and the features, both new and old, that are invoked by each skill.

Here’s a first-pass mapping that keeps all the **existing** capabilities but reorganizes them under a smaller, clearer set of skill entrypoints.

### Skills and domains overview

| Domain | Skill entrypoint(s) | Features each skill should invoke (new + existing) |
| :-- | :-- | :-- |
| Execution navigation \& gating | **/nav** | Wraps /nse + /q behaviors: session context reader, git state analyzer, conversation analyzer, scope intersector/detector, constitutional filter, action generator, threshold routing (Strategic/Mixed/Problem), NSE gap filler, DUF check orchestration, artifact audit, plan detection, issue counting, context writing for downstream skills. |
| Pre‑change risk \& quality | **/guard** | Wraps /duf + relevant /analyze modes: transcript parser, change magnitude classifier, 19 DUF checks, pre‑mortem/inversion/rollback checks, action‑item generator, effectiveness tracker, UAF framework for risk/gaps/quality/security, constitutional filter, recommendation reporter. |
| Deep analysis \& strategy | **/analyze** | Current /analyze (target detector, mode selector, focus lenses, phases, UAF) plus integration with /value and /think: constitutional filter, evidence‑backed findings, optional second‑order/complexity tax analysis for bigger changes. |
| Strategic thinking \& big decisions | **/think** | Existing /think (context checker, 12‑section framework, section selector, distilled recommendation, second‑order analysis, complexity tax) plus explicit decision framing for large architectural or product choices. |
| Value and product impact | **/value** | Existing /value (git diff scanner, value pattern matcher, impact assessor, opportunity presenter) plus: “bet” capture (hypothesis, metric, expected impact) and “impact review” hooks (post‑release outcome checks feeding CKS). |
| Post‑session reflection (systemic) | **/rr** | Current /rr: transcript reader, work summarizer, quality assessor, pattern extractor, follow‑up tracker, value analyzer, systemic change proposer, CKS auto‑storage. This is your main “session retro + systemic changes + value” loop. |
| Post‑session retro (code/skill‑focused) | **/retro** | Current /retro: retro script runner, segment extractor, SKILL.md reader/writer, duplicate checker, lesson quality filter, lesson synthesizer, write confirmer. Stays focused on “golden loop” lesson extraction to SKILL.md. |
| Skill improvement loop | **/reflect** | Existing /reflect: notification clearer, skill selector, signal detector \& classifier (corrections/successes/preferences), change proposer, skill file reader, change applier (with user approval), git committer, observation saver. |
| Knowledge system (patterns, docs, code) | **/cks** | Existing /cks: daemon client, content type detector, CKS ingester, session extractor, FAISS searcher, CLI fallback. Plus integration points: called from /rr, /retro, /value, /analyze, /think to store and retrieve patterns. |
| Conversation/semantic history | **/chs** | Existing /chs: daemon checker, semantic searcher, CLI fallback, filter applier, result presenter, drill‑down offer. Used by /rr, /retro, /reflect, /think when they need prior conversations. |
| Delivery \& runtime feedback | **/ship** | New wrapper: surfaces CI/CD status, build/test results, deployment state, and key runtime signals. Feeds /rr, /nav, /guard, /value (e.g., “recent incident here → analyze/duf/value this area”). |
| Cognitive load \& WIP | **/pace** | New: tracks session length, number of active branches/tasks, error/revert density, DUF/guard findings, subjective check‑in; recommends slowing, slicing, or parking work; can reduce allowed change magnitude or require /guard for risky edits when load is high. |
| Focus and scope control | **/focus** | New: chooses/locks current scope (task, repo area, topic), parks non‑essential threads, prunes context, and configures /nav, /guard, /analyze, /rr to operate only on the active scope. |
| Human–AI interaction safety | **/skeptic** | New: runs a “skeptical” pass over AI‑generated plans/diffs: cross‑checks assumptions, looks for missing tests/docs/edge cases, alignment with constitutions, and suggests counter‑questions or validation steps. Typically wraps /analyze and /duf checks. |
| Portfolio \& roadmap | **/roadmap** | New: manages themes/epics/bets across time; aggregates signals from /rr, /value, /ship, /cks to adjust priorities; surfaces “top 3 things that actually moved the needle vs what you planned”. |
| Knowledge gardening \& hygiene | **/garden** | New: runs over CKS and SKILL.md: finds duplicates and stale entries, merges/archives, tags by value/frequency, suggests what to promote or retire; may use /cks + /chs under the hood. |
| Decision logging \& governance | **/decide** | New: captures key decisions (context, alternatives, rationale, risks) and stores them via CKS; links to /think and /analyze outputs; can check against “guardrail” constraints before marking a decision final. |
| Human check‑in \& cooldown | **/checkin** | New: short self‑status plus objective metrics (session duration, recent /guard findings, revert counts); can auto‑invoke /pace or suggest /cooldown or /rr instead of “one more risky change”. |
| End‑of‑day/session closure | **/cooldown** | New: wraps /rr + a lighter /retro flavor + task list hooks: closes loops, captures follow‑ups, updates roadmap/CKS, and resets context for the next session. |

If you like this direction, we can next: (1) collapse overlapping entrypoints (e.g., decide if /nav should own /focus semantics), and/or (2) pick 3–4 high‑leverage new ones (/pace, /skeptic, /ship, /garden) and draft first‑version SKILL.md specs for them.

---

# please do 1 and 2

Here’s a tightened set of skills (step 1), then a first‑pass “v1 spec” for 4 high‑leverage skills (step 2).

## 1. Collapsing and simplifying the skill set

### Final entrypoints (after collapsing)

| Domain | Final skill(s) | Notes on collapse |
| :-- | :-- | :-- |
| Execution navigation \& gating | **/nav** | Owns session navigation, scope, and when to run /guard, /analyze, /rr, etc. Absorbs /focus semantics. |
| Pre‑change risk \& quality | **/guard** | Single gate for pre‑mortem + quality/risk checks. Wraps /duf + relevant /analyze modes. |
| Deep analysis \& strategy | **/analyze**, **/think** | /analyze = code/system analysis; /think = higher‑order strategic/architectural/product decisions. |
| Value \& product impact | **/value** | Value patterns + lightweight product “bet/impact” loop. |
| Post‑session reflection | **/rr**, **/retro**, **/reflect** | Keep all three: /rr = session/systemic, /retro = SKILL.md lessons, /reflect = skill evolution. |
| Knowledge system \& history | **/cks**, **/chs** | As‑is; central KM backbone. |
| Delivery \& runtime feedback | **/ship** | Deploy/CI/CD/runtime feedback loop (new). |
| Cognitive load \& WIP | **/pace** | Absorbs “human ops” + WIP control; replaces separate /checkin. |
| Human–AI safety \& interaction | **/skeptic** | Single “skeptical” wrapper around AI outputs and plans. |
| Portfolio \& roadmap | **/roadmap** | Portfolio view; can log decisions via /cks instead of a separate /decide skill. |
| Knowledge hygiene | **/garden** | CKS/SKILL.md pruning, dedupe, promotion. |
| Session closure | **/cooldown** | End‑of‑day/session closure; wraps /rr and suggests /retro/reflect as needed. |

Removed by merging:

- **/focus** → merged into /nav (scope selection is part of navigation).
- **/checkin** → merged into /pace (check‑in is how /pace starts).
- **/decide** → replaced by: /think + “decision record” subflow that writes via /cks.
- **/portfolio** → merged into /roadmap.

So your *new* skills to spec first are: **/pace, /skeptic, /ship, /garden** (plus wiring tweaks to /nav, /guard, /value, /rr later).

***

## 2. v1 specs for /pace, /skeptic, /ship, /garden

### /pace – Cognitive load \& WIP controller

**Purpose**
Keep you from overloading yourself: detect when cognitive load/WIP is too high and adapt the workflow (smaller changes, stronger gates, or stop/park).

**When to use**

- Manually: `/pace` when you feel scattered, stuck, or tempted to “just push one more big change”.
- Auto‑hook: before large edits, after long sessions, or when error/revert density spikes.

**Inputs**

- Optional: short natural‑language context (`/pace "I feel scattered, just did a huge refactor"`).
- Environment/session:
    - Session duration (start time vs now).
    - Number of active git branches and uncommitted files.
    - Recent /guard results (issue counts, severities).
    - Revert frequency (commits with “revert”, “fix”, etc.).
    - Pending tasks count (from your task list system, if available).

**Core behavior**

1. **Signal collection**
    - Read session activity file, git status/log, recent /guard or /q outputs.
    - Compute a simple load score (e.g., Low / Medium / High) based on: duration, WIP, errors/reverts, subjective text.
2. **Load classification**
    - Low: short session, few changes, low error rate.
    - Medium: moderate session, some WIP, some errors.
    - High: long session, many uncommitted changes, recent risky findings or reverts.
3. **Recommendations \& mode switches**
    - Low: OK to continue normally; may suggest optional /guard or /value on big changes.
    - Medium:
        - Suggest: smaller batch, run /guard on significant changes, capture a quick /rr checkpoint.
        - Offer: “park” low‑priority tasks to task list.
    - High:
        - Recommend: stop new risky work; run /cooldown or at least /rr.
        - If user insists, require /guard before any major edits and suggest narrowing scope (mini‑/nav inside).
4. **Outputs**
    - Clear state summary: “Pace: HIGH – reasons: 3 active branches, 17 modified files, 4 recent fix commits, session 3h+. Recommended actions: …”.
    - 2–3 specific Next Actions (no more): e.g., “Run /cooldown”, “Stage \& commit small slice”, “Open task list and park feature X”.

***

### /skeptic – Human–AI safety check

**Purpose**
Be the “safety brake” and critical reviewer of AI‑generated plans/diffs/analyses, especially before big moves.

**When to use**

- After you get a large plan, refactor, or analysis from an AI (Claude Code or others).
- Before merging or shipping AI‑heavy changes.

**Inputs**

- Required: a target to be skeptical about.
    - Pointer to a plan file, diff, or analysis summary (e.g., last /analyze or /nav output).
    - Optional: risk hints (“security‑sensitive”, “data‑loss risk”, “performance‑critical”).

**Core behavior**

1. **Context reading**
    - Load the target plan/diff/analysis.
    - Pull recent /guard and /analyze outputs if available.
2. **Skeptic lenses**
Apply a small, fixed set of lenses (internally similar to a cut‑down /duf + /analyze):
    - Evidence: Which claims lack concrete evidence or references?
    - Coverage: What obvious cases, edge conditions, or failure modes are missing?
    - Alignment: Any conflicts with constitutions, risk appetite, or existing architecture?
    - Overreach: Where is AI being overconfident or doing more than you asked?
3. **Findings \& actions**
    - Produce a short findings list (ranked High/Medium/Low).
    - For each High/Medium, propose a concrete follow‑up: extra tests, extra /guard run, smaller change, or manual review.
4. **Outputs**
    - “Skeptic report” with:
        - 3–7 findings, severity, and rationale.
        - 1–3 recommended actions (e.g., “Run /guard in deep mode on module X”, “Split this migration into two steps”, “Add test for scenario Y”).

***

### /ship – Delivery \& runtime feedback loop

**Purpose**
Give you a single place to see “can this safely go out / what just happened in prod?” and tie that back into your analysis and retros.

**When to use**

- Before deploying/releasing.
- After a deploy or incident, to ground /rr and /value in real runtime data.

**Inputs**

- Optional mode: `pre` (before deploy), `post` (after deploy), `status` (any time).
- Optional environment info if not auto‑detectable (branch, service name, environment).

**Core behavior**

1. **Signal gathering**
    - CI status: last pipeline results for current branch.
    - Tests: unit/integration status, flakiness if tracked.
    - Deploys: last deployment time \& target, previous vs current version.
    - Runtime: basic health metrics and recent errors/incidents (from logs/monitoring if wired).
2. **Safety summary**
    - For `pre`:
        - Summarize readiness: tests passing?, /guard recently run?, high‑risk changes present?
        - Simple “Ship readiness” classification: Ready / Caution / Blocked.
    - For `post`:
        - Summarize: new errors, latency/throughput changes, any rollbacks or alerts.
        - Tag “suspect changes” for deeper /analyze or /rr.
3. **Integration hooks**
    - Offer actions:
        - “Run /guard on this diff before shipping.”
        - “Open /value to see if this deployment aligns with your bets.”
        - “Start /rr focused on this deployment and recent incidents.”
4. **Outputs**
    - Concise dashboard‑style text:
        - Key CI/deploy/runtime facts.
        - Ship readiness or post‑deploy health verdict.
        - 2–3 suggested follow‑up steps.

***

### /garden – Knowledge hygiene \& promotion

**Purpose**
Keep your knowledge base (CKS + SKILL.md lessons) healthy: deduped, pruned, and focused on what you actually use.

**When to use**

- Periodically (e.g., weekly) or after heavy learning phases.
- When you notice CKS/skills starting to feel noisy or redundant.

**Inputs**

- Optional scope: `cks`, `skills`, or `all`.
- Optional time window (“this month”, “last 30 sessions”).

**Core behavior**

1. **Inventory \& usage stats**
    - Query CKS for entries by recency, usage frequency, and source.
    - Scan SKILL.md Neural Cache sections for lesson count, duplicates, and staleness.
2. **Issue detection**
    - Duplicates/near‑duplicates across CKS and SKILL.md.
    - Stale entries (never or rarely retrieved, referencing old workflows).
    - Hot entries (frequent retrieval, high value) that deserve promotion (e.g., to CLAUDE.md or explicit skill rules).
3. **Proposed gardening actions**
    - For duplicates: propose merge/simplify into a single canonical pattern.
    - For stale: propose archive or mark as “historical”.
    - For hot: propose promotion:
        - Update CLAUDE.md,
        - Add hooks/heuristics,
        - Adjust skills (/nav, /guard, /value) to lean on them.
4. **Outputs**
    - Short report with three sections:
        - “Prune/merge” candidates (with suggested new canonical text).
        - “Promote” candidates (with suggested destination and impact).
        - “Optional cleanups” (things that won’t hurt to leave, but could be tidied).
    - Each item clearly marked with suggested action so you can quickly approve/edit.

***

If you’d like, next step I can draft skeleton SKILL.md files for these four (description, triggers, dependencies, step list) in a format you can drop straight into `P:\.claude\skills\`.

---

# Here's more info.

❯ decompose the skills you highlighted into their component functions, like before.
⎿  UserPromptSubmit hook error

● Read 3 files (ctrl+o to expand)

● Complete Skills Decomposition

---
/vdate-deploy (Deploy Verification) Components

┌─────┬───────────────────────┬───────────────────────────────────────────────┬────────────
────┐
│ \# │ Component │ Function │ Dependencies │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 1 │ Git Status Checker │ git status, uncommitted changes │ Git CLI │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 2 │ Branch Verifier │ Verifies correct branch for deployment │ Git CLI │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 3 │ Pass/Fail Evaluator │ Exit code 0=PASS, 1=FAIL │ \#1, \#2 │
└─────┴───────────────────────┴───────────────────────────────────────────────┴────────────
────┘
Key Feature: Pre-deploy gate - git cleanliness only

---
/r (QA Certification) Components

┌─────┬───────────────────────────┬─────────────────────────────────────────────────┬──────
───────────────────────────────┐
│ \# │ Component │ Function │ Dependencies │
├─────┼───────────────────────────┼─────────────────────────────────────────────────┼──────
───────────────────────────────┤
│ 1 │ Session Target Detector │ Detects target from conversation history │ Chat history,
recent edits, cwd │
├─────┼───────────────────────────┼─────────────────────────────────────────────────┼──────
───────────────────────────────┤
│ 2 │ Token Triage │ FAST (<5K) vs STANDARD (5-20K) vs CAREFUL (>20K) │ Available tokens │
├─────┼───────────────────────────┼─────────────────────────────────────────────────┼──────
───────────────────────────────┤
│ 3 │ Phase 1: Sanity Check │ pytest, coverage, bandit │ pytest, coverage, bandit │
├─────┼───────────────────────────┼─────────────────────────────────────────────────┼──────
───────────────────────────────┤
│ 4 │ Phase 2: E2E Test │ Playwright user journeys │ Playwright (native Python) │
├─────┼───────────────────────────┼─────────────────────────────────────────────────┼──────
───────────────────────────────┤
│ 5 │ Phase 3: Chaos Test │ hypothesis, schemathesis, locust │ hypothesis, schemathesis,
locust │
├─────┼───────────────────────────┼─────────────────────────────────────────────────┼──────
───────────────────────────────┤
│ 6 │ Phase 4: Report Generator │ qa_report.md with verdict │ \#3, \#4, \#5 │
├─────┼───────────────────────────┼─────────────────────────────────────────────────┼──────
───────────────────────────────┤
│ 7 │ Next Steps Router │ Deploy / Optimize / Return to build │ qa_report.md verdict │
└─────┴───────────────────────────┴─────────────────────────────────────────────────┴──────
───────────────────────────────┘
Key Feature: 4-phase safety net (Sanity → E2E → Chaos → Report)

---
/verify (Implementation Verification) Components

┌─────┬───────────────────────┬───────────────────────────────────────────────┬────────────
────┐
│ \# │ Component │ Function │ Dependencies │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 1 │ Scope Detector │ Changed files this session or specific file │ Session history, file
arg │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 2 │ Tier Selector │ T1 only, T1+T2, or T1+T2+T3 │ User arg or default │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 3 │ T1: Syntax Checker │ ast.parse() for broken code │ Python AST │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 4 │ T2: Type/Lint Checker │ mypy --strict, ruff │ mypy, ruff │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 5 │ T3: Test Runner │ pytest for related tests │ pytest │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 6 │ Result Summarizer │ Overall PASS/FAIL with tier breakdown │ \#3, \#4, \#5 │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 7 │ Next Steps Recommender │ /test, /comply, /qa │ Test results │
└─────┴───────────────────────┴───────────────────────────────────────────────┴────────────
────┘
Key Feature: 3-tier verification (Syntax → Types → Tests)

---
/cleanup (Directory Structure Cleanup) Components

┌─────┬───────────────────────┬───────────────────────────────────────────────┬────────────
────┐
│ \# │ Component │ Function │ Dependencies │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 1 │ Path Violation Scanner │ Uses path_validator.py to detect violations │
path_validator.py │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 2 │ Directory Policy Reader │ Loads directory_policy.json │ directory_policy.json │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 3 │ Violation Reporter │ Shows violations with reasons and suggestions │ \#1, \#2 │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 4 │ Git-Tracked Detector │ Detects git-tracked files (requires override) │ Git CLI │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 5 │ Interactive Handler │ Per-file approval (move/delete/skip/quit) │ cleanup.py │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 6 │ Action Executor │ Move or delete based on user choice │ User approval │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 7 │ Compliance Verifier │ Re-validates after cleanup │ path_validator.py │
└─────┴───────────────────────┴───────────────────────────────────────────────┴────────────
────┘
Key Feature: Git-tracked file protection + per-file approval

---
/health-monitor (System Health) Components

┌─────┬───────────────────────┬───────────────────────────────────────────────┬────────────
────┐
│ \# │ Component │ Function │ Dependencies │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 1 │ Real-Time Memory Checker │ psutil.Process().memory_info().rss │ psutil │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 2 │ Memory Threshold Evaluator │ ≤500MB (healthy), 500-1000MB (moderate), >1000MB (high)
│ \#1 │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 3 │ Hook Health Checker │ Exit codes: 0 (healthy), 1 (unhealthy), 2 (critical), 3
(changed) │ hook_health_check.py │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 4 │ Database Health Checker │ CKS + Session Memory checks │ CKS DB files │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 5 │ API Endpoint Validator │ OpenRouter, Gemini, Groq, GitHub key validation │ API keys │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 6 │ Severity Classifier │ Critical vs Warning vs Info │ \#2, \#3, \#4, \#5 │
├─────┼───────────────────────┼───────────────────────────────────────────────┼────────────
────┤
│ 7 │ Remediation Advisor │ Specific action recommendations │ \#6 │
└─────┴───────────────────────┴───────────────────────────────────────────────┴────────────
────┘
Key Feature: Real-time measurement (no cached JSON for memory)

---
/cognitive-frameworks (Cognitive Enhancement) Components

┌─────┬──────────────────────────┬──────────────────────────────────────────────────┬──────
──────────────────────────┐
│ \# │ Component │ Function │ Dependencies │
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 1 │ Context Checker │ /q context staleness detection │ lib.q_context.read_context() │
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 2 │ Cynefin Classifier │ Clear/Complicated/Complex/Chaotic domain │ Problem description,
logs │
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 3 │ Inversion Analyzer │ Failure mode identification ("What could go wrong?") │
Proposal/plan │
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 4 │ Hanlon's Razor Assessor │ Malice vs stupidity vs bug │ Investigation evidence │
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 5 │ Chesterton's Fence Review │ Git history search for "why code exists" │ Git log, blame
│
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 6 │ Devil's Advocate Stress-Test │ Counterarguments: strongest objection, stakeholder
impact │ Proposal │
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 7 │ Framework Router │ Selects frameworks based on context (arch, rca, refactor) │
Trigger command │
├─────┼──────────────────────────┼──────────────────────────────────────────────────┼──────
──────────────────────────┤
│ 8 │ Output Formatter │ Structured markdown with all framework analyses │ \#2, \#3, \#4, \#5,
\#6 │
└─────┴──────────────────────────┴──────────────────────────────────────────────────┴──────
──────────────────────────┘
Key Feature: 5 cognitive frameworks (Cynefin, Inversion, Hanlon, Chesterton, Devil's
Advocate)

---
Domain Overlap Analysis
┌───────────────────────┬───────────┬───────────────────────────┬─────────────────────────┐
│    Existing Skill     │ Proposed  │     Shared Components     │           Gap           │
│                       │   Skill   │                           │                         │
├───────────────────────┼───────────┼───────────────────────────┼─────────────────────────┤
│                       │           │ Sanity checks, test       │ CI/CD status,           │
│ /r (QA)               │ /ship     │ runner, report generator  │ production runtime      │
│                       │           │                           │ feedback                │
├───────────────────────┼───────────┼───────────────────────────┼─────────────────────────┤
│ /vdate-deploy         │ /ship     │ Git status, branch        │ Pipeline integration,   │
│                       │           │ verification              │ rollback safety         │
├───────────────────────┼───────────┼───────────────────────────┼─────────────────────────┤
│ /verify               │ /ship     │ Tiers                     │ Deployment readiness    │
│                       │           │ (syntax/types/tests)      │ summary                 │
├───────────────────────┼───────────┼───────────────────────────┼─────────────────────────┤
│ /cleanup              │ /garden   │ Directory scanning,       │ CKS deduplication,      │
│                       │           │ violation detection       │ SKILL.md pruning        │
├───────────────────────┼───────────┼───────────────────────────┼─────────────────────────┤
│                       │           │ Real-time measurement,    │ WIP tracking, fatigue   │
│ /health-monitor       │ /pace     │ threshold evaluation      │ signals, "slow down"    │
│                       │           │                           │ recommendations         │
├───────────────────────┼───────────┼───────────────────────────┼─────────────────────────┤
│                       │           │ Devil's Advocate          │ AI output focus,        │
│ /cognitive-frameworks │ /skeptic  │ stress-test, evidence     │ hallucination detection │
│                       │           │ validation                │                         │
├───────────────────────┼───────────┼───────────────────────────┼─────────────────────────┤
│                       │           │                           │ Cognitive load          │
│ /cognitive-frameworks │ /pace     │ Context awareness         │ tracking, session       │
│                       │           │                           │ fatigue                 │
└───────────────────────┴───────────┴───────────────────────────┴─────────────────────────┘
Key Insight

Existing skills provide strong foundations:

- /r + /vdate-deploy + /verify → 80% of /ship covered
- /cleanup → File hygiene (not knowledge hygiene)
- /cognitive-frameworks → Decision frameworks (not load tracking)

Truly new domains:

- /pace → No WIP/fatigue tracking exists
- /skeptic → No AI-output skepticism exists (Devil's Advocate is close but broader)
- /garden → No CKS/SKILL.md knowledge hygiene exists

---

update the table with this new info.  In the notes cell, include use case examples.

Here’s the updated, collapsed skill set with the new decomposition information folded in and concrete use‑case examples.

### Final skills, mapped to existing components

| Domain | Final skill(s) | Features (existing + new) | Notes \& use cases |
| :-- | :-- | :-- | :-- |
| Execution navigation \& gating | **/nav** | Session context reader, git state analyzer, conversation analyzer, scope detector (absorbs /focus), constitutional filter, action generator, threshold routing (Strategic/Mixed/Problem), DUF check orchestration, artifact audit, plan detection, issue counting, context writer. | Use when you want “what should I do next?” at a session or project level; e.g., after a big coding block, run `/nav` to get a prioritized next‑step list plus suggestions to run /guard, /value, /rr, or /ship where appropriate. |
| Pre‑change risk \& quality | **/guard** | Uses /duf + parts of /analyze: transcript parser, change classifier, 19 DUF checks, pre‑mortem/inversion/rollback checks, action item generator, effectiveness tracker, constitutional filter, recommendation reporter. | Use before risky changes or merges; e.g., after implementing a major refactor, run `/guard` to surface “what will fail?”, how to roll back, and concrete safety actions before you ship. |
| Deep analysis \& strategy | **/analyze**, **/think** | /analyze: target detector, mode selector, focus lenses (risk, gaps, quality, security), phase orchestrator, UAF framework, constitutional filter, recommendation reporter. /think: context checker, internal 12‑section framework, section selector, recommendation distiller, second‑order analyzer, complexity tax assessor, approval waiter. | Use `/analyze` for focused code/system analysis (e.g., “analyze this diff for security and correctness before review”); use `/think` when deciding *how* to approach a bigger architectural or product decision (“should I introduce service X or refactor Y?”). |
| Value \& product impact | **/value** | Existing /value: git diff scanner, value pattern matcher (Leverage Point, Asymmetric Upside, Network Effect, Optionality, Flywheel), impact assessor, opportunity presenter. New: lightweight “bet” capture (hypothesis, metric), and “impact review” after /ship or runtime changes, with CKS integration. | Use right after coding but before/after deploy to ask “is this actually high‑leverage?”; e.g., `/value` on a diff to spot asymmetric upside, or after a feature goes live to assess if it’s worth further investment. |
| Post‑session reflection | **/rr**, **/retro**, **/reflect** | /rr: transcript reader, work summarizer, quality assessor, pattern extractor, follow‑up tracker, value analyzer, systemic change proposer, CKS auto‑storage. /retro: retro.py runner, segment extractor, SKILL.md reader/duplicate checker, lesson quality filter, lesson synthesizer, SKILL.md writer, write confirmer. /reflect: notification clearer, skill selector, signal detector/classifier, change proposer, skill file reader, change applier (with approval), git committer, observation saver. | Use `/rr` at the end of a work block to capture what happened, what worked/didn’t, and systemic changes (e.g., hooks/skills tweaks). Use `/retro` when you want to harvest lessons into SKILL.md after a meaningful event (RCA, major project). Use `/reflect` when a specific skill has been underperforming and you want to evolve its behavior. |
| Knowledge system \& history | **/cks**, **/chs** | /cks: daemon client, content type detector, CKS ingester, session extractor, FAISS searcher, CLI fallback. /chs: daemon checker, semantic searcher, CLI fallback, filter applier, result presenter, drill‑down offer. | Use `/cks` to store and retrieve patterns (e.g., “add this RCA pattern to CKS” or “fetch similar incidents”); use `/chs` to search past conversations (e.g., “when did we last debug a similar OpenRouter issue?”). |
| Delivery \& runtime feedback | **/ship** | Built from /vdate-deploy + /r + /verify: git status checker, branch verifier, pass/fail evaluator; session target detector; token triage (FAST/STANDARD/CAREFUL); 4‑phase QA (sanity: pytest/coverage/bandit; E2E: Playwright; chaos: hypothesis/schemathesis/locust); T1/T2/T3 verification (syntax, types, tests); qa_report generator; readiness summary; next‑steps router (Deploy/Optimize/Return to build). New: CI/CD pipeline status, deployment state, basic runtime signals, rollback hints. | Use before shipping or after a deploy. Example: `/ship pre` after tests pass to summarize git cleanliness, QA phases, and deployment readiness; or `/ship post` after a deploy to see if any new errors/perf regressions appeared and link into /rr or /value. |
| Cognitive load \& WIP | **/pace** | Combines new logic with /health-monitor signals: session duration \& activity stats; WIP metrics (uncommitted changes, branches); recent /guard findings and revert density; real‑time memory usage (psutil); memory threshold evaluator; hook health checker, DB health, API key checks; severity classifier; remediation advisor. New: load score (Low/Med/High), WIP/fatigue interpretation, and specific “slow down / slice / stop” recommendations plus suggested gates (e.g., require /guard). | Use when you feel scattered or it’s getting late; e.g., `/pace` after a 3‑hour sprint to see “Pace: HIGH – multiple branches, lots of changes, higher memory and error density → recommend /cooldown + small, safe commit instead of a big new change.” |
| Human–AI safety \& interaction | **/skeptic** | Built on /cognitive-frameworks: context checker, Cynefin classifier, inversion analyzer, Hanlon’s Razor assessor, Chesterton’s Fence review, Devil’s Advocate stress‑test, framework router, output formatter. New: specifically target AI‑generated plans/diffs/analyses; highlight unsupported claims, missing coverage, overreach vs instructions, and hallucination risks; propose concrete checks (tests, /guard, /analyze). | Use right after a large AI plan or diff before you trust it; e.g., `/skeptic` on a proposed refactor plan to get “here’s where this overreaches, here are untested edge cases, and here’s what to verify with /guard or extra tests.” |
| Portfolio \& roadmap | **/roadmap** | Aggregates from /rr, /value, /ship, /cks: themes/epics tracking, time/effort allocation, “bets” and their outcomes, surfaced from CKS patterns and deployment history. | Use weekly/monthly to steer your solo portfolio; e.g., `/roadmap` to see which themes are actually getting time and which ones are paying off (based on /value and /ship data), then adjust your next week’s focus. |
| Knowledge hygiene | **/garden** | Extends /cleanup’s pattern (scanner, policy reader, reporter, interactive handler, action executor, verifier) from files to knowledge: inventory of CKS entries by recency/usage; SKILL.md lesson scan; duplicate/near‑duplicate detection; stale vs hot entry detection; suggested merges/archives/promotions; optional interactive approval. | Use periodically to keep your knowledge base sharp; e.g., `/garden all` to find duplicate lessons across CKS and SKILL.md, archive stale patterns from old workflows, and promote a few high‑value patterns into CLAUDE.md or into explicit skill rules. |
| Session closure | **/cooldown** | Wraps /rr + light /retro hooks + task list integration: final work summary, follow‑up extraction to task list, optional SKILL.md lesson extraction, CKS updates, context reset. | Use at end of day or after a big push; e.g., `/cooldown` to close open loops, create a clear “tomorrow’s first task”, and store any high‑value lessons to /cks or SKILL.md so you can safely switch contexts. |

If you want, next step I can draft concrete SKILL.md skeletons for `/pace`, `/skeptic`, `/ship`, and `/garden` that map directly to your existing components and expected behaviors.

---

# please update the table to include the functions.  I'm looking to reorganize the skills, so I'll remove redundancies, but I want to make sure we know where the functions are going.

Here’s the updated table with explicit component functions mapped into each final skill, so you can see where everything lands before you dedupe.

### Skills → component functions mapping

| Domain | Final skill(s) | Component functions (mapped from existing skills) | Notes \& use cases |
| :-- | :-- | :-- | :-- |
| Execution navigation \& gating | **/nav** | From /nse + /q: Session Context Reader (WT_SESSION, session_activities JSON), Git State Analyzer (status, log), Conversation History Analyzer, Scope Intersector/Detector (git + session files, Code/Topic/Project), Constitutional Filter, Action Generator (priority‑ranked next steps), Output Formatter (NSE template), Session Activity Reader, Git State Verifier, Conversation Analyzer (topic‑based work detection), File Existence Checker, Artifact Auditor (PRD/ARD/CHANGELOG/README), Plan Detector (plans dir), Issue Counter, Threshold Router (Strategic/Mixed/Problem), DUF Check Orchestrator (calls /duf, /duf‑scan), NSE Gap Filler (fills remaining slots), Strategic Priority Generator (pre‑mortem questions), Context Writer (q_context.json). | Example: after a messy session, run `/nav` to read session/git/chat, detect scope, and output “here are your next 5 moves”, including whether to run /guard, /value, /rr, or /ship. |
| Pre‑change risk \& quality | **/guard** | From /duf + /analyze: Transcript Parser (extract_changed_files), Change Classifier (Trivial/Moderate/Significant/Major), Check Orchestrator (runs 19 cognitive checks), Pre‑Mortem Check (“what will fail?”), Inversion Check (“obvious risk?”), Rollback Check (“how to revert?”), Constitutional Filter, Action Item Generator (WHAT/WHY actions), Effectiveness Tracker; plus from /verify and /r: Scope Detector (changed files or arg), Tier Selector (T1/T2/T3), T1 Syntax Checker (ast.parse), T2 Type/Lint Checker (mypy, ruff), T3 Test Runner (pytest), Result Summarizer, Session Target Detector, Token Triage (FAST/STANDARD/CAREFUL), Phase 1 Sanity (pytest/coverage/bandit), Phase 2 E2E (Playwright), Phase 3 Chaos (hypothesis/schemathesis/locust), Phase 4 Report Generator (qa_report.md), Next Steps Router (Deploy/Optimize/Return). | Example: before merging a big refactor, run `/guard` to get DUF‑style failure scenarios, rollback plan, syntax/type/test verification, and a QA report telling you whether to ship or go back to build. |
| Deep analysis \& strategy | **/analyze**, **/think** | /analyze: Target Detector (git diff or file/path), Mode Selector (quick/standard/deep/council), Focus Lens Selector (risk/gaps/opportunities/quality/security), Phase Orchestrator, UAF Framework (analyze_uaf.py), Constitutional Filter, Recommendation Reporter. /think: Context Checker (q_context staleness), Framework Applier (internal 12‑section framework), Section Selector (routine vs architecture), Recommendation Distiller, Second‑Order Analyzer (what the change enables/risks), Complexity Tax Assessor, Approval Waiter. | Example: `/analyze` on a diff to get a multi‑lens risk/quality/security report; `/think` when choosing between two architectures, to get a distilled recommendation plus second‑order effects before committing. |
| Value \& product impact | **/value** | From /value + /rr: Git Diff Scanner, Pattern Matcher (Leverage Point, Asymmetric Upside, Network Effect, Optionality, Flywheel), Impact Assessor, Opportunity Presenter; from /rr: Value Analyzer (value created/lost/missed); new: Bet Recorder (hypothesis/metric/expected impact), Impact Reviewer (post‑/ship comparison of expected vs observed), CKS Writer/Reader hooks for value patterns. | Example: `/value` after implementing a feature to see if it’s a leverage point or low‑value; later run `/value` or a “review” mode after /ship to check whether the bet you recorded actually paid off and store the pattern in CKS. |
| Post‑session reflection | **/rr**, **/retro**, **/reflect** | /rr: Transcript Reader, Work Summarizer (files changed, ops count, purpose), Quality Assessor (what worked/didn’t), Pattern Extractor (repeat/avoid patterns), Follow‑up Tracker, Value Analyzer, Systemic Change Proposer (CLAUDE.md/hooks/skills), CKS Auto‑Storage (cks add). /retro: Retro Script Runner (retro.py), Segment Extractor (lesson‑worthy segments), SKILL.md Reader (Neural Cache), Duplicate Checker, Lesson Quality Filter (non‑obvious, pattern‑changing), Lesson Synthesizer (one‑line lessons), SKILL.md Writer, Write Confirmer. /reflect: Notification Clearer, Skill Selector, Signal Detector (corrections/successes/edge cases/preferences), Signal Classifier (HIGH/MED/LOW), Change Proposer (skill changes with confidence), Skill File Reader, Change Applier (Edit tool, user approval), Git Committer, Observation Saver. | Example: after a long debugging sprint, run `/rr` to summarize work and systemic improvements, `/retro` to extract a couple of neural‑cache lessons for affected skills, and `/reflect` on a specific skill that mis‑behaved to propose and apply improvements. |
| Knowledge system \& history | **/cks**, **/chs** | /cks: Daemon Client (semantic daemon interface), Content Type Detector (pattern/memory/code/document), CKS Ingester (CKS.ingest_*), Session Extractor (lessons from current session), FAISS Searcher (semantic search), CLI Fallback (cks_cli). /chs: Daemon Checker, Semantic Searcher (FAISS via daemon), CLI Fallback (chat_history_search.py), Filter Applier (session/context/ranking filters), Result Presenter (ranked results with scores), Drill‑Down Offer (/search-more). | Example: `/cks` to ingest an RCA outcome or refactor pattern; `/chs` when you vaguely remember “we debugged this kind of OpenRouter issue last month” and want to pull up that conversation quickly. |
| Delivery \& runtime feedback | **/ship** | From /vdate-deploy: Git Status Checker, Branch Verifier, Pass/Fail Evaluator. From /r: Session Target Detector, Token Triage, Phase 1 Sanity (pytest/coverage/bandit), Phase 2 E2E (Playwright), Phase 3 Chaos (hypothesis/schemathesis/locust), Phase 4 Report Generator (qa_report.md), Next Steps Router. From /verify: Scope Detector, Tier Selector, T1 Syntax Checker, T2 Type/Lint Checker, T3 Test Runner, Result Summarizer, Next Steps Recommender (/test, /comply, /qa). New: CI/CD Pipeline Status Reader, Deployment History Reader (last deploy, env), Runtime Health Snapshot (errors/latency if wired), Deploy Readiness Aggregator (Ready/Caution/Blocked), Post‑Deploy Health Comparator (pre vs post). | Example: run `/ship pre` on your main branch to verify git cleanliness, tests, QA phases, and CI state before deploying; run `/ship post` after a deploy to see if error rates or key metrics changed and whether to trigger /rr or /value. |
| Cognitive load \& WIP | **/pace** | From /health-monitor: Real‑Time Memory Checker (psutil RSS), Memory Threshold Evaluator (≤500/500–1000/>1000MB), Hook Health Checker (exit codes 0/1/2/3), Database Health Checker (CKS + session memory), API Endpoint Validator (OpenRouter/Gemini/Groq/GitHub keys), Severity Classifier, Remediation Advisor. New: Session Duration Analyzer (time active), WIP Analyzer (uncommitted changes, branches, pending tasks), Error/Revert Density Analyzer (recent fix/revert commits, /guard severity), Cognitive Load Scorer (Low/Medium/High), Behavior Router (normal vs constrained vs stop/park), Recommendation Generator (e.g., “run /cooldown”, “split work”, “run /guard before any more changes”). | Example: after 3–4 hours and several failed experiments, run `/pace` to get “Pace: HIGH” plus concrete guidance like “commit a small safe slice, postpone the risky migration, and run /cooldown instead of starting another big change.” |
| Human–AI safety \& interaction | **/skeptic** | From /cognitive-frameworks: Context Checker (/q context), Cynefin Classifier (clear/complicated/complex/chaotic), Inversion Analyzer (failure modes), Hanlon’s Razor Assessor (malice vs stupidity vs bug), Chesterton’s Fence Review (git history for why code exists), Devil’s Advocate Stress‑Test (strongest objections, stakeholder impact), Framework Router (based on context), Output Formatter (structured markdown). New: AI Output Reader (plan/diff/analysis ingestion), Evidence Checker (claims vs evidence), Coverage Checker (missing tests/edge cases), Overreach Detector (doing more than requested), Hallucination Risk Flagging, Follow‑up Action Suggester (tests, /guard, /analyze, manual review). | Example: after Claude proposes a large multi‑file refactor, run `/skeptic` on the plan to get a compact list of unsupported assumptions, missing checks, and recommended validation steps before you let the AI or yourself execute it. |
| Portfolio \& roadmap | **/roadmap** | Aggregators using existing functions: pulls Work Summarizer and Value Analyzer from /rr, value patterns from /value, deploy/runtime signals from /ship, patterns from /cks. New: Theme/Epic Catalog (group tasks and changes), Time/Effort Aggregator (what you actually worked on), Bet/Outcome Tracker (from /value bets and /ship results), Priority Recommender (which themes to focus/defer). | Example: weekly, run `/roadmap` to see which themes got the most effort, which bets paid off, and which areas /guard and /ship flagged as risky, then decide what your next week’s top 3 initiatives should be. |
| Knowledge hygiene | **/garden** | Inspired by /cleanup: Path/Entry Scanner (but over CKS entries \& SKILL.md lessons), Policy/Heuristic Reader (rules for dedupe/staleness), Violation/Issue Reporter (duplicates, stale entries, fragmentation), Interactive Handler (approve merge/archive/promote/skip), Action Executor (edit/merge/archive entries), Compliance/Consistency Verifier (re‑scan after actions). New: Usage Stats Analyzer (recency/frequency), Hot/Cold Classifier (high‑value vs stale), Promotion Suggester (promote key patterns to CLAUDE.md, hooks, or skill configs). | Example: run `/garden all` monthly to find duplicate lessons across skills, archive old patterns from workflows you no longer use, and promote 2–3 high‑impact patterns into CLAUDE.md or explicit rules so they’re applied automatically. |
| Session closure | **/cooldown** | Wraps /rr + light /retro + task integration: calls Transcript Reader and Work Summarizer, Quality Assessor, Follow‑up Tracker to extract next‑session tasks; optional Segment Extractor + Lesson Synthesizer for 1–2 quick SKILL.md lessons; CKS Auto‑Storage for high‑value patterns; Context Reset (clear notifications, mark session as closed). | Example: at the end of the night, run `/cooldown` to get “here’s what you did, here’s what to do first tomorrow, here are 1–2 lessons captured to CKS/SKILL.md”, then safely shut down without worrying you’ll forget key threads. |

If you want, next step I can propose a concrete “routing plan” for how to physically reorganize the existing skill files (e.g., which components to move under `/ship.md`, `/pace.md`, etc.) so you can implement this with minimal churn.

---

# Please update the table with the new info, as well as where each domain or proposed skill maps to SDLC.  Note the chat history I'm showing now include a plan, but we are not doing that plan, the LLM just really likes to make plans.

Below is an updated table that:

- Keeps the consolidated skills.
- Explicitly lists where each **existing component function** goes.
- Adds a column showing how each domain/skill maps to the **SDLC** (using broad phases: Requirements/Analysis, Design, Implementation, Verification \& Validation, Deployment/Operations, Maintenance/Improvement, Knowledge/Org learning).[^9_1][^9_2][^9_3]


### Skills → components → SDLC mapping

| Domain | Final skill | Component functions (existing + new) | SDLC phases covered | Notes \& example use cases |
| :-- | :-- | :-- | :-- | :-- |
| Execution navigation \& gating | **/nav** | From /nse + /q: Session Context Reader (WT_SESSION, session_activities), Git State Analyzer (status, log), Conversation History Analyzer, Scope Intersector/Detector (Code/Topic/Project), Constitutional Filter, Action Generator (priority‑ranked next steps), Output Formatter (NSE template), Session Activity Reader, Git State Verifier, Conversation Analyzer (topic‑based work detection), File Existence Checker, Artifact Auditor (PRD/ARD/CHANGELOG/README), Plan Detector (plans dir), Issue Counter, Threshold Router (Strategic/Mixed/Problem), DUF Check Orchestrator (/duf, /duf‑scan), NSE Gap Filler, Strategic Priority Generator, Context Writer (q_context.json). | Primarily: **Analysis**, **Implementation planning**, **Maintenance/Improvement**.[^9_1][^9_4] | Use mid‑session to answer “what now?”: `/nav` turns git/session/chat into a prioritized next‑step list (e.g., “tighten tests with /guard, then run /value, then consider /ship pre”). |
| Pre‑change risk \& quality | **/guard** | From /duf: Transcript Parser (extract_changed_files), Change Classifier (Trivial/Moderate/Significant/Major), Check Orchestrator (19 checks), Pre‑Mortem Check (“what will fail?”), Inversion Check, Rollback Check, Constitutional Filter, Action Item Generator, Effectiveness Tracker. From /verify: Scope Detector, Tier Selector (T1/T2/T3), T1 Syntax Checker (ast.parse), T2 Type/Lint Checker (mypy, ruff), T3 Test Runner (pytest), Result Summarizer, Next Steps Recommender. From /r: Session Target Detector, Token Triage, Phase 1 Sanity (pytest/coverage/bandit), Phase 2 E2E (Playwright), Phase 3 Chaos (hypothesis/schemathesis/locust), Phase 4 Report Generator (qa_report.md), Next Steps Router (Deploy/Optimize/Return). | Mainly: **Verification \& Validation**, plus **Implementation (pre‑commit)** and **Deployment readiness**.[^9_5][^9_6][^9_3] | Use before risky merges or deploys: `/guard` gives DUF‑style failure scenarios, rollback plan, syntax/type/test/QA verification, and a clear go/no‑go recommendation. |
| Deep analysis \& strategy | **/analyze** | Target Detector (git diff or file/path), Mode Selector (quick/standard/deep/council), Focus Lens Selector (risk/gaps/opportunities/quality/security), Phase Orchestrator, UAF Framework (analyze_uaf.py), Constitutional Filter, Recommendation Reporter. | **Analysis**, early **Design**, and **Verification** (reviewing a change for quality/security).[^9_1][^9_5] | Use `/analyze` when you want a multi‑lens read on a diff or module (e.g., “what are the main risks, gaps, and improvement opportunities before we lock this in?”). |
| Strategic thinking \& big decisions | **/think** | Context Checker (q_context staleness), Framework Applier (12‑section internal framework), Section Selector (routine vs architecture), Recommendation Distiller, Second‑Order Analyzer (what change enables/risks), Complexity Tax Assessor, Approval Waiter. | **Requirements/Problem shaping**, **Architecture/High‑level Design**, and **Governance/Decision making**.[^9_1][^9_7] | Use `/think` when deciding *how* to approach bigger shifts (e.g., “should I split this service, or keep it monolithic?”) and want a distilled recommendation plus second‑order consequences. |
| Value \& product impact | **/value** | From /value + /rr: Git Diff Scanner, Pattern Matcher (Leverage Point, Asymmetric Upside, Network Effect, Optionality, Flywheel), Impact Assessor, Opportunity Presenter, Value Analyzer (created/lost/missed). New: Bet Recorder (hypothesis/metric/expected impact), Impact Reviewer (compare expected vs observed after /ship), CKS hooks for value patterns. | Cross‑cuts **Requirements (value hypotheses)**, **Analysis**, and **Post‑Deployment Outcome Evaluation**.[^9_8][^9_9] | Use `/value` to decide if a change is worth doing and later to judge whether it actually moved the needle after /ship (feeding patterns into CKS). |
| Post‑session reflection | **/rr** | Transcript Reader, Work Summarizer (files changed, ops count, purpose), Quality Assessor, Pattern Extractor (repeat/avoid), Follow‑up Tracker, Value Analyzer, Systemic Change Proposer (CLAUDE.md/hooks/skills), CKS Auto‑Storage (cks add). | **Retrospective/Process Improvement** over the whole SDLC, esp. post‑implementation/post‑deployment.[^9_8][^9_10][^9_11] | Use `/rr` at natural stopping points to convert the session into patterns, value insights, and concrete follow‑ups for the next SDLC cycle. |
| Post‑session retro (lessons) | **/retro** | Retro Script Runner (retro.py), Segment Extractor (lesson‑worthy segments), SKILL.md Reader, Duplicate Checker, Lesson Quality Filter, Lesson Synthesizer (one‑liners), SKILL.md Writer, Write Confirmer. | **Knowledge/Org learning** aligned with retrospectives.[^9_8][^9_10] | Use `/retro` after particularly instructive sessions (e.g., an RCA) to mine “golden lessons” for SKILL.md. |
| Skill improvement | **/reflect** | Notification Clearer, Skill Selector, Signal Detector (corrections/successes/edge cases/preferences), Signal Classifier, Change Proposer, Skill File Reader, Change Applier (with approval), Git Committer, Observation Saver. | **Process/Tooling Maintenance \& Improvement** (meta‑SDLC for your skills).[^9_1] | Use `/reflect` when a specific skill underperforms (e.g., /nav or /guard mis‑fires) and you want a structured change proposal and commit. |
| Knowledge system | **/cks** | Daemon Client, Content Type Detector (pattern/memory/code/document), CKS Ingester (CKS.ingest_*), Session Extractor, FAISS Searcher, CLI Fallback. | **Knowledge/Org learning** – cross‑cutting repository across SDLC.[^9_12][^9_13][^9_14] | Use `/cks` to store patterns from /rr, /value, /ship, and to pull prior lessons when analyzing or designing. |
| Conversation history search | **/chs** | Daemon Checker, Semantic Searcher (FAISS via daemon), CLI Fallback (chat_history_search.py), Filter Applier, Result Presenter, Drill‑Down Offer. | Supports **Analysis, Design, Debugging, and Retrospectives** by reusing past conversations.[^9_12][^9_14] | Use `/chs` when you remember “we solved this before” and want to ground current SDLC work in prior reasoning. |
| Delivery \& runtime feedback | **/ship** | From /vdate-deploy: Git Status Checker, Branch Verifier, Pass/Fail Evaluator. From /r: Session Target Detector, Token Triage (FAST/STANDARD/CAREFUL), Phase 1 Sanity (pytest/coverage/bandit), Phase 2 E2E (Playwright), Phase 3 Chaos (hypothesis/schemathesis/locust), Phase 4 Report Generator (qa_report.md), Next Steps Router. From /verify: Scope Detector, Tier Selector, T1 Syntax Checker, T2 Type/Lint Checker, T3 Test Runner, Result Summarizer, Next Steps Recommender. New: CI/CD Pipeline Status Reader, Deployment History Reader, Runtime Health Snapshot (errors/latency), Deploy Readiness Aggregator (Ready/Caution/Blocked), Post‑Deploy Health Comparator. | **Deployment/Release**, **Operations/Runtime Monitoring**, and **Post‑Deployment Validation**.[^9_15][^9_9][^9_16][^9_17] | Use `/ship pre` to decide if a given change is truly deploy‑ready, and `/ship post` to see if the last deployment introduced new issues, then feed that into /rr and /value. |
| Cognitive load \& WIP | **/pace** | From /health-monitor: Real‑Time Memory Checker (psutil RSS), Memory Threshold Evaluator, Hook Health Checker (exit codes 0/1/2/3), Database Health Checker (CKS + session memory), API Endpoint Validator (OpenRouter, Gemini, Groq, GitHub keys), Severity Classifier, Remediation Advisor. New: Session Duration Analyzer, WIP Analyzer (branches, uncommitted files, pending tasks), Error/Revert Density Analyzer, Cognitive Load Scorer (Low/Med/High), Behavior Router (normal vs constrained vs stop/park), Recommendation Generator (e.g., “run /cooldown”, “split work”, “require /guard”). | Cross‑cuts **Implementation, Verification, and Maintenance**, but addresses **human factors** (keeping the solo dev effective).[^9_18][^9_19][^9_20][^9_21] | Use `/pace` when you feel overloaded or after long sessions to decide whether to continue, constrain changes, or move to /cooldown. It’s the SDLC “throttle” for you as the human in the loop. |
| Human–AI safety \& interaction | **/skeptic** | From /cognitive-frameworks: Context Checker (/q context), Cynefin Classifier, Inversion Analyzer, Hanlon’s Razor Assessor, Chesterton’s Fence Review, Devil’s Advocate Stress‑Test, Framework Router, Output Formatter. New: AI Output Reader (plan/diff/analysis ingestion), Evidence Checker, Coverage Checker, Overreach Detector, Hallucination Risk Flagger, Follow‑up Action Suggester (tests, /guard, /analyze, manual review). | Cross‑cuts **Design, Implementation planning, and Verification**, acting as an AI‑specific QA layer.[^9_19][^9_22][^9_23] | Use `/skeptic` after large AI‑generated plans/diffs to challenge assumptions and propose concrete validation steps before you let them influence the SDLC. |
| Portfolio \& roadmap | **/roadmap** | Aggregates from /rr (Work Summarizer, Value Analyzer), /value (value patterns, bets), /ship (deploy/runtime signals), /cks (stored patterns). New: Theme/Epic Catalog, Time/Effort Aggregator, Bet/Outcome Tracker, Priority Recommender. | **Portfolio/Program Management** above individual SDLC cycles: steering which requirements and projects you focus on.[^9_9][^9_24] | Use `/roadmap` weekly/monthly to realign your next SDLC cycles based on what actually consumed time and produced value or risk. |
| Knowledge hygiene | **/garden** | Inspired by /cleanup: Entry Scanner (over CKS entries \& SKILL.md lessons), Policy/Heuristic Reader, Issue Reporter (duplicates, stale entries, fragmentation), Git‑Tracked Detector analog (protect important entries), Interactive Handler (merge/archive/promote/skip), Action Executor, Consistency Verifier. New: Usage Stats Analyzer (recency/frequency via CKS/CHS), Hot/Cold Classifier, Promotion Suggester (to CLAUDE.md/hooks/skills), Demotion/Archive Suggester. | **Knowledge/Org learning maintenance** – keeps requirements/lessons/patterns clean and usable across SDLC.[^9_25][^9_14][^9_26] | Use `/garden` periodically to keep CKS and SKILL.md from turning into noise, ensuring the SDLC is driven by high‑quality, current patterns. |
| Session closure | **/cooldown** | Wraps /rr + light /retro + task integration: Work Summarizer, Quality Assessor, Follow‑up Tracker (task extraction), optional Segment Extractor + Lesson Synthesizer for 1–2 quick lessons, CKS Auto‑Storage, Context Reset (notifications, markers). | End‑of‑cycle **Retrospective**, **Maintenance**, and **Planning for the next iteration**.[^9_8][^9_10][^9_11] | Use `/cooldown` at the end of the day/iteration to close the loop on this SDLC slice and set up the next (clear first task, captured lessons, updated knowledge). |

This table is now explicit about:

- Where every decomposed component from `/vdate-deploy`, `/r`, `/verify`, `/cleanup`, `/health-monitor`, `/cognitive-frameworks`, `/nse`, `/q`, `/rr`, `/retro`, `/reflect`, `/value`, `/cks`, `/chs` ends up.
- How each **skill/domain lines up with SDLC phases**, so you can see coverage and avoid over‑building in one area.
<span style="display:none">[^9_27]</span>

<div align="center">⁂</div>

[^9_1]: https://www.computer.org/resources/software-engineering-process

[^9_2]: https://www.geeksforgeeks.org/software-engineering/software-engineering-classification-of-software-requirements/

[^9_3]: https://www.complianceonline.com/resources/software-verification-and-validation-overview-and-must-have-documents.html

[^9_4]: https://en.wikipedia.org/wiki/Agile_software_development

[^9_5]: https://builtin.com/software-engineering-perspectives/v-model

[^9_6]: https://www.sei.cmu.edu/blog/using-v-models-for-testing/

[^9_7]: https://www.zentao.pm/blog/the-software-development-v-model-1823.html

[^9_8]: https://www.larksuite.com/en_us/topics/project-management-methodologies-for-functional-teams/pre-mortem-for-software-development-teams

[^9_9]: https://articles.mergify.com/continuous-delivery-best-practices/

[^9_10]: https://www.scrum.org/resources/blog/pre-mortem-preventing-product-failure-it-strikes

[^9_11]: https://asana.com/resources/premortem

[^9_12]: https://deepnote.com/blog/semantic-search-using-faiss-and-mpnet

[^9_13]: https://kminsider.com/topic/semantic-search-in-knowledge-management/

[^9_14]: https://www.sinequa.com/resources/blog/knowledge-management-for-engineering-teams-in-the-era-of-data-driven-insights/

[^9_15]: https://www.opsmx.com/blog/6-pitfalls-to-avoid-for-an-effective-continuous-delivery/

[^9_16]: https://ijcem.in/wp-content/uploads/2024/09/A-REVIEW-OF-CONTINUOUS-INTEGRATION-AND-CONTINUOUS-DELIVERY-PRACTICES-IN-MODERN-SOFTWARE-DEVELOPMENT.pdf

[^9_17]: https://www.cto.mil/wp-content/uploads/2023/07/SWE-Guide-April2023.pdf

[^9_18]: https://www.linkedin.com/pulse/reducing-cognitive-load-software-development-ariel-pérez-1pyze

[^9_19]: https://www.itprotoday.com/software-development/cognitive-load-in-the-age-of-ai-rethinking-developer-workflows

[^9_20]: https://www.agileanalytics.cloud/blog/reducing-cognitive-load-the-missing-key-to-faster-development-cycles

[^9_21]: https://idelsoft.com/blog/tpost/rnno6h72v1-how-cognitive-load-affects-developer-pro

[^9_22]: https://lucvandonkersgoed.com/2025/02/09/are-humans-the-limiting-factor-in-ai-assisted-software-development/

[^9_23]: https://thoughtbot.com/blog/ai-led-or-human-led-coding-you-decide

[^9_24]: https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/engineering-productivity-governance-and-improvement-in-software-delivery

[^9_25]: https://asem.org/blog/13411293

[^9_26]: https://rosap.ntl.bts.gov/view/dot/78009/dot_78009_DS1.pdf

[^9_27]: paste.txt


---

# I'm not getting a good sense for the flow.  Can you show some mermaid or ascii flows of end to end use cases?

Here are a few end‑to‑end flows showing how the skills actually compose in practice. These are text/mermaid‑style so you can drop them into docs or SKILL.md comments.[^10_1][^10_2]

***

## 1) Implementing and shipping a feature (happy path)

```mermaid
flowchart TD

A[Idea / task chosen] --> B[/nav: where to start?]
B --> C[/pace: am I safe to go deep?]

C -->|OK| D[Implement changes]
C -->|High load| C1[/guard: smaller, safer slice or stop/park]

D --> E[/guard: pre-change risk & quality]
E -->|Issues found| E1[Fix issues] --> E
E -->|Acceptable risk| F[/value: is this worth it?]

F -->|Low value| F1[Adjust scope or deprioritize]
F -->|Good value| G[/ship pre: ready to deploy?]

G -->|Blocked| G1[Return to D or E based on report]
G -->|Ready| H[Deploy]

H --> I[/ship post: runtime & regressions]
I -->|Problems| I1[/analyze: deep dive on failure] --> I2[/guard: extra checks or rollback]
I -->|Healthy| J[/rr: session reflection]

J --> K[/retro (optional): extract SKILL.md lessons]
J --> L[/cks: store patterns & bets]
J --> M[/cooldown: close session and set up next steps]
```

Narrative:

- Use **/nav** to pick up the right task and context.
- Check your **cognitive state** with **/pace** before going deep.
- After coding, run **/guard** to do DUF + verification tiers.
- Use **/value** to confirm it’s a worthwhile change, then **/ship pre/post** for deployment and runtime feedback.
- Close with **/rr**, optionally **/retro**, and knowledge capture via **/cks**, wrapped in **/cooldown**.

***

## 2) High‑risk AI‑assisted refactor

```mermaid
flowchart TD

A[Refactor request] --> B[/nav: identify scope & files]
B --> C[AI generates refactor plan/diff]

C --> D[/skeptic: challenge AI output]
D -->|High-risk findings| D1[Revise plan or narrow scope] --> C
D -->|Acceptable with checks| E[/guard: DUF + syntax/types/tests + QA]

E -->|Problems| E1[Fix, rerun /guard] --> E
E -->|OK| F[/ship pre: readiness, CI, branch, git clean]

F -->|Blocked| F1[Back to E or C]
F -->|Ready| G[Deploy small batch]

G --> H[/ship post: check for regressions]
H -->|Issues| H1[/analyze: targeted risk & root causes] --> H2[Rollback or patch via /guard]
H -->|Clean| I[/rr: reflect on AI-assisted change]
I --> J[/retro (if big lesson): add to SKILL.md]
I --> K[/cks: store AI-specific patterns & skeptic findings]
I --> L[/cooldown]
```

Key points:

- **/skeptic** sits between AI output and **/guard** to catch hallucinations, missing tests, and overreach.
- **/guard** then enforces pre‑mortem and verification.
- **/ship** handles deployment, and **/rr + /retro + /cks** ensure you evolve how you use AI over time.

***

## 3) Debugging a production incident and learning from it

```mermaid
flowchart TD

A[Incident detected] --> B[/ship status/post: runtime snapshot]
B --> C[/nav: identify affected code & context]
C --> D[/chs: find similar past incidents/conversations]
D --> E[/analyze: multi-lens analysis on suspect changes]

E --> F[/guard: DUF + verification on fixes]
F -->|High risk fix| F1[/think: is workaround or rollback better?] --> F2[Choose strategy]

F --> G[Deploy fix or rollback] --> H[/ship post: confirm recovery]

H --> I[/rr: capture what happened, what worked, what to change]
I --> J[/retro: extract lessons from this incident]
J --> K[/cks: ingest incident patterns (failure, detection, resolution)]
I --> L[/garden (later): merge/clean redundant incident patterns]
I --> M[/cooldown: close incident work]
```

This shows how:

- **/ship** gives the operational view.
- **/nav, /chs, /analyze, /guard** drive the technical fix cycle.
- **/rr, /retro, /cks, /garden** turn the incident into durable knowledge.

***

## 4) Weekly portfolio / roadmap review (solo PM/tech‑lead mode)

```mermaid
flowchart TD

A[Start weekly review] --> B[/roadmap: aggregate work & value]
B --> C[Read signals from /rr, /value, /ship, /cks]

C --> D[/think: analyze strategic tradeoffs]
D --> E[/value: scan planned changes for leverage]
E --> F[Update roadmap: themes, bets, priorities]

F --> G[/nav: seed next week's first actions]
G --> H[/cks: store updated bets & roadmap context]
H --> I[/garden (periodic): prune stale roadmap/CKS entries]
```

Here:

- **/roadmap** sits atop all other signals.
- **/think + /value** help you choose what’s worth doing next.
- **/nav** then translates that into concrete next SDLC cycles.

***

## 5) Cognitive‑load‑aware workday (human‑centric flow)

```mermaid
flowchart TD

subgraph Morning block
A[Open editor] --> B[/nav: pick starting task]
B --> C[/pace: initial load check]
C -->|OK| D[Deep work]
end

subgraph Midday
D --> E[/pace: re-evaluate load]
E -->|High| F[/cooldown (mini): summarize & park]
E -->|Medium| G[/guard on current work, then small commit]
end

subgraph Afternoon
G --> H[/nav: next small slice]
H --> I[Implement]
I --> J[/ship pre/post if shipping]
J --> K[/rr: short reflection]
K --> L[/cooldown: end-of-day closure]
end
```

This illustrates:

- **/pace** gating how deep you go at different times.
- **/nav, /guard, /ship, /rr, /cooldown** forming a daily SDLC micro‑loop.

***

If you tell me which of these flows feels closest to your typical day (feature work vs refactor vs incident vs planning), I can tighten one diagram into a “canonical solo SDLC loop” that you can literally paste into CLAUDE.md and refer to when designing hooks and auto‑invocations.
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_16][^10_3][^10_4][^10_5][^10_6][^10_7][^10_8][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://pg.ucsd.edu/publications/how-programmers-ASCII-diagram-code_CHI-2024.pdf

[^10_2]: https://asciidiagrams.github.io

[^10_3]: paste.txt

[^10_4]: https://asciiflow.com

[^10_5]: https://www.reddit.com/r/programming/comments/1cccdti/taking_ascii_drawings_seriously_how_programmers/

[^10_6]: https://www.youtube.com/watch?v=k0im1A-bmkg

[^10_7]: https://www.free-power-point-templates.com/articles/how-to-make-a-text-diagram-using-ascii-flow-tool/

[^10_8]: https://www.harness.io/blog/software-development-life-cycle-phases

[^10_9]: https://www.scatterspoke.com/retrospective-library/pre-mortem-retrospective/

[^10_10]: https://unito.io/blog/sdlc-methodology-guide/

[^10_11]: https://www.scatterspoke.com/retrospective-library/pre-mortem-retrospective

[^10_12]: https://stackoverflow.com/questions/2713336/are-ascii-diagrams-worth-my-time

[^10_13]: https://lucid.co/templates/sdlc-functional-process-flow-example

[^10_14]: https://www.mountaingoatsoftware.com/blog/use-a-pre-mortem-to-identify-project-risks-before-they-occur

[^10_15]: https://www.reddit.com/r/programming/comments/ejkid/diagrams_through_ascii_art/

[^10_16]: https://www.virtasant.com/blog/sdlc-methodologies


---

# I can't read those.

Here are the same flows in very plain, linear text, no diagrams.

***

## Flow 1: Implement and ship a feature

1. You pick a task or idea.
2. You run **/nav**: it looks at git + session + chat and tells you what to work on and in what order.
3. You run **/pace**: it checks how long you’ve been working, how many changes/branches you have, error density, etc., and tells you whether it’s safe to keep going normally or if you should slow down or park work.
4. You implement the change (edit code, write tests, etc.).
5. You run **/guard**: it runs DUF checks, syntax/type/test tiers, and 4‑phase QA as needed, then tells you if the change is risky and how to mitigate.
6. You run **/value**: it analyzes the diff for value patterns (is this worth it, is it leverage, etc.) and optionally records a “bet” (what you expect this change to achieve).
7. You run **/ship pre**: it checks git cleanliness, branches, CI/tests, QA status, and gives you a deploy readiness verdict (ready / caution / blocked).
8. If ready, you deploy.
9. You run **/ship post**: it checks runtime health (errors, metrics) and tells you if the deploy looks healthy or needs investigation.
10. You run **/rr**: it summarizes what you did, what worked/didn’t, and suggests systemic improvements and follow‑ups.
11. Optionally, you run **/retro** to extract a couple of SKILL.md lessons, and **/cks** to store important patterns.
12. You run **/cooldown** to close the session and set up very clear next actions for next time.

***

## Flow 2: High‑risk AI‑assisted refactor

1. You decide you want a larger refactor.
2. You run **/nav** to identify the right scope and files to touch.
3. You ask an AI to propose a refactor plan or diff.
4. You run **/skeptic** on that AI output: it looks for missing evidence, missing tests/edge cases, overreach, and hallucination‑like behavior, and suggests extra checks.
5. You adjust or narrow the plan based on /skeptic’s feedback.
6. You apply the refactor (manually or via AI tools).
7. You run **/guard** to do DUF checks and verification tiers (syntax, types, tests, QA).
8. You run **/ship pre** to see if it’s really safe to deploy this refactor.
9. If it’s safe, you deploy.
10. You run **/ship post** and check if anything regressed (errors, performance).
11. If something looks wrong, you run **/analyze** on the diff or area and possibly **/guard** again to decide whether to roll back or patch.
12. You run **/rr** to reflect on how the AI‑assisted refactor went, then optionally **/retro** and **/cks** to capture AI‑specific lessons.
13. You use **/cooldown** to close out the refactor work.

***

## Flow 3: Debug a production incident

1. You notice an incident (alerts, errors, etc.).
2. You run **/ship** (status or post mode) to get a snapshot of the current runtime state and recent deploys.
3. You run **/nav** to figure out which code and context are most relevant (recent changes, topics).
4. You run **/chs** to search for similar past incidents or discussions.
5. You run **/analyze** on the suspect change or area to understand risks and likely failure modes.
6. You implement a fix or choose a rollback strategy (you can call **/think** here if you need help choosing between options).
7. You run **/guard** on the fix to check for risks and ensure tests/QA are in a good state.
8. You deploy the fix or rollback.
9. You run **/ship post** again to confirm that runtime looks healthy.
10. You run **/rr** to capture what broke, how you fixed it, and what needs to change in your process or tooling.
11. You run **/retro** to extract a small set of reusable lessons, and **/cks** to store them as patterns (failure, detection, resolution).
12. Later, you run **/garden** to merge or tidy incident‑related entries in CKS and SKILL.md.
13. You run **/cooldown** to close the incident and reset.

***

## Flow 4: Weekly roadmap / portfolio review

1. At the start of your weekly review, you run **/roadmap**.
2. /roadmap pulls in data from **/rr**, **/value**, **/ship**, and **/cks** to show where your time went, which bets paid off, and where risk or incident hotspots are.
3. You run **/think** to reason about strategic trade‑offs (what to focus on next, what to pause).
4. You run **/value** on planned changes or themes to see which ones look most promising.
5. You update your roadmap (themes, epics, priorities) with the help of /roadmap’s recommendations.
6. You run **/nav** to seed the next concrete tasks you’ll pick up in the coming days.
7. You call **/cks** to store updated bets and strategy.
8. Occasionally, you run **/garden** to clean up old roadmap entries and stale patterns so the next review stays sharp.

***

## Flow 5: Cognitive‑load‑aware workday

1. At the beginning of the day, you run **/nav** to choose a starting task and load relevant context.
2. You run **/pace** to check your current load and get a recommendation about how deep to go (e.g., fine for deep work vs keep things small).
3. You work on the chosen task (coding, design, etc.).
4. After one or two blocks of work, you run **/pace** again:
    - If load is low/medium, it may recommend continuing with some guardrails (e.g., smaller commits, run /guard periodically).
    - If load is high, it recommends a mini‑**/cooldown** or at least committing/parking work instead of starting something big.
5. When you’re ready to ship something, you run **/guard** and **/ship** as needed.
6. At the end of the day, you run **/rr** for reflection, optionally **/retro** and **/cks** for lessons, and finally **/cooldown** to close out and set tomorrow’s first move.

If you tell me which of these flows is closest to your current reality (feature work, refactor, incidents, or weekly planning), I can collapse just that one into a super‑tight “canonical solo loop” with the minimal set of skills you actually need on muscle memory.
<span style="display:none">[^11_1]</span>

<div align="center">⁂</div>

[^11_1]: paste.txt


---

# here's my thoughts for flow 1:

I have an idea
i use /prd to flesh out the idea maybe
i use /arch or /design to come up with a solution
i use /plan to plan it
i use /ask-olymp or /duf to review it, or /advesarial-review\

Answer skipped.

---

# here's my thoughts for flow 1:

I have an idea
i use /prd to flesh out the idea maybe
i use /arch or /design to come up with a solution
i use /plan to plan it
i use /ask-olymp or /duf to review it, or /advesarial-review it
now that I have a plan, I can use /tdd or /cwo to implement it, tasks will get created as needed.
i'll then use /v or /duf to check it, then fix the findings.
then eventually publishit on github.

What am I or you missing?

You’re not missing much; your flow already hits most SDLC phases cleanly. The gaps are mainly around value/bets, runtime feedback, and cognitive/human‑ops.[^13_1][^13_2]

Here’s your flow, annotated with what’s covered and what’s missing:

1. **Idea → /prd (flesh out idea)**
    - SDLC: Planning + Requirements analysis.[^13_3][^13_1]
    - Looks good. This is where you clarify scope, constraints, and acceptance criteria.
2. **/arch or /design (solution/architecture)**
    - SDLC: Architecture + Design.[^13_2][^13_1]
    - Good coverage for “how should we build this?”. Ensure /arch pulls from past failures via CKS when relevant.
3. **/plan (implementation plan)**
    - SDLC: Detailed design + implementation planning.[^13_2]
    - This is where you define phases, tasks, and sometimes test strategy. You’re solid here.
4. **/ask-olymp or /duf or /adversarial-review (review the plan)**
    - SDLC: Pre‑mortem / risk analysis / design review.[^13_4][^13_5][^13_6]
    - This is excellent pre‑change risk work. /duf gives “what will fail?”, adversarial review gives challenge/Devil’s‑Advocate coverage.
5. **/tdd or /cwo to implement, tasks auto‑created**
    - SDLC: Implementation with TDD loop (Red‑Green‑Refactor).[^13_7][^13_8][^13_9][^13_10]
    - Great, especially if /tdd enforces “write test → see it fail → implement → refactor” at small increments.
6. **/v or /duf to check, then fix findings**
    - SDLC: Verification \& Validation, mostly at the code/feature level.[^13_11][^13_12][^13_7]
    - /v (= /verify) gives syntax/types/tests; /duf gives higher‑order failure scenarios and rollback thinking.
7. **Publish on GitHub**
    - SDLC: Deployment (to your public repo) and the very start of maintenance.[^13_13][^13_1][^13_2]

### What’s missing or weak

I’d call out five main gaps:

1. **Value/bet framing and post‑deployment impact**
    - You don’t have an explicit step where you say: “This feature is a bet to achieve X (metric, outcome) by doing Y.”[^13_1][^13_2]
    - After you publish, there’s no “did this actually produce the value I expected?” loop.

Minimal fix:
    - Before /plan (or at the end of /prd), call **/value** (or a light “/bet”) to:
        - Capture a one‑sentence bet and metric.
    - After some usage or after deployment plus whatever data you have, call **/value** again in “review” mode to compare expected vs observed, then store that in CKS.
2. **Runtime / operational feedback**
    - “Publish to GitHub” is not the same as “in prod and behaving well”. There’s no explicit CI/CD or runtime health check in your flow.[^13_14][^13_15][^13_16][^13_17]
    - If you deploy to a running system, you want a quick “did we break anything?” step.

Minimal fix:
    - Add **/ship pre** right before deploy (or right before merge) to check git cleanliness, CI, tests, and QA.
    - Add **/ship post** after deploy to check runtimes/logs/monitoring (even if rudimentary) and feed that into /rr or /value.
3. **Cognitive‑load / human‑ops gating**
    - You don’t have a point where you decide “should I even attempt this level of complexity right now?”.[^13_18][^13_19][^13_20][^13_21]
    - For you as a solo/AI‑assisted dev, this is where things actually fall over (fatigue → sloppy design or bad deploy).

Minimal fix:
    - At the start of the work block (after the idea and /prd), call **/pace** once:
        - If load is high, shrink the scope or stop at /plan and defer implementation.
    - Optionally call /pace again before big risky steps (like the final /duf + deploy).
4. **Systematic reflection and learning**
    - You have very strong “micro‑verification” (/v, /duf), but your default flow doesn’t explicitly mention **/rr, /retro, /cks**.
    - Without them, you get less compound learning across features/projects.[^13_22][^13_23][^13_24][^13_25]

Minimal fix:
    - After you publish (or after /ship post if you add it), run **/rr** as a lightweight default.
    - For particularly interesting features or problems, follow with **/retro** and **/cks**.
5. **Navigation across multiple threads / WIP**
    - Your flow describes one project cleanly, but not “what happens when I have 4 half‑finished flows at once?”.
    - That’s where **/nav** (session navigator) becomes central and ensures you finish things instead of starting new ones.

### A tightened version of your Flow 1 (with minimal additions)

Here’s your flow with only the smallest extra steps:

1. Idea.
2. **/prd** – flesh out requirements.
3. **/value (bet mode)** – define what success looks like for this feature.
4. **/arch or /design** – design/architecture.
5. **/plan** – detailed implementation and test plan (optionally referencing the bet/value).
6. **/ask-olymp or /duf or /adversarial-review** – pre‑mortem / adversarial design review.
7. **/pace** – check cognitive load; if high, shrink scope or stop at a smaller slice.
8. **/tdd or /cwo** – implement with tests and code.
9. **/v and/or /duf** – verify and pre‑mortem the implementation.
10. **/ship pre** – CI, tests, git state, readiness to deploy.
11. Publish / deploy.
12. **/ship post** – basic runtime health.
13. **/value (review mode)** – did we get the value we expected from step 3?
14. **/rr** – reflect on the work and note systemic improvements.
15. **/retro (optional)** – SKILL.md lessons.
16. **/cks** – store important patterns (requirements, design, failure, value).
17. **/cooldown** – close the session, set next actions.

If you want, I can compress this into a super‑short “checklist version” you could paste into CLAUDE.md and then mark which steps are mandatory vs optional so it stays usable day‑to‑day.
<span style="display:none">[^13_26][^13_27][^13_28]</span>

<div align="center">⁂</div>

[^13_1]: https://www.harness.io/blog/software-development-life-cycle-phases

[^13_2]: https://saigontechnology.com/blog/6-stages-for-software-development-procedure-you-need-to-know/

[^13_3]: https://www.geeksforgeeks.org/software-engineering/software-development-life-cycle-sdlc/

[^13_4]: https://www.mountaingoatsoftware.com/blog/use-a-pre-mortem-to-identify-project-risks-before-they-occur

[^13_5]: https://www.scatterspoke.com/retrospective-library/pre-mortem-retrospective/

[^13_6]: https://www.scatterspoke.com/retrospective-library/pre-mortem-retrospective

[^13_7]: https://code.visualstudio.com/docs/copilot/guides/test-driven-development-guide

[^13_8]: https://developer.ibm.com/articles/5-steps-of-test-driven-development/

[^13_9]: https://martinfowler.com/bliki/TestDrivenDevelopment.html

[^13_10]: https://en.wikipedia.org/wiki/Test-driven_development

[^13_11]: https://www.testrail.com/blog/test-driven-development/

[^13_12]: https://circleci.com/blog/test-driven-development-tdd/

[^13_13]: https://www.microsoft.com/en-ca/power-platform/topics/phases-of-the-software-development-lifecycle

[^13_14]: https://www.opsmx.com/blog/6-pitfalls-to-avoid-for-an-effective-continuous-delivery/

[^13_15]: https://articles.mergify.com/continuous-delivery-best-practices/

[^13_16]: https://ijcem.in/wp-content/uploads/2024/09/A-REVIEW-OF-CONTINUOUS-INTEGRATION-AND-CONTINUOUS-DELIVERY-PRACTICES-IN-MODERN-SOFTWARE-DEVELOPMENT.pdf

[^13_17]: https://www.cto.mil/wp-content/uploads/2023/07/SWE-Guide-April2023.pdf

[^13_18]: https://www.linkedin.com/pulse/reducing-cognitive-load-software-development-ariel-pérez-1pyze

[^13_19]: https://www.itprotoday.com/software-development/cognitive-load-in-the-age-of-ai-rethinking-developer-workflows

[^13_20]: https://www.agileanalytics.cloud/blog/reducing-cognitive-load-the-missing-key-to-faster-development-cycles

[^13_21]: https://idelsoft.com/blog/tpost/rnno6h72v1-how-cognitive-load-affects-developer-pro

[^13_22]: https://www.larksuite.com/en_us/topics/project-management-methodologies-for-functional-teams/pre-mortem-for-software-development-teams

[^13_23]: https://www.scrum.org/resources/blog/pre-mortem-preventing-product-failure-it-strikes

[^13_24]: https://asana.com/resources/premortem

[^13_25]: https://www.sinequa.com/resources/blog/knowledge-management-for-engineering-teams-in-the-era-of-data-driven-insights/

[^13_26]: paste.txt

[^13_27]: https://tweag.github.io/agentic-coding-handbook/WORKFLOW_TDD/

[^13_28]: https://www.reddit.com/r/ClaudeCode/comments/1qd64xx/tdd_workflows_with_claude_code_whats_actually/


---

# please create skills for :

1. /ship [R:2] - New deploy readiness aggregator
2. /pace [R:2] - Cognitive load + WIP tracking (extends /health-monitor)
3. /skeptic [R:1] - AI output validation (NEW, standalone)
4. /cooldown [R:1] - Session closure wrapper (simple composition)
5. /garden [R:2] - Knowledge hygiene (NEW)

Below are concise SKILL.md‑style specs for the five skills, focused on behavior and composition rather than implementation details.

***

## 1. `/ship` – Deploy readiness \& runtime snapshot

**Purpose**
Aggregate git, verification, QA, and (optionally) pipeline/runtime signals into a single “ship readiness” or “post‑deploy health” verdict.[^14_1][^14_2][^14_3][^14_4]

**When to use**

- Before merging or deploying a change.
- After a deploy to check for regressions.

**Inputs**

- Optional mode: `pre`, `post`, or `status` (default: infer from context).
- Optional: target branch/service/env if not obvious from cwd.

**Dependencies / components reused**

- `/vdate-deploy`:
    - Git Status Checker (clean vs dirty).
    - Branch Verifier (on correct branch?).
    - Pass/Fail Evaluator.
- `/verify`:
    - Scope Detector (changed files).
    - Tier Selector (T1/T2/T3).
    - T1 Syntax Checker (ast.parse).
    - T2 Type/Lint Checker (mypy, ruff).
    - T3 Test Runner (pytest).
    - Result Summarizer + Next Steps Recommender.
- `/r` (QA certification):
    - Session Target Detector.
    - Token Triage (FAST/STANDARD/CAREFUL).
    - Phase 1: Sanity (pytest/coverage/bandit).
    - Phase 2: E2E (Playwright).
    - Phase 3: Chaos (hypothesis/schemathesis/locust).
    - Phase 4: Report Generator (qa_report.md).
    - Next Steps Router (Deploy/Optimize/Return to build).
- New:
    - CI/CD pipeline status reader.
    - Deployment history reader (last deploy, env).
    - Runtime health snapshot (errors/latency if available).
    - Readiness Aggregator (Ready/Caution/Blocked).
    - Post‑deploy health comparator (pre vs post).

**Behavior**

- **pre mode**

1. Run `/vdate-deploy` to confirm clean git and correct branch.
2. Run `/verify` at least T1+T2, optionally T3.
3. If “full QA” requested or high risk, run `/r` (or at least Phase 1).
4. Pull CI/CD status for current branch.
5. Aggregate into a single verdict: Ready / Caution / Blocked, with a short checklist.
- **post mode**

1. Identify the last deployment for this branch/service.
2. Compare key metrics and logs (errors, latency, health checks) before vs after.
3. Summarize any regressions or anomalies and suggest actions (rollback, /analyze, /guard).

**Outputs**

- Short “ship report” with:
    - Git \& branch status.
    - Verify + QA phases run and results.
    - CI/CD status and last deploy info.
    - Runtime health summary.
    - Final verdict and 2–3 recommended next actions.

***

## 2. `/pace` – Cognitive load \& WIP tracking

**Purpose**
Protect you from overloading yourself by tracking WIP, session duration, error/revert density, and system strain, then adjusting how aggressively you should work.[^14_5][^14_6][^14_7][^14_8]

**When to use**

- At the start of a work block.
- After a long sprint or when you feel scattered.

**Inputs**

- Optional free‑text note: “I feel scattered / tired / hyperfocused”, etc.
- Implicit: session activity, git state, recent /guard or /ship outputs.

**Dependencies / components reused**

- From `/health-monitor`:
    - Real‑Time Memory Checker (psutil RSS).
    - Memory Threshold Evaluator.
    - Hook Health Checker (exit codes 0/1/2/3).
    - Database Health Checker (CKS + session memory).
    - API Endpoint Validator (OpenRouter/Gemini/Groq/GitHub).
    - Severity Classifier.
    - Remediation Advisor.
- New:
    - Session Duration Analyzer (time since start, since last break).
    - WIP Analyzer (uncommitted files, active branches, number of active tasks).
    - Error/Revert Density Analyzer (recent “fix”/“revert” commits, /guard severity).
    - Cognitive Load Scorer: Low / Medium / High.
    - Behavior Router:
        - Low: normal.
        - Medium: constrained (smaller changes, more frequent /guard).
        - High: recommend stopping/parking or only doing safe maintenance.
    - Recommendation Generator.

**Behavior**

1. Collect signals: session duration, WIP metrics, revert/error density, memory, hook/DB/API health.
2. Compute a simple load score (Low/Medium/High) with reasons.
3. Choose a behavior mode and suggest 2–3 concrete actions, such as:
    - “Proceed normally; consider /guard after next chunk.”
    - “Commit a small slice, run /guard, avoid starting new features.”
    - “Run /cooldown and stop new risky changes; only do low‑risk cleanup.”

**Outputs**

- “Pace report” that explains your state and prescribes specific actions, not just a label.

***

## 3. `/skeptic` – AI output validation

**Purpose**
Be a focused, skeptical reviewer of AI‑generated plans, diffs, and analyses, with special attention to hallucinations, missing evidence, and overreach.[^14_6][^14_9][^14_10]

**When to use**

- After a large AI plan, refactor, or design recommendation.
- Before you act on or deploy AI‑heavy changes.

**Inputs**

- Required: target to scrutinize (file / buffer / diff / last tool output).
- Optional: risk context (e.g., “security‑sensitive”, “data‑loss risk”).

**Dependencies / components reused**

- From `/cognitive-frameworks`:
    - Context Checker (/q context).
    - Cynefin Classifier (clear/complicated/complex/chaotic).
    - Inversion Analyzer (what could go wrong).
    - Hanlon’s Razor Assessor.
    - Chesterton’s Fence Review (git history “why”).
    - Devil’s Advocate Stress‑Test (strongest objections, stakeholder impacts).
    - Framework Router.
    - Output Formatter.
- New, AI‑specific:
    - AI Output Reader (parse plan/diff/analysis).
    - Evidence Checker (claims vs backing evidence).
    - Coverage Checker (missing tests/edge cases, unstated constraints).
    - Overreach Detector (doing more than requested or changing unrelated areas).
    - Hallucination Risk Heuristics (e.g., references to non‑existent files/APIs).
    - Follow‑up Action Suggester.

**Behavior**

1. Read the AI output and classify the context (Cynefin).
2. Apply inversion, Chesterton, and Devil’s Advocate lenses to the proposal.
3. Look for:
    - Unbacked claims.
    - Missing obvious tests/edge cases.
    - Conflicts with existing code or constraints (using git history with Chesterton).
    - Signs of hallucination.
4. Rate findings (High/Medium/Low) and suggest concrete mitigations: extra tests, /guard run, narrower plan, manual review, or alternative approaches.

**Outputs**

- Short “skeptic report” with:
    - 3–10 findings (with severity and rationale).
    - 2–3 recommended actions before you accept or ship the AI output.

***

## 4. `/cooldown` – Session closure wrapper

**Purpose**
Provide a simple, predictable “end of session” ritual that closes loops, saves learnings, and sets up the next session.

**When to use**

- End of day / night.
- After a long or intense session.

**Inputs**

- Optional: short summary from you (“today’s main focus was X”, “I feel done halfway through Y”).

**Dependencies / components reused**

- `/rr`:
    - Transcript Reader, Work Summarizer, Quality Assessor, Pattern Extractor, Follow‑up Tracker, Value Analyzer, Systemic Change Proposer, CKS Auto‑Storage.
- `/retro` (optional):
    - Segment Extractor, Lesson Quality Filter, Lesson Synthesizer, SKILL.md Writer.
- `/cks`: for storing particularly important patterns.

**Behavior**

1. Run a constrained `/rr` focusing on this session:
    - What did we do?
    - What worked/didn’t?
    - What follow‑ups are needed (tasks)?
2. Offer an optional mini‑`/retro` if the session looks lesson‑rich (e.g., big bug, new technique).
3. Write any high‑value patterns into CKS.
4. Produce a “tomorrow’s first actions” list (1–3 items).
5. Optionally flag high‑value items for `/garden` or `/roadmap` later.

**Outputs**

- Compact “cooldown summary”:
    - Session recap.
    - Next‑session starting points.
    - Any stored lessons/patterns.

***

## 5. `/garden` – Knowledge hygiene

**Purpose**
Keep CKS and SKILL.md healthy by cleaning duplicates, pruning stale entries, and promoting high‑value patterns.[^14_11][^14_12][^14_13]

**When to use**

- Periodically (e.g., weekly).
- After a burst of intense learning (many /rr, /retro, /cks writes).

**Inputs**

- Optional scope: `cks`, `skills`, or `all`.
- Optional time window (e.g., “last 30 days”).

**Dependencies / components reused**

- From `/cleanup`:
    - Scanner (but over CKS entries and SKILL.md lessons instead of paths).
    - Policy Reader (directory_policy → knowledge‑policy equivalent).
    - Reporter (issues + suggestions).
    - Interactive Handler (approve/skip/quit).
    - Action Executor.
    - Verifier.
- New:
    - CKS Query for Duplicates/Similar Entries.
    - SKILL.md Lesson Scanner (Neural Cache sections).
    - Usage Frequency Analyzer (via CKS/CHS search logs).
    - Staleness Detector (age + low usage).
    - Hot Pattern Detector (high usage, high value).
    - Promotion Suggester (to CLAUDE.md, hooks, skill configs).
    - Archive/Demotion Suggester.

**Behavior**

1. Inventory knowledge: pull a sample of CKS entries and SKILL.md lessons based on scope/time.
2. Detect:
    - Near‑duplicate entries.
    - Stale items (old + rarely used).
    - Hot items (frequently used or recently high‑impact).
3. Propose actions per item: merge, archive, keep, or promote.
4. Optional interactive mode to confirm actions.
5. Re‑scan to confirm the knowledge base looks cleaner, and report a brief summary.

**Outputs**

- “Garden report” summarizing:
    - What was merged, archived, or promoted.
    - Any remaining TODOs for a future gardening pass.

***

If you’d like, next we can turn each of these into a concrete SKILL.md file layout (title, description, triggers, step list, dependencies) ready to drop into `P:\.claude\skills\`.
<span style="display:none">[^14_14][^14_15][^14_16][^14_17][^14_18][^14_19][^14_20][^14_21][^14_22][^14_23][^14_24][^14_25][^14_26][^14_27][^14_28][^14_29]</span>

<div align="center">⁂</div>

[^14_1]: https://www.opsmx.com/blog/6-pitfalls-to-avoid-for-an-effective-continuous-delivery/

[^14_2]: https://articles.mergify.com/continuous-delivery-best-practices/

[^14_3]: https://ijcem.in/wp-content/uploads/2024/09/A-REVIEW-OF-CONTINUOUS-INTEGRATION-AND-CONTINUOUS-DELIVERY-PRACTICES-IN-MODERN-SOFTWARE-DEVELOPMENT.pdf

[^14_4]: https://www.cto.mil/wp-content/uploads/2023/07/SWE-Guide-April2023.pdf

[^14_5]: https://www.linkedin.com/pulse/reducing-cognitive-load-software-development-ariel-pérez-1pyze

[^14_6]: https://www.itprotoday.com/software-development/cognitive-load-in-the-age-of-ai-rethinking-developer-workflows

[^14_7]: https://www.agileanalytics.cloud/blog/reducing-cognitive-load-the-missing-key-to-faster-development-cycles

[^14_8]: https://idelsoft.com/blog/tpost/rnno6h72v1-how-cognitive-load-affects-developer-pro

[^14_9]: https://lucvandonkersgoed.com/2025/02/09/are-humans-the-limiting-factor-in-ai-assisted-software-development/

[^14_10]: https://thoughtbot.com/blog/ai-led-or-human-led-coding-you-decide

[^14_11]: https://asem.org/blog/13411293

[^14_12]: https://www.sinequa.com/resources/blog/knowledge-management-for-engineering-teams-in-the-era-of-data-driven-insights/

[^14_13]: https://rosap.ntl.bts.gov/view/dot/78009/dot_78009_DS1.pdf

[^14_14]: paste.txt

[^14_15]: https://www.reddit.com/r/ChatGPTPromptGenius/comments/13dt71x/i_made_a_prompt_template_for_learning_any_skill/

[^14_16]: https://www.promptingguide.ai/introduction/examples

[^14_17]: https://www.aiforwork.co/prompt-articles/chatgpt-prompt-career-coach-personal-development-create-a-skills-analysis-report-89060

[^14_18]: https://pointerpro.com/skills-assessment-template/

[^14_19]: https://mcpmarket.com/tools/skills/skill-integration-templates

[^14_20]: https://stevekinney.com/courses/ai-development/test-driven-development-with-claude

[^14_21]: https://tweag.github.io/agentic-coding-handbook/

[^14_22]: https://www.reddit.com/r/ChatGPTPromptGenius/comments/1iwzbzk/i_have_crafted_the_universal_prompt_to_master_any/

[^14_23]: https://www.reddit.com/r/ClaudeAI/comments/1lnbcb5/code_claude_how_can_i_create_a_workflow_tdd_it/

[^14_24]: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

[^14_25]: https://faculty.risepoint.com/ai-prompt-templates-and-examples-for-authentic-assessments/

[^14_26]: https://www.reddit.com/r/ClaudeAI/comments/1n67d3f/my_claude_code_workflow_tdd_with_small_commits/

[^14_27]: https://www.youtube.com/watch?v=X2ciJedw2vU

[^14_28]: https://dextralabs.com/blog/prompt-engineering-templates/

[^14_29]: https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/


---

# yes please

Below are SKILL.md‑style skeletons you can drop into `P:\.claude\skills\`. Adjust paths/filenames to match your repo.

***

## 1. `P:\.claude\skills\ship.md`

```markdown
# /ship – Deploy Readiness & Runtime Snapshot

## Purpose

Aggregate git, verification, QA, CI/CD, and basic runtime signals into a single “ship readiness” or “post‑deploy health” verdict.

## When to Use

- Before merging or deploying a change (`/ship pre`).
- After deploying a change (`/ship post`).
- Any time you want to see current readiness/health (`/ship status`).

## Inputs

- Optional mode (natural language or arg):
  - `pre` – pre‑deploy readiness.
  - `post` – post‑deploy health.
  - `status` – current status (auto‑detected if not provided).
- Optional: branch/service/environment if not obvious from cwd.

## Dependencies

- Skills:
  - `/vdate-deploy` – git cleanliness and branch verification.
  - `/verify` – T1/T2/T3 verification (syntax/types/tests).
  - `/r` – 4‑phase QA certification (sanity/E2E/chaos/report).
- Tools/CLI:
  - Git CLI.
  - Test/QA tooling (pytest, coverage, bandit, Playwright, hypothesis, schemathesis, locust).
  - CI/CD API or CLI (if available).
  - Basic logs/metrics endpoints (optional).

## High‑Level Behavior

1. **Mode detection**
   - Infer `pre`, `post`, or `status` from user request and context.
   - If ambiguous, ask: “Pre‑deploy check, post‑deploy health, or status snapshot?”

2. **Pre‑deploy (`pre`) flow**
   - Run `/vdate-deploy` to confirm:
     - Git status is clean.
     - On the expected branch.
   - Run `/verify`:
     - At least T1+T2.
     - Optionally T3 if changes are non‑trivial or user requests full verification.
   - Optionally run `/r`:
     - At least Phase 1 (sanity).
     - Full suite if risk is high or user requests full QA.
   - Query CI/CD:
     - Latest pipeline status for current branch.
   - Aggregate into a single readiness verdict:
     - Ready / Caution / Blocked.
     - Include a short checklist explaining why.

3. **Post‑deploy (`post`) flow**
   - Identify last deployment for current branch/service.
   - Compare key metrics before vs after deploy:
     - Error rates, latency, basic health checks (if available).
   - Detect regressions or anomalies.
   - Suggest next actions:
     - Investigate with `/analyze` or `/guard`.
     - Consider rollback.
     - Capture an incident note for `/rr` if needed.

4. **Status flow**
   - Provide a combined summary of:
     - Current git/verify/QA/CI state.
     - Recent deployments and basic runtime health.
   - No hard go/no‑go verdict; this is informational.

## Output Format

- Concise “ship report” including:
  - Mode: pre/post/status.
  - Git & branch status (clean/dirty, branch name).
  - Verify tiers run and results.
  - QA phases run and results (if applicable).
  - CI/CD status summary.
  - Runtime health summary (post/status).
  - Final verdict (Ready/Caution/Blocked for `pre`, Healthy/Watch/Degraded for `post`).
  - 2–3 recommended next actions.

## Notes

- Prefer small, actionable suggestions over long narratives.
- Do not auto‑deploy; only assess and recommend.
```


***

## 2. `P:\.claude\skills\pace.md`

```markdown
# /pace – Cognitive Load & WIP Tracking

## Purpose

Track cognitive load, WIP, rework, and system health to decide whether to:
- Continue normally.
- Constrain work (smaller changes, mandatory gates).
- Stop or park work and run cooldown/closure.

## When to Use

- At the start of a work block.
- After long or intense sessions.
- When you feel scattered, tired, or tempted to “just do one more big change”.

## Inputs

- Optional free‑text context:
  - e.g., “I’ve been at this for 3 hours”, “I keep thrashing”, “I feel fine”.
- Implicit:
  - Session start time and activity log.
  - Git status/log.
  - Recent `/guard` or `/ship` outcomes.

## Dependencies

- Skills:
  - `/health-monitor` – system health, memory, DB, API checks.
- Data:
  - Session activity tracker (duration, operations count).
  - Git CLI (branches, uncommitted files, recent commits).
  - Task list (if available).
  - Recent `/guard` and `/ship` reports (if any).

## High‑Level Behavior

1. **Signal collection**
   - Session duration (now - first event / last cooldown).
   - WIP:
     - Number of modified files.
     - Number of active branches.
     - Count of open tasks for this session/project.
   - Rework:
     - Count of recent “fix”/“revert” commits.
     - Recent `/guard` issue counts/severity (if available).
   - System health via `/health-monitor`:
     - Memory usage levels.
     - Hook health.
     - DB health.
     - API key health.

2. **Load scoring**
   - Compute a simple score:
     - Low load – short session, low WIP, low rework, healthy system.
     - Medium load – moderate WIP, some rework, possibly rising memory.
     - High load – long session, high WIP, multiple reverts/fixes, issues from `/health-monitor`.

3. **Behavior routing**
   - For **Low**:
     - Recommend continuing; maybe suggest a future `/pace` checkpoint.
   - For **Medium**:
     - Recommend:
       - Smaller commits.
       - Running `/guard` on significant changes.
       - Avoiding new major features.
   - For **High**:
     - Recommend:
       - Stop starting new risky work.
       - Run `/cooldown` and/or checkpoint with a small commit.
       - If user insists on proceeding, suggest mandatory `/guard` and reduced scope.

4. **Action recommendations**
   - Provide 2–3 concrete actions:
     - e.g., “Commit current work and run /cooldown”, “Split this into a smaller slice and run /guard before continuing”.

## Output Format

- “Pace report” containing:
  - Load level (Low/Medium/High).
  - Key contributing signals (duration, WIP, rework, system health).
  - 2–3 specific recommended next actions.

## Notes

- Keep output short and directive.
- Never force action; always present clear options.
```


***

## 3. `P:\.claude\skills\skeptic.md`

```markdown
# /skeptic – AI Output Validation

## Purpose

Act as a skeptical reviewer of AI-generated plans, diffs, and analyses, with emphasis on:
- Evidence.
- Coverage (tests, edge cases).
- Overreach and unintended changes.
- Hallucination risk.

## When to Use

- After receiving a large AI plan or diff.
- Before acting on AI-heavy recommendations or merging AI-generated changes.

## Inputs

- Required:
  - Target to inspect:
    - A plan file.
    - A diff.
    - The last tool output.
- Optional:
  - Risk tags:
    - e.g., “security-sensitive”, “data-loss risk”, “performance-critical”.

## Dependencies

- Skills:
  - `/cognitive-frameworks` – Cynefin, inversion, Chesterton’s fence, Devil’s Advocate, etc.
- Data:
  - Git history / blame (for Chesterton’s fence).
  - Relevant code and tests for the target area.

## High‑Level Behavior

1. **Context & artifact loading**
   - Determine the artifact to critique (plan, diff, or narrative).
   - Identify relevant code and tests (if needed).

2. **Framework‑based analysis**
   - Use Cynefin to characterize problem domain.
   - Apply inversion (“what could go wrong if we follow this?”).
   - Use Chesterton’s fence to check whether the change removes or alters existing logic without understanding why it exists.
   - Use Devil’s Advocate to generate strongest objections and stakeholder impacts.

3. **AI-specific checks**
   - Evidence:
     - Highlight claims without clear support (e.g., “this improves performance” with no measurement).
   - Coverage:
     - Identify missing tests, edge cases, or non‑covered failure paths.
   - Overreach:
     - Identify changes that go beyond request scope or touch unrelated modules.
   - Hallucination:
     - Spot references to non‑existent files, APIs, or patterns not present in the repo.

4. **Findings and actions**
   - Summarize findings with severity:
     - High / Medium / Low.
   - Propose concrete actions:
     - Add tests for specific scenarios.
     - Run `/guard` for deeper risk analysis.
     - Narrow the change.
     - Discard or re‑request the plan if hallucinations dominate.

## Output Format

- “Skeptic report” including:
  - Brief context summary.
  - List of findings (each with severity, description, and rationale).
  - 2–3 actionable next steps.

## Notes

- Focus on *where to be careful*, not rewriting the entire plan.
- Can be chained with `/guard` and `/ship` for high‑risk flows.
```


***

## 4. `P:\.claude\skills\cooldown.md`

```markdown
# /cooldown – Session Closure Wrapper

## Purpose

Provide a small, consistent end-of-session ritual to:
- Summarize what happened.
- Capture follow-ups and lessons.
- Store important patterns.
- Set up the next session.

## When to Use

- At the end of the day.
- After finishing a significant chunk of work or an incident.

## Inputs

- Optional short note from you:
  - e.g., “Today was focused on X feature”, “We debugged Y bug”.

## Dependencies

- Skills:
  - `/rr` – session reflection.
  - `/retro` – lesson extraction to SKILL.md (optional).
  - `/cks` – pattern storage.

## High‑Level Behavior

1. **Session summary via `/rr`**
   - Invoke `/rr` in a constrained, session‑only mode:
     - Summarize work done.
     - Note what worked and what didn’t.
     - Identify follow‑up items.

2. **Lesson extraction (optional)**
   - If the session appears lesson‑rich (RCA, tricky bug, new pattern):
     - Offer to run `/retro` to add 1–3 new lessons to SKILL.md.
   - Otherwise, skip or suggest doing `/retro` later.

3. **Knowledge storage**
   - Use `/cks` to store:
     - Important patterns.
     - Value insights.
     - Key decision summaries.

4. **Next‑session setup**
   - Produce 1–3 “next session starting tasks” drawn from `/rr` follow‑ups.
   - Make them copy‑pastable or easy to drop into your task system.

5. **Closure**
   - Optionally mark the session as closed in your session_activity state.

## Output Format

- “Cooldown summary” including:
  - Brief recap of the session.
  - List of follow‑up tasks.
  - Notable lessons or patterns stored.
  - Suggested first action for next time.

## Notes

- Keep it short enough that using it never feels like a burden.
- Prefer explicit “Next session: 1)… 2)… ” bullets.
```


***

## 5. `P:\.claude\skills\garden.md`

```markdown
# /garden – Knowledge Hygiene

## Purpose

Keep your knowledge base (CKS + SKILL.md) clean and high‑signal by:
- Merging duplicates.
- Archiving stale entries.
- Promoting high‑value patterns.

## When to Use

- On a regular cadence (e.g., weekly).
- After periods with many new lessons or CKS entries.

## Inputs

- Optional scope:
  - `cks` – CKS entries only.
  - `skills` – SKILL.md lessons only.
  - `all` – both (default).
- Optional time window:
  - e.g., “last 30 days”, “this month”.

## Dependencies

- Skills / components:
  - CKS semantic search and metadata (timestamps, usage counts).
  - SKILL.md parser for Neural Cache or Lessons sections.
  - `/chs` (optional) for usage examples.

## High‑Level Behavior

1. **Inventory**
   - For the chosen scope/time window:
     - List CKS entries (id, title, created_at, last_used_at, usage_count).
     - List SKILL.md lessons (skill, section, text, last touched).

2. **Issue detection**
   - Duplicates or near‑duplicates:
     - Cluster by semantic similarity.
   - Stale entries:
     - Old + low usage or superseded patterns.
   - Hot entries:
     - Frequent usage, recent high value (e.g., mentioned in /rr, /value, /ship, /skeptic).

3. **Action proposals**
   - For each cluster or entry:
     - Duplicate clusters → propose a canonical merged version.
     - Stale entries → propose archive/demotion.
     - Hot entries → propose promotion:
       - E.g., move to CLAUDE.md, skill docs, or add as rule/heuristic.

4. **Interactive confirmation (optional)**
   - Present a concise list with actions:
     - `[merge]`, `[archive]`, `[keep]`, `[promote]`, `[skip]`.
   - Apply chosen actions:
     - Update CKS entries.
     - Edit SKILL.md.
     - Optionally log changes.

5. **Verification & summary**
   - Re‑scan a small sample to verify changes.
   - Output a short summary:
     - Number of merges, archives, promotions.
     - Notable promoted patterns.

## Output Format

- “Garden report” including:
  - Summary counts (merged/archived/promoted).
  - A brief list of key changes.
  - Optional recommended future gardening focus (e.g., a specific skill or topic that’s noisy).

## Notes

- Start conservative (more “propose” than “auto‑apply”).
- Over time, you can tighten heuristics once you trust the behavior.
```

If you want, I can now draft a tiny “how they fit” snippet for CLAUDE.md that explains in 5–6 lines when to reach for `/ship`, `/pace`, `/skeptic`, `/cooldown`, and `/garden` in your overall flow.
<span style="display:none">[^15_1]</span>

<div align="center">⁂</div>

[^15_1]: paste.txt

