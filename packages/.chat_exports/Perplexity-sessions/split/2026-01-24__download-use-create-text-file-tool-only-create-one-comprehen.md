---
title: "'[DOWNLOAD]: Use create_text_file tool only. Create ONE comprehensive .md file.

MUST INCLUDE:

SOLUTION DESIGN:
- "
date: "2026-01-24"
mode: "COPILOT"
uuid: "a74131bc-1596-4060-b89e-e75cb8a0f2a3"
entry_count: 5
---

## Human

"[DOWNLOAD]: Use create_text_file tool only. Create ONE comprehensive .md file.

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

CRITICAL: Everything copy-paste ready. No external references.

Provide artifact ID for immediate download.
"

Should that prompt be updated to instead steady state use and troubleshooting?  Is that already included?

## Assistant

Looking at your prompt structure, I can see it's **comprehensive but has room for optimization** based on typical usage patterns. Let me analyze what's there and what could be improved:

## Current Coverage Analysis

✅ **Already Included:**
- Solution design (current → target)
- Implementation details (files, setup, configuration)
- Testing patterns
- Troubleshooting

⚠️ **Implicit but Not Explicit:**
- Steady-state operation/maintenance
- Day-to-day usage patterns
- Monitoring/observability
- Common operational issues vs one-time setup issues

## Recommended Update

I'd suggest adding **explicit operational sections** since troubleshooting covers only *problems*, not *normal operation*:

```markdown
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

STEADY-STATE OPERATION:
- Day-to-day usage & workflows
- Monitoring & health checks
- Common operational tasks
- Performance expectations

TROUBLESHOOTING & MAINTENANCE:
- Common issues & solutions
- Debugging approach
- Log interpretation
- Recovery procedures

CRITICAL: Everything copy-paste ready. No external references.
Provide artifact ID for immediate download.
```

## Key Differences

| Section | Covers |
|---------|--------|
| **Testing** | Validation during setup |
| **Steady-State** | How you'll actually *use* it every day |
| **Troubleshooting** | When things break |

**Recommendation:** Yes, split into **two distinct sections**—operations is continuous, troubleshooting is reactive. This matches actual workflow better than lumping both under "troubleshooting."

Should I update your template prompt, or would you prefer a different structure?

## Human

Are we missing anything else?

## Assistant

Yes—reviewing against your typical workflow patterns, there are **several gaps**:

## Critical Missing Sections

### 1. **Dependencies & Prerequisites**
- Runtime requirements (Python 3.11+, Node 18+, etc.)
- System-level dependencies (FFmpeg, PostgreSQL, etc.)
- External API keys/services needed
- Compatibility constraints (Windows/Linux/Mac)
- Storage/compute requirements

**Why:** You can't execute setup without knowing what's required first.

### 2. **Architecture Diagram / System Overview**
- Visual representation of components
- Data flow
- Integration points
- Service dependencies

**Why:** Your multi-terminal, multi-agent workflows benefit from clear architecture visualization upfront.

### 3. **Quick Start (5-10 min path)**
- Minimal viable setup
- First successful run
- Validate basic functionality
- BEFORE deep configuration

**Why:** Separate from full implementation—lets you get working fast, then optimize.

### 4. **Configuration Reference (Structured)**
- All environment variables/config keys
- Default values
- Valid options/ranges
- Security implications

**Why:** Currently implicit in setup—needs explicit reference section.

### 5. **Performance Tuning & Optimization**
- Bottleneck identification
- Common optimizations
- Resource allocation
- Scaling considerations

**Why:** Your scale (26K+ torrents, 20K+ transcripts) makes this critical.

### 6. **Safety & Rollback**
- Backup strategy before changes
- Rollback procedures
- State recovery
- Data migration reversibility

**Why:** Critical for solo developer handling large-scale systems.

### 7. **Integration Points**
- APIs exposed
- Webhook support
- CLI interface
- Programmatic access

**Why:** Ties to your multi-agent orchestration patterns.

### 8. **Observability Setup**
- Logging configuration
- Metrics/monitoring
- Health check endpoints
- Debug mode activation

**Why:** Essential for debugging multi-terminal workflows.

## Revised Comprehensive Structure

```markdown
PREREQUISITES & REQUIREMENTS
- Runtime/system dependencies
- External services
- Storage/compute needs
- Compatibility matrix

SOLUTION DESIGN
- Current state vs target
- Architecture diagram
- What's changing & why
- Key metrics/benefits

QUICK START (5-10 min)
- Minimal setup path
- First successful validation
- Basic workflow example

IMPLEMENTATION (All code inline)
- [List each file]
- Full step-by-step setup
- Configuration reference (structured table)
- Integration points
- Performance tuning

STEADY-STATE OPERATION
- Day-to-day workflows
- Monitoring & health checks
- Common operational tasks

TROUBLESHOOTING & MAINTENANCE
- Common issues & solutions
- Debug activation & log reading
- Recovery procedures
- Rollback strategy

APPENDIX
- Environment variables reference
- CLI commands reference
- API endpoints reference
- Common extensions/customizations
```

## Priority Ranking (for your use case)

**MUST HAVE:**
1. Prerequisites (blocks execution)
2. Quick Start (validates immediately)
3. Configuration Reference (structured, not prose)
4. Troubleshooting (your solo-dev reality)

**SHOULD HAVE:**
5. Architecture/diagram (multi-agent context)
6. Observability setup (multi-terminal debugging)
7. Safety/rollback (large-scale data handling)

**NICE TO HAVE:**
8. Performance tuning
9. Integration points
10. Appendix references

***

**Bottom line:** Add **Prerequisites** (top) and **Quick Start** (after design, before full impl). Structure **Configuration** as a reference table. Add **Observability** & **Safety/Rollback** sections. This covers the solo-dev reality better.

Want me to write an updated master prompt?

## Human

yes please

## Assistant

Done. **Artifact ID: 1** — Master prompt saved and ready.

This comprehensive prompt template covers:

✅ **All 8 missing sections** (prerequisites, quick start, architecture, config reference, observability, safety/rollback, integration points, steady-state operation)

✅ **Structured for your workflow:**
- Windows PowerShell 7.5+ compatibility
- Solo developer reality (backup/rollback-first)
- Large-scale operations (26K+ items)
- Multi-terminal debugging patterns
- Reference tables instead of prose

✅ **Customizable:** Bracketed sections `[...]` for your specific context

✅ **Quick checklist** at the bottom to validate before using

## How to Use It

When you need implementation documentation, grab the prompt from this file and customize:
```
[DOWNLOAD]: Use create_text_file tool only...

CONTEXT:
[Your specific problem]

PREREQUISITES & REQUIREMENTS:
Document what's needed...
```

The template handles everything else—sections, structure, best practices all baked in.

## Human

That's overboard.  Use the original prompt I gave you, and add a similar style section for steady state/operational use.

## Assistant

Done. **Artifact ID: 1** — Updated master prompt.

Kept your original structure and added **STEADY-STATE OPERATION** as a co-equal section with the same treatment. Much cleaner and more actionable than the bloated version.

The prompt now has:
- ✅ Original 4 sections (Solution Design, Implementation, Testing, Troubleshooting)
- ✅ New STEADY-STATE OPERATION section (same detailed format)
- ✅ Still under ~200 lines instead of 500+
- ✅ Focused and practical

## Human

Health checks are good, but make in ondemand.

Don't need:
"Monitoring
CPU usage: Should stay < [threshold]%
Memory usage: Should stay < [threshold]%
Disk I/O: Watch for [specific pattern]
Queue depth: Should stay < [threshold] items
Performance Expectations
Response time: [p95 metric]
Throughput: [req/sec or similar]
Error rate: [acceptable threshold]
Resource Utilization
Disk space growth: ~[X] GB/day
CPU: [Pattern description]
Memory: [Pattern description]



"

don't need:
"### For Large-Scale Operations (26K+ items)
- Clearly document resource requirements upfront
- Include performance tuning for scale
- Provide monitoring/alerting setup
- Make batch operations explicit"

## Assistant

Done. **Artifact ID: 1** — Updated.

Changes made:
- ✅ Health checks now **on-demand** (not periodic/scheduled)
- ✅ Removed Monitoring, Performance Expectations, Resource Utilization sections
- ✅ Removed Large-Scale Operations tips
- ✅ Kept everything else focused and actionable

Cleaner now.
