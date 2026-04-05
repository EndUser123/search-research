# Changelog

All notable changes to the pre-mortem skill will be documented in this file.

## [Unreleased]

### Added
- **v6.0** (2026-03-31): Major enhancement release
  - Added Step-Back Prompting (Step 2 continued): First-principles grounding before specific failure enumeration. Each failure must cite the governing principle it violates.
  - Added ToT-lite cascade analysis (Step 2.5): Branch evaluation with sure/maybe/impossible labels (>70%/30-70%/<30%), highest-certainty path recommendation
  - Added Calibrated Confidence Prompting (Step 4): likelihood% (0-100), confidence% (0-100), uncertainty notes as mandatory output fields
  - Added Verbalized Sampling reference document (references/verbalized_sampling.md)
  - Added enforcement: advisory tier in SKILL.md frontmatter

### Fixed
- **v5.1.1** (2026-03-22): Critical documentation fixes from skill review
  - Fixed duplicate content bug (lines 47-51): Removed duplicate "Execute Framework Steps" block
  - Added Step 4.5 to Success Criteria: "Dependency cascades mapped if applicable (Step 4.5 - OPTIONAL)"
  - Added concrete dependency examples to Output Format section
  - Clarified retry logic documentation: Rewrote as "Agent Tool Behavior" to avoid confusion about manual implementation
  - Consolidated redundant "Default Target Detection" section: Now references Execution Workflow instead of duplicating content

### Added
- **v5.2** (2026-03-28): Added Step 2.7 temporal failure mode analysis
  - Added inline step after Step 2.6 checking for: LLM forgets requirement from 50 turns ago, context window exceeded, AI contradicts earlier decision
  - Warning sign: "what was the requirement again?"
  - Closes gap identified in ADR-20260327 session (breadcrumb verification was temporal failure)
  - **v5.2.1** (2026-03-28): Fixed off-by-one error in Step 2.7 - "> 50" excluded 50th turn; changed to "50 turns ago (or more)" per LOGIC-003
- **v5.1** (2026-03-22): Added Step 4.5 dependency cascade analysis (OPTIONAL)
  - Created `references/dependency-cascades.md` with complete methodology
  - Added inline annotation format for inter-risk dependencies ([causes], [blocks], [caused-by], [enables])
  - Documented keystone risk pattern: fix A resolves B+C+D
  - Clarified when to skip: most solo dev pre-mortems have independent risks
  - Distinguished structural dependencies from categorization (Step 3)
  - Updated Output Format section with dependency annotation examples
  - Anti-patterns documented: don't map "related to" or "similar domain"
- **v4.9** (2026-03-20): Fixed adversarial agent dispatch to match working implementation
  - Changed from Python loop pattern to explicit Agent() calls (one per line)
  - Fixed agent types: replaced `code-critic` (doesn't exist) with `adversarial-logic`
  - Fixed agent types: replaced `qa-engineer` (doesn't exist) with `adversarial-qa`
  - Added `adversarial-logic` for pure logic errors (matches planning skill)
  - Added file path references to prompts: "Review pre-mortem at <analysis_path>..."
  - Reference: P:\.claude\skills\planning\SKILL.md:205-210
  - Rationale: Loop pattern with try/except retry doesn't work with Agent tool subprocess wrapper

### Added
- **Execution Workflow section** (v4.7) - MANDATORY execution instructions when skill is invoked
  - Explicit Step 7 adversarial validation with parallel Agent() calls to all 8 agents
  - Auto-detection workflow for targets when no arguments provided
  - Step-by-step execution instructions for all 16 framework steps

### Fixed
- **Agent tool syntax** (v4.7.1) - Fixed adversarial agent dispatch pattern
  - Changed from loop-based `description=f"Adversarial review: {focus}"` to explicit Agent() calls
  - Each agent now has brief description ("Compliance review") and detailed prompt
  - Removed `model="haiku"` to use default model
  - Pattern now matches working implementation in planning skill (P:\.claude\skills\planning\SKILL.md:205-210)

### Changed
- **Execution Workflow section** (v4.7) - MANDATORY execution instructions when skill is invoked
  - Explicit Step 7 adversarial validation with parallel Agent() calls to all 8 agents
  - Auto-detection workflow for targets when no arguments provided
  - Step-by-step execution instructions for all 16 framework steps

### Changed
- **Output format: Emoji-coded Compact Snapshot** - Replaced SYSTEM DIAGNOSTIC REPORT with visual hierarchy using 🔴🧠🧪📂 emoji headers
  - 🔴 What's Actually Broken (Critical failures + High-risk behavior)
  - 🧠 Blind Spots & Contradictions (Meta-analysis findings)
  - 🧪 Testing & Watchlist (Operational checklist with cadence)
  - 📂 Evidence Artifacts (Deep dive references)
  - Recommended Next Steps section at bottom (preserved from previous format)
- Headers now render as plain text instead of raw markdown syntax
- Recommended Next Steps now use domain-based action format (1, 1a, 1b, 0) matching /gto
- Added two-mode output system: Compact Snapshot (default) and Verbose (--verbose flag)
- **CRITICAL**: Every TOP PRIORITY (RISK ≥ 6) MUST have a corresponding recommended next step
  - Added structural requirement preventing orphan priorities (risks without actions)
  - Added validation check: actions count must ≥ priorities count
  - Updated Success Criteria to include "Action Mapping Validated"
- **Step 7: Adversarial Validation** now uses Agent tool directly (not Python wrapper)
  - Removed `adversarial_validation.py` Python module
  - Documented Agent tool dispatch pattern for parallel adversarial review
  - Updated integration examples to show Agent(subagent_type=...) calls

### Fixed
- Removed raw markdown rendering (no more `**bold**` or `- item` syntax in output)
- Important information now shows in compact format instead of verbose details
- Fixed structural gap where recommended next steps could drift from top priorities
  - Added CRITICAL rule in output format enforcing priority→action mapping
  - Enhanced Step 5 (Prevent) with explicit mapping requirement and validation check
  - Generic "testing" or "documentation" actions no longer satisfy requirements
- Fixed over-engineering: Adversarial validation no longer requires Python wrapper module
  - Agent tool provides direct subagent dispatch without intermediate code layer
