# Flow-of-Action Paradigm for rca

**Status**: Design Document
**Task**: #986
**Author**: Claude Code
**Date**: 2026-02-16

## Abstract

The **Flow-of-Action Paradigm** provides a systematic way to trace execution paths through code during Root Cause Analysis. Unlike static data flow analysis, this paradigm captures the *actual* sequence of actions taken during an investigation and maps them to the code's intended execution paths.

## Problem Statement

Current rca Phase 1 ("data_flow_trace") has conceptual guidance but no implementation:
- Phase detection relies on keyword patterns in tool output
- No systematic reconstruction of execution paths
- No way to identify the "first divergence" point (where actual behavior diverges from expected)
- Relies on manual tracing via Serena MCP tools

The Flow-of-Action Paradigm addresses these gaps by:

1. **Action Abstraction**: Define what constitutes an "action" in the RCA context
2. **Action Graph Construction**: Build a directed graph of actions executed during investigation
3. **Divergence Detection**: Identify where actual execution diverges from expected paths
4. **Evidence Binding**: Link each action to concrete evidence (files read, tools invoked, outputs)

## Core Concepts

### 1. Action Definition

An **Action** is a discrete unit of investigation activity with:

| Attribute | Type | Description |
|-----------|------|-------------|
| `action_id` | str | UUID for this action |
| `action_type` | ActionType | Type of action (enum) |
| `timestamp` | datetime | When action occurred |
| `tool_used` | str | Tool name (Read, Grep, Bash, etc.) |
| `tool_input` | dict | Serialized tool input |
| `tool_output` | str | Tool output (truncated if large) |
| `evidence_refs` | list[str] | IDs of evidence items produced |
| `parent_action_id` | str \| None | Previous action in sequence |
| `phase` | int | RCA phase when action occurred |

### 2. ActionType Enum

```python
class ActionType(Enum):
    """Types of actions in RCA investigation."""

    # Information gathering
    READ_FILE = "read_file"           # Read tool usage
    SEARCH_CODE = "search_code"        # Grep/Serena find_symbol
    LIST_DIR = "list_dir"              # Directory listing

    # Analysis
    TRACE_SYMBOL = "trace_symbol"      # Serena find_referencing_symbols
    INSPECT_VARIABLE = "inspect_variable"  # Variable inspection
    EXECUTE_TEST = "execute_test"      # Running tests

    # Investigation
    FORM_HYPOTHESIS = "form_hypothesis"    # Hypothesis creation
    VERIFY_HYPOTHESIS = "verify_hypothesis" # Hypothesis testing
    ELIMINATE_CAUSE = "eliminate_cause"     # Ruling out causes

    # External
    SEARCH_HISTORY = "search_history"    # CKS/CHS search
    FETCH_DOCS = "fetch_docs"           # Web research

    # Meta
    SYNTHESIZE = "synthesize"           # Synthesis checkpoint
    RECORD_OUTCOME = "record_outcome"   # Finding recording
```

### 3. Action Graph Structure

```
[Start: User Problem Report]
    |
    v
[Action 1: Search History] --> [Action 2: Read Error File]
    |                              |
    v                              v
[Action 3: Trace Entry Point] <--+
    |
    v
[Action 4: Follow Execution Path]
    |
    v
[Action 5: Identify Divergence Point]
    |
    v
[Action 6: Form Hypothesis]
    |
    v
[Action 7: Verify Hypothesis]
    |
    v
[End: Root Cause Found]
```

## Implementation Design

### Component 1: Action Tracer

**File**: `src/rca/action_tracer.py`

```python
class ActionTracer:
    """Records and manages actions during RCA investigation."""

    def record_action(
        self,
        action_type: ActionType,
        tool_used: str,
        tool_input: dict,
        tool_output: str,
        phase: int,
    ) -> Action:
        """Record a new action and return it."""

    def get_action_graph(self) -> DirectedGraph:
        """Get the complete action graph for this session."""

    def find_divergence_point(
        self,
        expected_path: list[ActionType],
    ) -> Action | None:
        """Find where actual execution diverged from expected."""
```

### Component 2: Expected Path Builder

**File**: `src/rca/expected_paths.py`

Defines common execution patterns for different problem types:

```python
EXPECTED_PATHS = {
    ProblemType.ERROR: [
        ActionType.SEARCH_HISTORY,
        ActionType.READ_FILE,
        ActionType.TRACE_SYMBOL,
        ActionType.FORM_HYPOTHESIS,
        ActionType.VERIFY_HYPOTHESIS,
    ],
    ProblemType.TEST: [
        ActionType.SEARCH_HISTORY,
        ActionType.READ_TEST_FILE,
        ActionType.EXECUTE_TEST,
        ActionType.INSPECT_VARIABLE,
        ActionType.FORM_HYPOTHESIS,
    ],
    # ... more patterns
}
```

### Component 3: Hook Integration

**File**: `skill/hooks/PostToolUse_rca_action_tracker.py`

New PostToolUse hook that:
1. Intercepts all tool usage during active RCA session
2. Classifies the tool usage as an Action
3. Adds action to the action graph
4. Detects divergence from expected path
5. Emits warnings when patterns deviate

### Component 4: Flow Visualization

**File**: `src/rca/flow_visualizer.py`

```python
class FlowVisualizer:
    """Generate visual representations of action flow."""

    def render_mermaid(self, graph: DirectedGraph) -> str:
        """Render action graph as Mermaid diagram."""

    def render_text(self, graph: DirectedGraph) -> str:
        """Render action graph as ASCII/Unicode art."""

    def highlight_divergence(
        self,
        graph: DirectedGraph,
        divergence_point: Action,
    ) -> str:
        """Highlight where actual diverged from expected."""
```

## Hook Integration Points

### Existing: `PostToolUse_rca_phase_tracker.py`

Current behavior:
- Detects phase based on tool name and output patterns
- Updates `current_phase` in state
- Records `phases_completed`

**Enhancement**: Add action recording
```python
# After phase detection, record the action
action = action_tracer.record_action(
    action_type=classify_action(tool_name, tool_input),
    tool_used=tool_name,
    tool_input=tool_input,
    tool_output=tool_output,
    phase=detected_phase,
)
```

### New: `PostToolUse_rca_action_tracker.py`

Dedicated hook for building the action graph:
- Runs for ALL tools (unlike phase tracker which only cares about RCA-specific tools)
- Builds comprehensive action trace
- Stores in `rca_actions.json` alongside `rca_workflow.json`

## State Structure

### `rca_actions.json`

```json
{
  "session_id": "rca_abc123",
  "actions": [
    {
      "action_id": "act_001",
      "action_type": "search_history",
      "tool_used": "WebSearch",
      "tool_input": {"query": "similar hook errors"},
      "timestamp": "2026-02-16T12:00:00",
      "phase": -1,
      "parent_id": null
    },
    {
      "action_id": "act_002",
      "action_type": "read_file",
      "tool_used": "Read",
      "tool_input": {"file_path": "error.log"},
      "timestamp": "2026-02-16T12:00:30",
      "phase": 0,
      "parent_id": "act_001"
    }
  ],
  "divergence_point": null,
  "expected_path": "error",
  "created_at": "2026-02-16T12:00:00",
  "updated_at": "2026-02-16T12:05:00"
}
```

## API Surface

### For SKILL.md Integration

```python
from rca.action_tracer import ActionTracer, ActionType

# At start of RCA
tracer = ActionTracer(session_id)

# During investigation (automated via hook)
action = tracer.record_action(
    action_type=ActionType.READ_FILE,
    tool_used="Read",
    tool_input={"file_path": "src/main.py"},
    tool_output="...",
    phase=1,
)

# Synthesis point
graph = tracer.get_action_graph()
divergence = tracer.find_divergence_point()

# Visualization
from rca.flow_visualizer import FlowVisualizer
viz = FlowVisualizer()
print(viz.highlight_divergence(graph, divergence))
```

## Phase 1 Enhancement

### Current Phase 1 Guidance

From SKILL.md:
> 1. **Start with a falsifiable symptom** — define exactly what is wrong
> 2. **Trace the real path, not the intended path** — use Serena MCP
> 3. **Find the first divergence** — earliest mismatch from expected

### New: Flow-of-Action Enhanced Phase 1

```markdown
## Phase 1: Data Flow Trace (Enhanced)

### Action-Based Tracing

1. **Start with falsifiable symptom** (unchanged)
2. **Build action graph** - ActionTracer automatically records your investigation path
3. **Compare to expected path** - System shows standard investigation pattern for this problem type
4. **Identify divergence** - First point where your investigation deviates from (or corrects) the expected path
5. **Trace from divergence** - Focus investigation from the divergence point forward

### Visualization

Use `/rca --show-flow` to see:
- Mermaid diagram of your action graph
- Highlighted divergence point
- Expected vs. actual paths

### Example Output

```
Expected: search_history → read_file → trace_symbol → form_hypothesis
Actual:   search_history → read_file → **list_dir** → read_file → form_hypothesis
                                        ↑ DIVERGENCE: You explored directory instead of tracing symbol
```

## Implementation Phases

### Phase 1: Core Action Tracer (Week 1)
- [ ] Create `Action` dataclass
- [ ] Create `ActionType` enum
- [ ] Implement `ActionTracer` class
- [ ] Add unit tests for action recording
- [ ] Add `rca_actions.json` state file

### Phase 2: Hook Integration (Week 1)
- [ ] Create `PostToolUse_rca_action_tracker.py`
- [ ] Integrate with existing phase tracker
- [ ] Add action classification logic
- [ ] Test hook records actions correctly

### Phase 3: Expected Paths (Week 2)
- [ ] Define expected paths for each ProblemType
- [ ] Implement `ExpectedPathBuilder`
- [ ] Add divergence detection algorithm
- [ ] Test divergence detection accuracy

### Phase 4: Visualization (Week 2)
- [ ] Create `FlowVisualizer` class
- [ ] Implement Mermaid rendering
- [ ] Implement ASCII rendering
- [ ] Add divergence highlighting
- [ ] Add `--show-flow` CLI option

### Phase 5: SKILL.md Integration (Week 3)
- [ ] Update Phase 1 documentation
- [ ] Add action tracing examples
- [ ] Add visualization examples
- [ ] Update synthesis checkpoint format

## Success Criteria

1. **Action Coverage**: Every tool usage during RCA is recorded as an Action
2. **Divergence Detection**: System correctly identifies first deviation from expected path
3. **Visualization**: User can view action graph as Mermaid diagram
4. **Performance**: Action tracking adds <10ms overhead per tool call
5. **Multi-Terminal Safe**: Actions tracked per terminal (same isolation as workflow state)

## Open Questions

1. **Action Granularity**: Should we record each individual tool call, or aggregate related calls?
   - *Decision*: Record each tool call, aggregate during visualization

2. **Output Storage**: Tool outputs can be large (megabytes). Should we store full output?
   - *Decision*: Store truncated version (first 1KB) + hash of full output

3. **Cross-Session Actions**: Should actions persist across compaction?
   - *Decision*: Yes, store in `rca_actions.json` alongside workflow state

4. **Expected Path Authority**: Who defines the "expected" investigation path?
   - *Decision*: Start with heuristics based on ProblemType, evolve with learning from CKS

## Dependencies

- **Internal**: `PostToolUse_rca_phase_tracker.py` (existing)
- **Internal**: `session.py` ProblemType enum (existing)
- **External**: Serena MCP (for action classification enhancement)
- **Optional**: Mermaid CLI (for diagram rendering)

## Alternatives Considered

### Alternative A: Static Analysis Approach
- Use AST/static analysis to trace data flow
- **Rejected**: Doesn't capture actual investigation actions, only code structure

### Alternative B: Full Execution Tracing
- Trace every function call during code execution
- **Rejected**: Overkill for RCA; we trace investigation actions, not code execution

### Alternative C: Manual Graph Construction
- User manually builds action graph
- **Rejected**: Defeats purpose of automation; hook-based is better

## References

- **Memory**: `MEMORY.md` - "Reading Order = Execution Order"
- **SKILL.md**: Phase 1 "Data Flow Trace" guidance
- **SimpleRCAEngine**: Fishbone/Fault Tree analysis (complementary methodology)

---

**Next Steps**: Review this design with user, then begin Phase 1 implementation.
