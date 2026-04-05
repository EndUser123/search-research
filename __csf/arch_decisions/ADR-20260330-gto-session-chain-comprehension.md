# ADR-20260330: GTO Session Chain Comprehension

## Status

Draft

## Context

When a user asks "what are we doing?", "what's the status?", or "what's needed next?", GTO must understand the session chain — starting from the first transcript and linked forward through compact events to the current session.

**Current state:**
- GTO's `SessionGoalDetector` uses rigid regex patterns (`"the goal is"`, `"I need to"`, `"let's build"`) that only match explicit goal statements, not question-style intent ("what are we working on?")
- GTO only reads the most recent transcript, not the full session chain
- Handoff context (`current_goal`) exists but isn't passed to the goal detector
- No mechanism for the LLM's comprehension to be used — only pattern matching

**The problem:**
- User asks "what are we doing?" in a new terminal session
- GTO has no loaded handoff context
- Regex patterns don't match question-style queries
- Even if they did, the session chain isn't traversed — only the most recent transcript

## Decision

### Core Principle: Use LLM Comprehension, Not Pattern Matching

The LLM already understands language naturally. The system should pass transcript content to the LLM rather than trying to regex-match intent. This applies to both:
- Historical session chains (subagent reading)
- Current session context (LLM's in-memory comprehension)

### Architecture: Two-Stage Synthesis

```
GTO Orchestrator
├── Stage 1: Subagent reads session chain
│   └── Reads transcript chain via handoff links
│   └── Produces structured findings about historical work
│
├── Stage 2: Current LLM contributes current session context
│   └── In-memory understanding of what's happening now
│   └── No extra tokens needed
│
└── Stage 3: Synthesis + Critique Loop
    └── Current LLM combines subagent findings + current context
    └── Grades output: PASS or FAIL with specific feedback
    └── FAIL → subagent reruns with targeted fixes
    └── PASS → output to user
```

### Key Design Decisions

**D1: Subagent handles historical chain, current LLM handles current session**
- Avoids forcing the subagent to re-read what the LLM already knows
- Token-efficient: subagent reads old transcripts, LLM contributes live context
- The best synthesis comes from combining both sources

**D2: Critique loop is specific, not generic**
- When grading FAIL, the LLM specifies exactly what's wrong: "you missed X, Y was wrong, Z needs more depth"
- This targeted feedback lets the subagent fix precisely what failed
- Generic "bad output" feedback wastes cycles

**D3: Session chain traversal via handoff transcript_path links**
- Each transcript file may contain a `transcript_path` field pointing to the prior transcript
- Subagent follows the chain backward to build complete picture of session history
- This is self-contained: no dependency on external handoff files beyond the chain

**D4: Fast-path regex preserved for explicit goal statements**
- When regex finds a clear goal statement, skip subagent call
- This keeps simple cases fast while enabling comprehension for complex cases

### What GTO Should Surface

When user asks "what are we doing?":
1. **Historical work**: What was the session chain focused on? (from subagent analysis)
2. **Current work**: What is the current session doing right now? (from LLM context)
3. **Status**: What phase/stage are we at?
4. **Next steps**: What needs to happen next?

### Open Questions

- Q1: How deep should the session chain traversal go? (full chain vs last N transcripts)
- Q2: Should we use the handoff file's `current_goal` as a hint, or only the transcript chain?
- Q3: How many critique loop iterations before giving up and presenting partial results?

## Consequences

**Positive:**
- GTO understands question-style intent, not just imperative goal statements
- Session chain comprehension enables accurate "what are we doing?" answers
- Token-efficient: historical = subagent, current = LLM's memory
- Self-improving through critique loop

**Negative:**
- Subagent invocation adds latency on first query in a new terminal
- Critique loop adds complexity to the GTO orchestrator

**Risks:**
- Session chain could be very long → subagent takes too long reading
- Mitigation: limit to last N transcripts or last 24 hours of chain
