# Shared Schemas and Documentation

This directory contains shared schemas, documentation, and specifications used across
multiple review and analysis skills in the Claude Code marketplace.

## Purpose

Provide common contracts, schemas, and formats that skills like `/improve`, `/red-team`,
`/gto`, and `/debrief` can reference and implement consistently.

## Structure

```
shared/
├── schemas/
│   └── promotion_opportunity.schema.json    # Shared schema for long-term opportunities
├── docs/
│   ├── wiki_cks_ingest_queue.md            # Wiki/CKS ingest queue specification
│   ├── external_llm_review_format.md       # External LLM second-opinion format
│   └── external_review_calibration.md      # Calibration plan for external reviewers
└── README.md                                # This file
```

## Components

### 1. Promotion Opportunity Schema

**File:** `schemas/promotion_opportunity.schema.json`

**Purpose:** Shared JSON schema for capturing long-term efficiency/effectiveness
opportunities identified during review workflows.

**Used by:** `/improve`, `/red-team`, `/gto`, `/debrief`

**Key fields:**
- `id`: Unique opportunity identifier (OPP-XXX format)
- `source_workflow`: Which workflow identified it
- `observation`: What was observed
- `evidence`: Concrete evidence (file:line, tool output, citation)
- `reusable_lesson`: Pattern others should apply
- `promotion_target`: Where to promote (skill, hook, prompt, config, test, docs, cks_or_wiki, task, backlog, reject)
- `uniqueness`: new, strengthens_existing, duplicate, rejected
- `confidence`: high, medium, low
- `proposed_action`: Concrete action to take
- `validation_signal`: How to verify it worked
- `falsification_condition`: What would prove it wrong

**Rules:**
- No weak or vague observations
- No raw web snippets
- No user-specific preferences without intent
- Every entry must have validation/falsification path

### 2. Wiki/CKS Ingest Queue Specification

**File:** `docs/wiki_cks_ingest_queue.md`

**Purpose:** Defines the queue artifact format for review workflows to propose notes
for long-term preservation in wiki (QMD) or CKS.

**Queue location:** `.claude/.artifacts/wiki_ingest/proposed_notes/{session_id}.jsonl`

**Key concepts:**
- Lock-free concurrent writes (one JSONL per session)
- Dedicated ingest workflow processes queue
- Duplicate detection before ingestion
- Quality gate applies before writes
- No automatic wiki/CKS writes from review workflows

**Promotion targets:**
- `skill`: Update or create a skill
- `hook`: Update or create a hook
- `prompt`: Update a prompt template
- `config`: Update configuration
- `test`: Add or improve tests
- `docs`: Update documentation
- `cks_or_wiki`: Knowledge preservation
- `task`: Create a task
- `backlog`: Defer indefinitely
- `reject`: Discard

### 3. External LLM Second-Opinion Format

**File:** `docs/external_llm_review_format.md`

**Purpose:** Defines a reusable packet format for soliciting structured second-opinion
reviews from external LLMs (GLM-5.2, MiniMax-M3, etc.).

**Key components:**

**Input packet:**
- `context`: Session summary, domain, relevant rules
- `artifacts_under_review`: Files, prompts, hooks being reviewed
- `primary_findings`: Current findings to review
- `unresolved_assumptions`: Assumptions needing validation
- `specific_questions`: Targeted questions for external reviewer
- `success_criteria`: What a valid outcome requires
- `required_output_shape`: Expected response format

**External LLM response:**
- `missed_risks`: Issues we didn't identify
- `overclaimed_findings`: Findings that overreach evidence
- `severity_disagreements`: Severity level disagreements
- `duplicate_grouping_suggestions`: Findings that should merge
- `evidence_gaps`: Missing concrete evidence

**Model routing:**
- **GLM-5.2:** High-trust second critic for consequential reviews
- **MiniMax-M3:** Cheaper breadth reviewer for fast scans

**Integration contract:**
- External LLM is evidence, not authority
- Orchestrator owns final verdict
- External feedback merged selectively
- Falls back to internal review on failure

### 4. External Review Calibration Plan

**File:** `docs/external_review_calibration.md`

**Purpose:** Defines how to measure and validate external LLM effectiveness as reviewers.

**Calibration corpus:**
- 5-10 prior review packets with known outcomes
- Annotated with: known issues, false positives, missed findings
- Varied domains and verdict types

**Scoring rubric:**
- Useful missed issue (+2 critical, +1 high, +0.5 med/low)
- False alarm (-2 critical, -1 high, -0.5 med/low)
- Overclaim (-1)
- Duplicate detection (+0.5)
- Severity accuracy (+1 exact, +0.5 within one level)
- Evidence gap identification (+1)

**Acceptance criteria:**

GLM-5.2 (high-trust critic):
- Average score ≥ +3 per review
- False positive rate ≤ 20%
- Critical recall ≥ 80%
- Overclaim rate ≤ 15%

MiniMax-M3 (breadth reviewer):
- Average score ≥ +1 per review
- False positive rate ≤ 30%
- Critical recall ≥ 60%
- Overclaim rate ≤ 25%

## Implementation Status

### Completed

✅ Shared promotion opportunity schema created
✅ Wiki/CKS ingest queue specification documented
✅ External LLM review format specified
✅ Calibration plan defined
✅ `/improve` SKILL.md updated with opportunities section (v0.4.0)
✅ `/red-team` command updated with opportunities section (v0.2.0)

### Next Steps (Optional Enhancements)

- ⏳ Add opportunities section to `/gto` output format
- ⏳ Add opportunities section to `/debrief` output format
- ⏳ Build calibration corpus from prior reviews
- ⏳ Implement calibration scripts
- ⏳ Run calibration and document results
- ⏳ Create dedicated `/wiki-ingest` workflow

## Usage by Skills

### /improve (improve-partner plugin)

**Version:** 0.4.0

**Integration:** Added "Long-Term Efficiency / Effectiveness Opportunities" section to
Required Output Sections. Uses promotion opportunity schema format.

**Behavior:** Advisory by default. May propose notes to queue but does not silently
write to wiki/CKS.

### /red-team (red-team plugin)

**Version:** 0.2.0

**Integration:** Added "Long-Term Efficiency / Effectiveness Opportunities" section to
Final output format. Uses promotion opportunity schema format.

**Behavior:** Captures lessons beyond immediate ship/no-ship decision. Does not
derail verdict. Advisory by default.

### /gto (cc-skills-analysis plugin)

**Status:** Existing findings schema already compatible. Can adopt promotion format
in future updates.

### /debrief (cc-skills-analysis plugin)

**Status:** Existing opportunity/task templates already compatible. Can adopt
promotion format in future updates.

## Verification

To verify the shared schema is valid:

```bash
# Validate JSON schema syntax
python -m json.tool packages/.claude-marketplace/shared/schemas/promotion_opportunity.schema.json

# Check that documentation files exist and are readable
ls packages/.claude-marketplace/shared/docs/
```

## See Also

- Improve partner skill: `packages/.claude-marketplace/plugins/improve-partner/skills/improve/SKILL.md`
- Red-team command: `packages/.claude-marketplace/plugins/red-team/commands/red-team.md`
- GTO skill: `packages/.claude-marketplace/plugins/cc-skills-analysis/skills/gto/`
- Debrief skill: `packages/.claude-marketplace/plugins/cc-skills-analysis/skills/debrief/`
