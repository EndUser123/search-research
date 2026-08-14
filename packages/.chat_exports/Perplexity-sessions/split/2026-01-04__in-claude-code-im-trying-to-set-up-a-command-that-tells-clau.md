---
title: "In claude code, I'm trying to set up a command that tells Claude to document what we have been working on.  But I guess "
date: "2026-01-04"
mode: "COPILOT"
uuid: "8f22ff6f-9f92-4650-9661-f340c9eb3f89"
entry_count: 3
---

## Human

In claude code, I'm trying to set up a command that tells Claude to document what we have been working on.  But I guess I'm not doing ti right, because when I give the command, it tells me it is documentation and does nothing.  What is a best practice documentation command that can replace what I'm doing?

---
id: doc
aliases: ["/doc", "/docs"]
category: unified-document-system
handles:
  - "documentation"
  - "docs"
  - "doc quality"
  - "document lifecycle management"
  - "intelligent document processing"
  - "unified document operations"
  - "lazy documentation updates"
  - "what docs need updating"
orchestrator:
  mode: unified-agent-orchestration
  plan_capable: true
  execute_capable: true
  sub_agents:
    - "documentation-generator"
    - "document-validator"
    - "lifecycle-manager"
    - "doc-suggest"
  docs: "P://__csf.nip/src/modules/document_system/doc_unified.md"
---


# DOC - Unified Document System with Sub-Agent Architecture


**CSF NIP Constitution v4.0 Compliant | Single Entry Point | Specialized Sub-Agent Orchestration**


The unified `/doc` command provides intelligent document processing through specialized sub-agents, delivering the power of three focused systems through one cohesive interface.


## Intelligent Path Integration


DOC integrates with the Path Intelligence system to automatically organize generated documentation and processed files:


```python
# Get intelligent path for document outputs
import subprocess
import json


def get_doc_output_path(filename, content="Generated documentation"):
    """Get optimal path for document output using Path Intelligence"""
    cmd = [
        "python", "__csf.nip/commands/path_command.py",
        "--json", "suggest", filename,
        "--content", content,
        "--category", "documentation"
    ]


    result = subprocess.run(cmd, capture_output=True, text=True, cwd="C:/_Python/Projects")
    suggestion = json.loads(result.stdout)


    return suggestion['suggested_path']


# Example usage for generated documentation
doc_path = get_doc_output_path(
    "api_documentation.md",
    "Comprehensive API reference guide with examples"
)
```


**Direct CLI Integration**:
```bash
# Get path for document files
path --json suggest "user_guide.md" --content "User documentation with examples" --category documentation


# Show available routing options
path rules


# Get integration examples
path markdown-examples
```


---


**description**: Intelligent document system that automatically selects and orchestrates specialized sub-agents for documentation generation, validation, and lifecycle management


## Quick Start


```bash
# LAZY MODE - No arguments, figures out what you did
/doc
# Analyzes git status + chat history + suggests doc updates


# Auto-detect and process document (intelligent mode)
/doc "README.md"


# Specify sub-agent explicitly
/doc "api_spec.md" --agent generator
/doc "user_guide.md" --agent validator
/doc "temp_files/" --agent lifecycle


# Multi-agent workflows
/doc "docs/" --workflow validate,enhance,classify
/doc --scan-repository --auto-fix
```


**Core Variables:**
- `$1` - Target (file path, directory, or "scan-repository") - **OPTIONAL, lazy mode if omitted**
- `--agent` - Force specific sub-agent: `generator`, `validator`, `lifecycle`, `auto`
- `--workflow` - Multi-agent sequence: `validate,enhance,classify,archive`
- `--mode` - Processing mode: `lazy` (default), `intelligent`, `batch`, `interactive`


---


## Lazy Mode (Default - No Arguments)


**Just type `/doc` and it figures out what needs updating.**


```bash
/doc
```


### What Lazy Mode Does


1. **Checks your working tree** (git status - uncommitted changes only)
2. **Analyzes recent chat history** (what you discussed in THIS session)
3. **Cross-references documentation** (which docs mention your changed files)
4. **Shows actionable suggestions**


### Example Output


```
📋 Documentation Update Suggestions


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Files changed in your working tree:
  ✓ src/yt_fts/download/batch_downloader.py
  ✓ src/yt_fts/core/cli.py


Documentation affected:
  → ARCHITECTURE.md mentions "batch_downloader" (line 45)
  → DEVELOPING.md mentions "cli.py" (line 16)
  → CLAUDE.md mentions "Downloads:" section


Session context detected:
  • Added dual-sink logging integration
  • New FR-13 requirement in PRD
  • Updated stats format for channel display


Suggested updates:
  1. ARCHITECTURE.md → Add dual-sink logging section
  2. DEVELOPING.md → Update logging configuration
  3. CHANGELOG.md → Add v1.9.5 entry


Run: /doc --apply    (auto-generates the updates)
Run: /doc --verbose  (show detailed analysis)
```


### How It Filters Your Work (Not Other Devs')


In a 6-developer workspace, lazy mode only sees **YOUR changes**:


| Source | What It Captures | What It Ignores |
|--------|------------------|-----------------|
| Git status | Your uncommitted files | Other devs' commits |
| Chat history | THIS session only | Other conversations |
| File mtimes | Files YOU touched | Files changed by others |


### Lazy Mode Options


```bash
/doc                    # Show suggestions (default)
/doc --apply            # Auto-generate documentation updates
/doc --verbose          # Show detailed analysis with evidence
/doc --dry-run          # Show what would be updated
/doc --scope {dir}       # Limit analysis to specific directory
```


---


## Sub-Agent Architecture


### 1. Documentation Generator Agent
**Handles**: Content creation, API documentation, user guides
**Capabilities**:
- Auto-discovery of documentation needs
- API code implementation generation from code
- User guide creation from existing content
- Enhancement and improvement of existing docs
**Specialists Used**: `csf-nip-documentation-specialist`, `code-analyzer`


### 2. Document Validator Agent
**Handles**: Quality assurance, consistency, validation
**Capabilities**:
- Multi-agent coordination (4 specialist agents)
- Technical accuracy validation
- Consistency and reference integrity checking
- Constitutional compliance verification
**Specialists Used**: `csf-nip-technical-accuracy`, `csf-nip-consistency-validator`, `csf-nip-reference-integrity`, `csf-nip-structure-flow`


### 3. Lifecycle Manager Agent
**Handles**: Document organization, cleanup, archival
**Capabilities**:
- Intelligent document classification (TEMPORARY vs ARCHIVAL)
- Automated cleanup with preservation of valuable content
- Knowledge system integration and ingestion
- Archive organization and management
**Specialists Used**: `document-classifier`, `knowledge-orchestrator`


## Intelligent Processing Pipeline


### Step 1: Context Analysis
```python
def analyze_document_context(target):
    # Document type detection
    doc_type = detect_document_type(target)


    # Agent requirement analysis
    required_agents = determine_specialist_needs(doc_type)


    # Processing strategy selection
    workflow = select_optimal_workflow(doc_type, required_agents)


    return {
        'document_type': doc_type,
        'agents': required_agents,
        'workflow': workflow,
        'confidence': calculate_confidence()
    }
```


### Step 2: Agent Orchestration
```python
def orchestrate_agents(context):
    results = []


    for agent in context['agents']:
        # Initialize specialized agent
        specialist = get_specialist_agent(agent)


        # Execute with quality gates
        result = specialist.execute(
            target=context['target'],
            quality_gates=get_quality_gates(agent),
            constitutional_compliance=True
        )


        results.append(result)


        # Cross-agent validation
        if needs_validation(agent, results):
            validate_cross_agent_consistency(results)


    return synthesize_results(results)
```


### Step 3: Intelligent Synthesis
```python
def synthesize_results(agent_results):
    # Resolve conflicts between agents
    resolved = resolve_agent_conflicts(agent_results)


    # Apply constitutional filters
    constitutional = apply_constitutional_compliance(resolved)


    # Generate unified output
    return create_unified_document_state(constitutational)
```


## Processing Modes


### Auto-Intelligent Mode (Default)
```bash
/doc "README.md"
```
- Automatically determines document type and needs
- Selects optimal sub-agent combination
- Provides comprehensive processing without user code implementation


### Specialist Mode
```bash
/doc "api_spec.md" --agent validator
```
- Forces specific sub-agent execution
- Useful for targeted operations
- Maintains specialist expertise


### Workflow Mode
```bash
/doc "docs/" --workflow validate,enhance,classify
```
- Executes sequence of sub-agents
- Each agent builds on previous results
- Optimizes for complex document operations


### Repository Scan Mode
```bash
/doc --scan-repository --auto-fix
```
- Scans entire repository for document issues
- Applies appropriate agents to each document
- Generates comprehensive repository health report


## Quality Gates & Constitutional Compliance


### Unified Quality Framework
- **Evidence-Based Processing**: All operations require evidence and validation
- **Specialist Routing**: Mandatory routing through CSF NIP specialists
- **Constitutional Compliance**: 95% minimum compliance score required
- **Audit Trail**: Complete operation tracking and logging


### Cross-Agent Validation
- Agents validate each other's results
- Conflict resolution through constitutional principles
- Consistency checks across specialist domains
- Quality gate enforcement at each processing stage


## Performance & Productivity


### Force Multiplier Effects
- **Generator Agent**: 3-5x documentation creation speed
- **Validator Agent**: 8-12x quality improvement through multi-agent coordination
- **Lifecycle Agent**: 10-15x document organization efficiency
- **Combined Workflow**: 15-25x overall productivity improvement


### Optimization Features
- Parallel agent execution where possible
- Caching of classification results
- Intelligent batching of similar operations
- Learning system integration for continuous improvement


## Integration with CSF NIP Ecosystem


### Existing System Integration
- **Document Coordinate**: Integrated as Validator Agent sub-specialists
- **Cleanup System**: Enhanced and integrated as Lifecycle Manager
- **Documentation System**: Preserved as Generator Agent capabilities
- **Knowledge Orchestrator**: Used for intelligent ingestion and archival


### Specialized Agent Access
All individual specialist agents remain accessible:
```bash
# Direct specialist access for advanced users
/document-coordinate "spec.md" all
/cleanup --intelligent-classification
```


## Constitutional Requirements


### Solo Developer Effectiveness
- **Unified Interface**: Single command reduces cognitive load
- **Specialized Power**: Sub-agents maintain domain-specific effectiveness
- **Zero Background Resources**: No persistent processes or services
- **Immediate Response**: Sub-500ms response time for all operations


### Plugin Architecture Compliance
- **Modular Sub-Agents**: Each agent is independently maintainable
- **Configurable Workflows**: Easy to customize agent sequences
- **Extensible Architecture**: Simple addition of new specialist types
- **No External Dependencies**: Fully self-contained within CSF NIP ecosystem


---


**Usage**: Use for all document operations. The intelligent sub-agent architecture automatically selects optimal processing strategies while maintaining specialist effectiveness and constitutional compliance.

## Assistant

I see the issue. Your current command is being recognized as documentation *about* documentation rather than as an *action* that generates documentation. The problem is in how Claude Code interprets the command—it's hitting the "documentation" category/handle and treating it as informational rather than as an actionable command.

Here's the best practice fix:

## The Problem

Your command structure has this in `handles`:
```yaml
handles:
  - "documentation"
  - "docs"
  - "doc quality"
```

When you type `/doc`, Claude Code matches "documentation" and treats it as a lookup request rather than executing the command logic.

## Best Practice Solution

Restructure your command to be **action-oriented** rather than documentation-oriented:

```yaml
id: record
aliases: ["/record", "/snapshot", "/session-summary"]
category: session-management
handles:
  - "record what we did"
  - "document session"
  - "update docs from session"
  - "capture progress"
  - "session snapshot"
orchestrator:
  mode: unified-agent-orchestration
  plan_capable: true
  execute_capable: true
  sub_agents:
    - "documentation-generator"
    - "document-validator"
    - "lifecycle-manager"
  docs: "P://__csf.nip/src/modules/document_system/doc_unified.md"
---

# RECORD - Session Documentation Snapshot

**Captures and documents current session work automatically**

## Quick Start

```bash
# Generate documentation from this session's work
/record

# Record with specific target
/record "docs/ARCHITECTURE.md"

# Detailed recording with validation
/record --verbose --validate
```

## What It Does

1. **Analyzes git status** - Uncommitted changes in YOUR working tree
2. **Reviews session history** - What YOU discussed in THIS conversation
3. **Updates relevant docs** - Modifies documentation that touches changed files
4. **Validates changes** - Ensures consistency and accuracy
5. **Reports results** - Shows what was updated

## Options

```bash
/record                    # Show what would be recorded
/record --apply            # Execute the recording
/record --verbose          # Detailed analysis
/record --scope {dir}      # Limit to specific directory
```
```

## Why This Works Better

| Aspect | Your Current | Fixed Version |
|--------|--------------|---------------|
| **Intent clarity** | "doc" = reference lookup | "record" = action to take |
| **Handles** | "documentation" (passive) | "record what we did" (active verb) |
| **User mental model** | "Show me docs" | "Document this session" |
| **Claude Code match** | Treats as info request | Treats as command execution |
| **Triggering** | Ambiguous | Unambiguous action |

## Alternative Names (Pick One)

```yaml
# Action-focused options:
id: snapshot     # /snapshot
id: commit-docs  # /commit-docs
id: update-docs  # /update-docs
id: capture      # /capture
id: summarize    # /summarize
```

I'd recommend `/record` or `/snapshot` because:
- Clear action verb
- Session-focused (captures "what we did")
- Less likely to be confused with general documentation
- Matches your workflow intent (recording progress)

The key principle: **Use action verbs in handles and aliases** so Claude Code executes the command rather than treating it as a documentation lookup. Your current setup is technically correct for a reference system, but you're trying to use it as an execution system.

Would you like me to help refactor this further or set up additional commands that work in tandem (like `/analyze` for reviewing before `/record` commits)?

## Human

Oddly I have an /analyze command for reviews before commits!

## Assistant

That is excellent—you are already halfway to a perfect "Definition of Done" workflow!

If you already have `/analyze` (Pre-commit/Review) and now you implement `/record` (Post-commit/Documentation), you create a powerful "Bookend" workflow:

1.  **Start/Mid Work:** `/analyze` (Checks code quality, logic, bugs)
2.  **Finish Work:** `/record` (Updates docs, changelogs, and summaries)

Here is the **full, corrected command file** that replaces your broken `/doc`. I have renamed it to `/record` and tweaked the handles to ensure Claude executes it as an action rather than treating it as a help page.

### Recommended Command File: `record.md`

You can drop this directly into your commands directory.

```markdown
---
id: record
aliases: ["/record", "/chronicle", "/log-work"]
category: session-management
handles:
  - "record session"
  - "log changes"
  - "document what we did"
  - "update documentation"
  - "generate session summary"
  - "finalize documentation"
  - "write release notes"
orchestrator:
  mode: unified-agent-orchestration
  plan_capable: true
  execute_capable: true
  sub_agents:
    - "documentation-generator"
    - "document-validator"
    - "lifecycle-manager"
    - "doc-suggest"
  docs: "P://__csf.nip/src/modules/document_system/record_unified.md"
---

# RECORD - Session Documentation & Archival

**CSF NIP Constitution v4.0 Compliant | Action-Oriented | Intelligent Archival**

The `/record` command is the "Closing Action" of a work session. It looks at what was just accomplished and automatically updates the relevant documentation, changelogs, and project context files.

## Intelligent Path Integration

RECORD integrates with Path Intelligence to place session logs and updates correctly:

```python
# Intelligent path routing for session records
import subprocess
import json

def get_record_path(filename, content="Session Record"):
    """Get optimal path for session documentation"""
    cmd = [
        "python", "__csf.nip/commands/path_command.py",
        "--json", "suggest", filename,
        "--content", content,
        "--category", "session-log"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="C:/_Python/Projects")
    return json.loads(result.stdout)['suggested_path']
```

## Quick Start

```bash
# LAZY MODE (Best Practice)
/record
# 1. Scans your recent git changes
# 2. Reads the last ~50 messages of conversation
# 3. Updates CHANGELOG.md and affected docs automatically

# Explicit Target
/record "README.md" --context "Added new login feature"

# Dry Run (See what it WOULD write)
/record --dry-run
```

**Core Variables:**
- `$1` - Target (file/dir) - **OPTIONAL (Defaults to "Session Context")**
- `--mode` - `auto` (default), `changelog-only`, `full-audit`
- `--commit` - Optional: Generate a git commit message alongside the docs

## How It Differs From /Analyze

| Command | Timing | Focus |
| :--- | :--- | :--- |
| **`/analyze`** | **During** Development | Code Quality, Bugs, Logic, Security |
| **`/record`** | **After** Development | Documentation, Context, History, Readability |

## Lazy Mode Logic (The "Magic")

When you run `/record` with no arguments, it executes this logic:

1.  **Git Diff Check**: `git diff --name-only HEAD` (What files did you touch?)
2.  **Context Extraction**: Summarizes the last turn of conversation to understand *why* changes were made.
3.  **Impact Analysis**: Identifies which documentation files references the changed code.
    *   *Example: You changed `auth.py`. `/record` checks `API.md` and `SECURITY.md`.*
4.  **Drafting**: Proposes updates to those specific document sections.

## Sub-Agent Architecture

### 1. The Scribe (Generator)
**Role**: Writes the actual content.
**Behavior**: meaningful prose over bullet points. Connects code changes to business value.

### 2. The Librarian (Lifecycle)
**Role**: Figures out where things go.
**Behavior**: Decides if this is a "Temporary Note" or "Permanent Architecture Update".

### 3. The Auditor (Validator)
**Role**: Ensures the docs match the code.
**Behavior**: Fails the command if you documented a function that doesn't exist.

## Example Workflow

```bash
# 1. You finish coding a feature
# 2. You run your existing command:
/analyze --safety

# 3. Everything looks good. You commit.
git commit -m "feat: added login"

# 4. You run the closer:
/record
# Output: 
# "Updated CHANGELOG.md with new feature."
# "Updated API.md with new /login endpoint details."
# "Session summary saved to /docs/work-logs/2026-01-04.md"
```
```

### Why this fixes your problem:
1.  **New ID**: `record` avoids the internal keyword collision with `doc`.
2.  **Action Handles**: "log changes" and "record session" tell Claude "DO SOMETHING", whereas "documentation" often tells Claude "EXPLAIN SOMETHING".
3.  **Clearer Separation**: It separates the *reference* material (docs) from the *activity* (recording).

## Human

Your version is much shorter.  Is that intentional?

## Assistant

Yes, it was intentional, but for a specific technical reason regarding how LLMs process system prompts.

The original file contained a high **Signal-to-Noise Ratio** issue. It had a lot of "marketing language" (e.g., *"Force Multiplier Effects," "15-25x overall productivity improvement"*).

While that text looks professional to a human reader, to Claude Code, it is **distracting noise**. It consumes token budget without providing executable instructions. When a prompt is too "wordy" with non-instructional text, the model sometimes dilutes the actual commands or gets confused about the priority of tasks.

### The "Perfect Balance" Strategy

You should **keep** the robust logic (the Python snippets, the sub-agent definitions, the workflow steps) but **cut** the descriptive "sales pitch" text.

Here is the **Hybrid Version**. It keeps your sophisticated CSF NIP architecture but applies the "Action-Oriented" fix and strips the fluff so Claude executes it instantly.

***

### `record.md` (Optimized for Performance)

```markdown
---
id: record
aliases: ["/record", "/snapshot", "/log-work"]
category: session-management
handles:
  - "record session"
  - "log changes"
  - "document what we did"
  - "update documentation"
  - "generate session summary"
  - "finalize documentation"
orchestrator:
  mode: unified-agent-orchestration
  plan_capable: true
  execute_capable: true
  sub_agents:
    - "documentation-generator"
    - "document-validator"
    - "lifecycle-manager"
  docs: "P://__csf.nip/src/modules/document_system/doc_unified.md"
---

# RECORD - Unified Document System

**CSF NIP Constitution v4.0 Compliant | Sub-Agent Orchestration**

The `/record` command is the actionable trigger for the Unified Document System. It captures the current session work, updates documentation, and manages file lifecycles.

## Core Logic & Path Integration

```python
# Intelligent path routing for session records
import subprocess
import json

def get_record_path(filename, content="Session Record"):
    """Get optimal path for session documentation using Path Intelligence"""
    cmd = [
        "python", "__csf.nip/commands/path_command.py",
        "--json", "suggest", filename,
        "--content", content,
        "--category", "documentation"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="C:/_Python/Projects")
    return json.loads(result.stdout)['suggested_path']
```

## Usage

```bash
# LAZY MODE (Default) - Auto-detects git changes and session context
/record

# Explicit Target
/record "api_spec.md" --agent generator

# Multi-agent Workflow
/record "docs/" --workflow validate,enhance,classify
```

## Processing Logic

### 1. Lazy Mode Execution
1.  **Git Check**: Identifies uncommitted files in working tree.
2.  **Context**: Analyzes recent chat history for intent.
3.  **Cross-Ref**: Identifies existing docs that reference changed files.
4.  **Action**: Suggests or applies updates.

### 2. Sub-Agent Routing
*   **Generator**: Creates content, API specs, and user guides. (Ref: `csf-nip-documentation-specialist`)
*   **Validator**: Enforces consistency and constitutional compliance. (Ref: `csf-nip-technical-accuracy`)
*   **Lifecycle**: Manages archival and knowledge ingestion. (Ref: `document-classifier`)

### 3. Orchestration Pipeline
```python
def orchestrate_agents(context):
    results = []
    for agent in context['agents']:
        # Execute specialist with quality gates
        result = agent.execute(
            target=context['target'],
            quality_gates=get_quality_gates(agent),
            constitutional_compliance=True
        )
        results.append(result)
    return synthesize_results(results)
```

## Options
- `--agent` - Force specific agent: `generator`, `validator`, `lifecycle`
- `--workflow` - Sequence: `validate,enhance,classify`
- `--apply` - Auto-generate and save updates without confirmation
- `--verbose` - Show detailed analysis with evidence
```

### Key Changes Made:
1.  **Renamed ID/Handles**: From `doc` (noun) to `record` (verb) to fix the execution bug.
2.  **Removed "Fluff"**: Deleted sections like "Force Multiplier Effects" and "Why It Filters Your Work." Claude doesn't need to be convinced to use the tool; it just needs to know *how*.
3.  **Preserved Logic**: Kept the Python orchestration snippets and agent definitions because those define the *behavior* you want.

This version is lean enough to be parsed reliably but dense enough to retain your complex sub-agent architecture.
