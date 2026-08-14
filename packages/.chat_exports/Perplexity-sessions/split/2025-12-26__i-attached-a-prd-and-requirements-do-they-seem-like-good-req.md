---
title: "I attached a prd and requirements.  Do they seem like good requirements?"
date: "2025-12-26"
mode: "COPILOT"
uuid: "7d2b3bac-9ad3-43d1-b2ea-a2dd58610f37"
entry_count: 2
---

## Human

I attached a prd and requirements.  Do they seem like good requirements?

## Assistant

## Analysis: Your Requirements Documents

Your PRD and requirements analysis are **solid foundational documents** with strong structure and clarity. However, they have **critical gaps and ambiguities** that will create friction during implementation. Here's my detailed assessment:

***

## Strengths

**Clear Problem Definition**
Your problem statement is well-articulated—fragmented tools with no unified entry point. The pain points are concrete and relatable to any developer who's juggled multiple quality tools.

**Pragmatic Phasing**
Option B (Minimal Integration) is a sensible approach to avoid scope creep. Breaking into Phase 1 (core integration) and Phase 2 (enhancements) shows strategic thinking about MVP delivery.

**Detailed Specification Document**
The `specify.md` goes deeper than the PRD with architecture diagrams and component breakdown, which is good scaffolding for developers.

**Risk Awareness**
You've identified real risks (CKS storage growth, performance on large files, semantic detector unavailability) with mitigation strategies.

***

## Critical Gaps

### 1. **Requirement Ambiguity: What is "Code Quality"?**

Your scope statement says detect "syntax, types, style, security, dead code, duplicates, logic bugs, performance, anti-patterns, and constitutional violations," but your actual requirements focus only on:
- Duplicate detection (FR-002)
- CKS pattern ingestion (FR-003)
- Python standards indexing (FR-004)

**Missing specifics:**
- What does `ruff`, `mypy`, and `bandit` *actually* validate? How are conflicts between tools resolved?
- Which detectors run by default in `/cq`? Which are opt-in?
- How do you prioritize issues when detectors disagree?

**Recommendation:** Add a "Detection Matrix" that explicitly maps each detector (ruff, mypy, bandit, pytest, hash, AST, semantic) to what it catches, severity levels, and whether it's blocking or advisory.

***

### 2. **Vague Acceptance Criteria for FR-001**

Your `/cq` CLI signature is incomplete:

```
/cq [directory] [options]
  --detectors <list>
  --exclude <patterns>
  --fix
  --learn
  --output <format>
  --severity <level>
```

**Missing details:**
- What happens if `--detectors` specifies a detector that doesn't exist?
- How does `--fix` work? Is it truly interactive (user confirms each fix), or does it apply fixes automatically and report?
- Does `/cq --learn` automatically ingest after fixes, or is it a separate command?
- What counts as a "severity level"? How are hash duplicates vs. ruff warnings prioritized?
- What is the **default behavior** when running `/cq` with no args? (Full scan of current dir? All detectors? Filter by severity?)

**Recommendation:** Provide 3-4 concrete usage examples:
```bash
# Example 1: Full scan
/cq . --severity medium

# Example 2: Duplicates only
/cq . --detectors hash,ast

# Example 3: Interactive fixing
/cq . --detectors ruff --fix

# Example 4: Learn from results
/cq . --learn
```

***

### 3. **FR-002 (Duplicate Detection) Lacks Implementation Context**

You specify three detectors but don't address:

- **Integration dependencies:** Hash and AST are stdlib, but how do you invoke them from `qual-gate.py`? Is there a new module (`duplicate_detector.py`) that wraps all three, or does each run independently?
- **Performance ambiguity:** Your NFR-1 says "Full `/cq` scan < 30 seconds." Does this include duplicate detection on a 10K-file project? Hash is fast, but AST on 10K Python files could be slow. What's the actual threshold?
- **Semantic detector fallback:** You mark it "optional with graceful fallback," but what does graceful mean? Silent skip? Warning in output? Log message?
- **Similarity thresholds:** AST threshold is 0.85—where did that number come from? Have you tested it? What's the semantic threshold?

**Recommendation:** Add a "Performance Baseline" section with actual test data:
```
Tested on real codebases:
- Project A (2K Python files): Hash detection = 3s, AST = 18s, Semantic = N/A
- Project B (500 Python files): Hash detection = 0.5s, AST = 2s, Semantic = 7s
```

***

### 4. **FR-003 (CKS Pattern Ingestion) Missing Critical Design Questions**

The `QualityPattern` dataclass is defined, but you haven't answered:

- **What is the actual CKS storage schema?** Is each pattern a separate document? How do you query duplicates of the same pattern across runs?
- **Deduplication strategy:** You mention deduping by `pattern_hash`, but how do you compute `pattern_hash`? Is it `hash(detector_type + file_path + line_number + description)`? That would create duplicates across runs.
- **False positive tracking:** How is `false_positive` set? Is there a mechanism for developers to manually mark something as a false positive, or is it just a boolean field?
- **Success rate math:** If a developer applies fix X once and it succeeds, does future detection of the same issue show "100% success rate"? What's the denominator?

**Recommendation:** Provide a concrete example of CKS ingestion for a single duplicate detection result:
```python
# Input: Hash detector finds file_a.py == file_b.py
# Expected CKS storage:
{
  "detector_type": "hash_duplicate",
  "severity": "high",  # Why high? Duplicates waste disk space but aren't functional bugs
  "pattern_hash": "sha256(hash_duplicate + file_a.py + file_b.py)",
  "description": "Exact duplicate file",
  "metadata": {
    "file_a": "src/module_a.py",
    "file_b": "src/module_b.py",
    "hash": "abc123...",
    "size_bytes": 4096
  }
}
```

***

### 5. **Severity Levels Undefined**

You reference "critical, high, medium, low" in multiple places, but never define what these mean in context of code quality:

- Is a hash duplicate "critical" or just "medium"? (It's technically a code smell, not a runtime bug.)
- Is a ruff style violation "low"? (Yes, typically.)
- Is a bandit security issue always "critical"? (No, depends on the specific issue.)

**Recommendation:** Add a severity mapping table:

| Issue Type | Severity | Rationale |
|-----------|----------|-----------|
| Hash duplicate | Medium | Code smell; suggests refactoring but not functional defect |
| AST duplicate | Medium | Similar justification |
| Ruff style (E501) | Low | Cosmetic; doesn't affect behavior |
| Ruff bug check (F) | High | Likely error; strong signal |
| Bandit SQL injection | Critical | Security vulnerability |
| Dead import | Low | Cleanup only |

***

### 6. **FR-004 and FR-005 Are Underspecified**

- **FR-004:** "Index Python 2025 standards into CKS." How do you link this to quality checks? If ruff catches a PEP 8 violation, does `/cq` output auto-reference the relevant standard? Or is this just a searchable knowledge base?
- **FR-005:** CWO12 integration is listed but seems orthogonal to core `/cq` functionality. Should this be Phase 2 or even Phase 3?

**Recommendation:** Move FR-005 to Phase 2. Focus Phase 1 on making `/cq` robust first.

***

## Structural Issues

### **Circular Dependency in Phase 1**

Your Phase 1 task dependency shows:
```
cq_001 (Add duplicates to qual-gate)
cq_002 (CKS pattern ingestion)
cq_003 (/cq wrapper) → depends on cq_001, cq_002
```

But your architecture shows duplicate detection runs *inside* `/cq`. So the dependency should actually be:
- `cq_001` and `cq_002` are parallel
- `cq_003` depends on both
- However, `cq_002` (CKS ingestion) could be optional in Phase 1—you could defer it to Phase 2 to reduce initial complexity

### **Testing Strategy Missing**

You have acceptance criteria but no test plan:
- Unit tests for each detector?
- Integration tests for `/cq --fix`?
- Performance tests to validate the 30-second threshold?
- False positive baseline tests?

***

## What's Missing for Implementation

1. **Configuration schema:** How does `/cq` know which detectors to run? YAML file? Environment variables? Hardcoded defaults?
2. **Error handling:** What happens if duplicate detection crashes on one file? Does `/cq` continue or fail?
3. **Output schema:** Your `--output json` is mentioned but not specified. What's the exact JSON structure?
4. **Backwards compatibility:** Does modifying `qual-gate.py` break existing workflows that depend on it?
5. **Developer experience:** Will developers need to create `.cq.yaml` config files? Learn new flags? Or is this a zero-config tool?

***

## Verdict

**Your documents are 65% ready for development.** They have strong strategic direction and clear problem framing, but they need:

1. **Concrete examples** (CLI usage, CKS output, severity mapping)
2. **Design clarifications** (what detectors run by default, exact similarity thresholds, how conflicts are resolved)
3. **Scope boundary** (explicitly list what's *not* covered in Phase 1)
4. **Risk quantification** (actual performance baselines, not just targets)

I'd recommend a **2-day design review** where you:
- Create a "Detective Matrix" documenting every detector and what it catches
- Write 5 end-to-end scenarios (e.g., "User runs `/cq` on untouched project, finds duplicates, applies fix")
- Mock up the JSON output format for `--output json`
- Define the CKS schema with concrete examples

Then you'll be ready to hand off to implementation with minimal ambiguity.

## Human

are there any github.com repos that help with prd and requirements?  PRP any useful?

## Assistant

Yes—there are several excellent GitHub repos for PRD and requirements, and **PRP is genuinely useful** if you're planning to use AI coding agents (like Claude Code). Here's the breakdown:

## Quick Answer: Best Repos by Use Case

### **For Traditional PRD + Requirements:**
- **[opulo-inc/prd-template]** - Clean, pragmatic PRD structure[1]
- **[rick4470/IEEE-SRS-Template]** - Formal specification standard (comprehensive but heavyweight)[2]
- **Product School's template** - Balanced approach with "Features Out" section (what you're explicitly NOT building)[3]

### **For AI-Assisted Code Generation (Highly Relevant to You):**
- **[Wirasm/PRPs-agentic-eng]** ⭐ **1.7K stars** - This is what you want if using Claude Code[4][5]
- **[B-AI-bot/PRP-Generator]** - Fork with same methodology[5]
- **[coleam00/context-engineering-intro]** - Context engineering approach[6]

***

## What is PRP? (You were right to ask)

**PRP = "Product Requirement Prompt"** — established summer 2024, it's **PRD evolved for AI coding agents**.[4][5]

**Key difference:**
- **Traditional PRD:** "What must the product do and why" (deliberately vague on implementation)
- **PRP:** PRD + **curated codebase intelligence** + **agent runbook** = minimum viable context for AI to ship production-ready code on first pass[5][4]

### PRP Structure (vs. Your Current PRD)

Your documents are missing three critical AI-focused layers:

| Layer | Your PRD | PRP Approach | Example |
|-------|---------|-------------|---------|
| **Goal** | ✅ You have this | ✅ Same | "Unified code quality system" |
| **Why** | ✅ You have this | ✅ Same | Business value, user impact |
| **What** | ✅ You have this | ✅ Same | FR-001 through FR-005 |
| **All Needed Context** | ❌ Missing | ✅ New | File paths, code examples, library docs, gotchas |
| **Implementation Blueprint** | ❌ Missing | ✅ New | Step-by-step tasks + pseudocode |
| **Validation Loop** | ❌ Missing | ✅ New | Executable tests (syntax, unit, integration) |

***

## Wirasm PRP Methodology (Highly Compatible with Your Project)

The Wirasm repo includes:[4][5]

**Pre-configured Claude Code commands:**
- `/create-base-prp` - Auto-generates comprehensive PRPs (you feed it a description, it researches & builds)
- `/execute-base-prp` - Executes the PRP against your codebase
- `/planning-create` - Generates architecture diagrams
- `/review-general`, `/refactor-simple`, `/create-pr` - Code operations

**Recommended directory structure:**
```
your-project/
├── .claude/commands/     # Slash commands for Claude Code
├── PRPs/
│   ├── templates/
│   ├── ai_docs/          # Library docs, architecture patterns
│   ├── completed/
│   └── my-feature.md     # Your actual PRP
├── CLAUDE.md             # Project guidelines
├── src/
└── tests/
```

**Example PRP (for your `/cq` feature):**
```markdown
## Goal
Implement unified code quality system with duplicate detection

## Why
- Fragmented tools (ruff, bandit, mypy) don't coordinate
- No duplicate detection integrated
- Quality results don't feed into learning systems

## What
`/cq` command that runs all checks + stores patterns in CKS

## All Needed Context
- qual-gate.py current implementation: [file path]
- CKS unified.py API: [file path + code snippet]
- Ruff documentation: https://docs.astral.sh/ruff/
- AST similarity algorithm: [pseudocode]

## CRITICAL Gotchas
- AST detector will timeout on files > 10KB
- CKS storage growth needs deduplication by pattern_hash
- Must handle conflicting detector results gracefully

## Implementation Blueprint
1. Task: Create hash_detector.py (SHA256 exact matches)
   - Input: List[Path]
   - Output: Dict[hash, List[Path]]
   - Tests: pytest tests/test_hash_detector.py

2. Task: Create ast_detector.py (structural similarity)
   - Algorithm: Compare AST nodes with 0.85 threshold
   - ...

## Validation Loop
- Level 1: `ruff check src/ --fix && mypy src/`
- Level 2: `pytest tests/ -v`
- Level 3: `/cq . --detectors hash,ast` (integration test)
```

Then you'd run: `/execute-base-prp PRPs/cq-unified.md` and Claude Code starts implementing with full context.

***

## My Honest Assessment

**For your code quality system:**

1. **If you're NOT using Claude Code:** Use opulo-inc/prd-template + Product School structure. Your current PRD is already 70% there; just add concrete CLI examples and a severity matrix.

2. **If you ARE using Claude Code (which seems likely given your profile):** Absolutely convert to PRP format using Wirasm methodology. This solves half your design gaps:
   - Adds "Implementation Blueprint" (eliminates ambiguity)
   - Forces you to document "All Needed Context" (qual-gate.py patterns, CKS schema, library versions)
   - Includes "Validation Loop" (executable tests AI can run)
   - Provides Claude Code commands that auto-wire the repo structure

**The shortcut:** Clone Wirasm/PRPs-agentic-eng, run `/create-base-prp "unified code quality system with duplicate detection and CKS pattern storage"`, and let Claude Code generate a production-ready PRP from your existing PRD + codebase analysis.
