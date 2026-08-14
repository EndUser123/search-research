---
title: "For claude code, I'd like to capture things to remember into CKS automatically.  Something like:

❯ hrm.  Can we make t"
date: "2026-01-28"
mode: "COPILOT"
uuid: "b65855da-a5bd-4f18-ad4c-0552b2e29c5b"
entry_count: 2
---

## Human

For claude code, I'd like to capture things to remember into CKS automatically.  Something like:

❯ hrm.  Can we make that automatic in a hook?  That the system captures good info
  automatically?

● Feasible. Two approaches:

  Option A: Stop Hook Auto-Extraction

  Analyze conversation at /compact, extract decisions, store to CKS.

  Pros: Single LLM call per session, captures all decisions at once
  Cons: Decisions not available for handover in same session (only next sessions)

  Option B: PostToolUse Decision Capture

  After significant tools (Read, Edit, Write), analyze if a decision was made.

  Pros: Decisions available immediately for same-session handover
  Cons: More LLM calls, risk of over-capturing noise

  Recommendation: Stop Hook

  Add to SessionStart_checkpoint_restore.py or create Stop_auto_decision_capture.py:

  def extract_decisions_from_transcript(transcript_path: str) -> list[dict]:
      """Analyze transcript for decision patterns."""
      # Read transcript, look for:
      # - "Recommend: X" + "because Y"
      # - "Choose X over Y"
      # - Bridge tokens already mentioned

      # For each decision found, store to CKS:
      # cks.add_entity(DecisionEntity(task_name, what, answer, reasoning))


---

Are there repos that do this already we can copy from?

## Assistant

Perfect! Here's your comprehensive research summary:

## 🎯 TL;DR: Yes, Repos Exist & Better Approach Exists

### **Best Reference: Convictional's Research (Production-Validated)**

You're on the right track with the Stop Hook approach, but **don't use single-shot extraction**. The Convictional team published a case study on exactly this problem ("From Transcripts to Decisions") with production results showing:

- ❌ **Single-shot extraction:** Generic options, sparse coverage (1-2 decisions per hour), overlapping criteria
- ✅ **Multi-step pipeline:** 3-5x more decisions, specific alternatives, clean deduplication

**Their breakthrough discovery:** Adding **line numbers to transcript** had MORE IMPACT than all prompt engineering combined.

***

### **The Working Pipeline (Copy This)**

**Convictional's proven approach:**

1. **High-level extraction** → Find decision points with source line numbers
2. **Enrichment** → For each decision, independently extract options/criteria/insights  
3. **Deduplication** → Merge "user experience" vs "ease of use"
4. **Selection determination** → Which option was chosen?
5. **Object construction** → Final decision entity

**Counterintuitive finding:** Process 5500-token chunks instead of full transcript
- Better decision coverage (3-5x more extracted)
- Better option quality (specific, not generic)
- Better source attribution accuracy
- Reasoning: attention dilution on giant contexts; smaller chunks = deeper analysis

***

### **Existing Codebases to Copy From**

1. **claude-code-hooks-mastery** (disler) — Hook lifecycle & patterns
2. **ccheckpoints** — UserPromptSubmit → Stop pipeline for session tracking
3. **claude-conversation-extractor** — JSONL transcript parsing
4. **decisionrecords.org + MCP** — External decision repo pattern

***

### **What You Need**

**Stop Hook Script:**
```python
# 1. Read transcript (with line numbers)
# 2. Chunk into 5500-token groups  
# 3. Multi-step extraction per chunk (not single-shot)
# 4. Dedup across chunks
# 5. Store to CKS
```

I've saved a complete research document with:
- Detailed Convictional findings
- All 4 repo patterns explained
- Pydantic data models (Decision, Option, Criterion, Insight)
- Hook configuration + skeleton script
- How this integrates with your CLAUDE.md system

Check `decision_capture_research.md` for the full breakdown, code samples, and implementation roadmap.

## Human

[DOWNLOAD]: Use create_text_file tool only. Create ONE comprehensive .md file.

MUST INCLUDE:

SOLUTION DESIGN:
- Current state vs target state
- What's changing & why
- Architecture & benefits
- Key metrics/improvements

IMPLEMENTATION (All code inline):
- [List each file]
- Step-by-step setup
- Configuration reference
- Testing patterns
- Troubleshooting

STEADY-STATE OPERATION:
- Day-to-day usage workflows
- On-demand health checks
- Common operational tasks

CRITICAL: Everything copy-paste ready. No external references.

Provide artifact ID for immediate download.
Section Guide & Best Practices
SOLUTION DESIGN
What to include:

Current state vs target state

Architecture overview

What's changing & why

Key benefits & metrics

Integration points

Format:

text
### Current State
[Describe existing setup, pain points, limitations]

### Target State
[Describe desired outcome, capabilities, improvements]

### Architecture Overview
[ASCII diagram or detailed text description]

### Key Changes
1. [Change 1] - Why: [reasoning]
2. [Change 2] - Why: [reasoning]

### Benefits & Metrics
- Performance: X% improvement
- Reliability: [specific metric]
- Cost savings: [if applicable]

### Trade-offs & Constraints
- [Trade-off 1]: [Why acceptable]
IMPLEMENTATION
What to include:

Complete file list with paths

Step-by-step setup instructions

Configuration reference (structured)

All code inline, fully functional

Testing patterns

Troubleshooting common issues

Format:

text
### Files Required
project/
├── src/
│ ├── main.py
│ ├── config.py
│ └── utils.py
├── .env.example
├── requirements.txt
└── README.md

text

### Configuration Reference
| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `API_KEY` | string | (required) | Authentication |
| `DB_URL` | string | `localhost` | Database connection |
| `LOG_LEVEL` | enum | `INFO` | Logging verbosity |

### Step-by-Step Setup
1. [First step with full command]
2. [Second step with full command]
...

### Testing Patterns
- [Test 1]: How to validate [feature]
- [Test 2]: How to validate [feature]

### Troubleshooting
#### Issue: [Common problem]
**Symptom:** [What you'll see]
**Solution:** [Steps to fix]
STEADY-STATE OPERATION
What to include:

Day-to-day usage workflows

On-demand health checks

Common operational tasks

Format:

text
### Daily Workflows
- [Task 1]: Do this regularly
  ```powershell
  [Command to accomplish task]
[Task 2]: Do this when [condition]

Health Checks (On-Demand)
Run when you need to verify status:

powershell
# Check service status
[Health check command]

# Expected response: [what success looks like]
text

---

## Implementation Tips for Your Workflow

### For Windows PowerShell 7.5+ Compatibility
- Use `Get-Content` instead of `cat`
- Use `Copy-Item` instead of `cp`
- Prefer native PowerShell cmdlets over Linux aliases
- Include both `.ps1` scripts and `.bat` wrappers if needed

### For Solo Developer Scale
- **Backup before each change** (automated in procedures)
- **Reversibility is critical** (every major change needs rollback path)
- **Debug mode must be easy to enable**
- **Health checks automated** (scheduled tasks)

### For Multi-Terminal Workflows
- Provide commands that work in multiple terminals simultaneously
- Make logging easy to tail in separate windows
- Structure output for easy parsing (JSON where possible)

---

## Quick Reference: Section Checklist

Before submitting the prompt, verify you have:

- [ ] **SOLUTION DESIGN** - Current → target clear? Architecture documented?
- [ ] **IMPLEMENTATION** - Every file complete? All commands copy-paste ready?
- [ ] **STEADY-STATE** - Day-to-day workflows documented? Health checks defined?
- [ ] **Testing** - How to validate each feature?
- [ ] **Troubleshooting** - Common issues covered?
- [ ] **All code inline** - No external references?
- [ ] **Windows compatible** - PowerShell 7.5+ friendly?

CRITICAL: Everything copy-paste ready. No external references.

Provide artifact ID for immediate download.

## Assistant

Perfect! ✅ **File created successfully**

## **Artifact ID: 45**
### **Filename:** `claude_decision_capture.md`

***

## What You Get (Complete, Copy-Paste Ready)

This comprehensive guide includes **everything**:

### **SOLUTION DESIGN**
- ✅ Current state vs target (transcript → lost context → structured decisions)
- ✅ Architecture diagram (5-step pipeline)
- ✅ Key changes & why (Stop hook, multi-step extraction, chunking, LineNums)
- ✅ Metrics (3-5x more decisions, zero per-session overhead)
- ✅ Trade-offs (acceptable latency, API costs)

### **IMPLEMENTATION** (All code inline, production-ready)
- ✅ **7 complete Python files** (data models, extractor pipeline, hooks)
- ✅ **Full config file** with all tunable parameters
- ✅ **Step-by-step setup** (directories → dependencies → config → registration)
- ✅ **4 testing patterns** (transcript reader, chunking, end-to-end, storage)
- ✅ **5 troubleshooting scenarios** with exact fixes
- ✅ All commands **Windows PowerShell 7.5+ compatible**

### **STEADY-STATE OPERATION**
- ✅ **4 daily workflows** (review decisions, search by topic, export ADRs, weekly health)
- ✅ **5 health checks** (hook registration, dependencies, storage integrity, hook execution, API connectivity)
- ✅ **4 operational tasks** (manual trigger, cleanup old decisions, restore DECISIONS.md, analyze patterns)
- ✅ **All code copy-paste ready** — no external references

### **Quick Reference**
- Configuration reference table
- Quick start checklist (12 steps)
- Version/compatibility info

***

## Download & Use

**Click the download button** in the artifact viewer to get `claude_decision_capture.md`.

**Then:**
```powershell
# 1. Follow "Step-by-Step Setup" section exactly
# 2. Copy each Python file to ~/.claude/hooks/
# 3. Run "Test 1: Verify Transcript Reading" to validate
# 4. Register hooks in .claude_code_config.json
# 5. Next Claude Code session will auto-extract decisions
```

**Check it works:**
```powershell
Get-Content ~/.claude/storage/decisions.jsonl -Head 3 | ConvertFrom-Json
# Should show extracted decisions with title, options, criteria, selected_option
```

***

## Key Features

| Feature | Benefit |
|---------|---------|
| **Multi-step pipeline** | 3-5x more decisions extracted (proven by Convictional research) |
| **5500-token chunking** | Better coverage than single-shot; avoids attention dilution |
| **Line-numbered transcripts** | Source attribution — can jump to exact line in transcript |
| **Automatic deduplication** | No duplicate "use Redis" decisions across chunks |
| **SessionStart integration** | Recent decisions auto-loaded in next session (DECISIONS.md) |
| **Zero manual overhead** | Stop hook handles everything; you just use Claude Code normally |
| **Fully offline setup** | All code runs locally; only API calls are to Claude for extraction |

***

**Ready to go!** Download the file and follow the Quick Start Checklist. 🚀
