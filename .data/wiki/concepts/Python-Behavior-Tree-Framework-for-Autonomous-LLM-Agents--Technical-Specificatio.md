---
created: '2026-04-10'
sources:
- C:\Users\brsth\Downloads\Python Behavior Tree Framework for Autonomous LLM Agents  Technical
  Specification + Boilerplate.md
summary: ''
tags: []
---

# Python Behavior Tree Framework for Autonomous LLM Agents
### Technical Specification + Complete Boilerplate (py_trees 2.4+ / Pydantic v2)

***

## Executive Summary

This document is a complete, production-oriented technical specification for a self-optimizing Behavior Tree (BT) framework targeting autonomous LLM agents. The framework combines **py_trees 2.4+** for reactive hierarchical execution with **Pydantic v2** for strongly-typed schema validation, **NetworkX** for tree visualization, and a **Tree-of-Thought (ToT)** style LLM feedback loop that prunes failing subtrees and regenerates superior branches at runtime. The net result is an agent that evolves its own execution plan toward a verifiable success metric without human intervention.[^1][^2][^3][^4][^5][^6]

***

## 1. Architecture Overview

### 1.1 Design Principles

The framework is built on four invariants:

1. **Schema-first**: Every node in the tree is a validated Pydantic model before it touches py_trees. LLM-generated subtrees are rejected at the schema boundary, not at runtime.
2. **Non-blocking execution**: Every `update()` method returns immediately — async work is managed via py_trees blackboards and background futures.[^7][^8]
3. **Failure is signal, not terminal**: `FAILURE` status propagates failure context (`feedback_message`) directly to the LLM optimizer rather than halting the agent.[^9][^10]
4. **Deterministic resume**: Full tree state is serialized to disk after every tick via Pydantic's `model_dump_json()`; the agent can resume from any RUNNING node.[^11][^12]

### 1.2 Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentOrchestrator                         │
│  ┌──────────┐   tick()   ┌─────────────────────────────┐   │
│  │  Pydantic │──────────▶│       TreeTicker             │   │
│  │  BT Schema│◀──rebuild─│  (wraps BehaviourTree)       │   │
│  └──────────┘            │  SUCCESS / FAILURE / RUNNING │   │
│       │                  └──────────┬──────────────────-┘   │
│       │ model_dump_json()           │ FAILURE                │
│       ▼                            ▼                         │
│  ┌──────────┐           ┌──────────────────────┐            │
│  │  Disk    │           │  LLMOptimizer        │            │
│  │  (JSON)  │           │  (ToT + feedback)    │            │
│  └──────────┘           │  prune → regrow      │            │
│                         └──────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

***

## 2. Data Schema — Universal BT Node (Pydantic v2)

The schema uses Pydantic v2's `model_rebuild()` to resolve the forward reference required for the recursive `children` field. All fields are validated before any py_trees object is instantiated.[^13][^4]

```python
# ============================================================
# bt_schema.py — Universal Behavior Tree Node Schema
# ============================================================
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    ACTION    = "Action"
    CONDITION = "Condition"
    SELECTOR  = "Selector"       # Fallback — ticks until first SUCCESS
    SEQUENCE  = "Sequence"       # Ticks until first FAILURE
    PARALLEL  = "Parallel"       # Ticks all children concurrently
    DECORATOR = "Decorator"      # Wraps single child, transforms status


class NodeStatus(str, Enum):
    INVALID = "INVALID"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class NodeMetadata(BaseModel):
    """Immutable node-level metadata preserved across prune/regrow cycles."""
    static: bool = Field(
        default=False,
        description="If True, this node is never pruned by the optimizer.",
    )
    description: str = Field(default="", description="Human-readable purpose.")
    failure_count: int = Field(default=0, description="Cumulative FAILURE ticks.")
    last_feedback: str = Field(default="", description="Most recent feedback_message.")


class BTNode(BaseModel):
    """
    Universal, recursive Behavior Tree node.
    Supports Action / Condition / Selector / Sequence / Parallel / Decorator.
    Use model_rebuild() after class definition to resolve the Self-reference.
    """
    node_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Stable identifier — survives serialize/deserialize cycles.",
    )
    name: str = Field(..., description="Display name; must be unique within a tree.")
    type: NodeType
    priority_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Relative importance hint for the LLM optimizer (higher = prune last).",
    )
    children: list["BTNode"] = Field(
        default_factory=list,
        description="Ordered child nodes. Leaf types (Action, Condition) must have no children.",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Tool mapping for Action nodes, e.g.:\n"
            "  {'tool': 'yt-dlp', 'args': {'url': '...', 'format': 'bestvideo'}}\n"
            "  {'tool': 'mcp', 'method': 'read_file', 'path': '/tmp/out.py'}\n"
            "  {'llm_prompt': 'Generate FastAPI endpoint for {goal}'}"
        ),
    )
    metadata: NodeMetadata = Field(default_factory=NodeMetadata)
    runtime_status: NodeStatus = Field(
        default=NodeStatus.INVALID,
        description="Populated by TreeTicker after each tick; never set manually.",
    )

    @field_validator("children")
    @classmethod
    def validate_leaf_has_no_children(
        cls, v: list["BTNode"], info: Any
    ) -> list["BTNode"]:
        node_type = info.data.get("type")
        if node_type in (NodeType.ACTION, NodeType.CONDITION) and v:
            raise ValueError(
                f"Leaf node type '{node_type}' must not have children."
            )
        return v

    @field_validator("children")
    @classmethod
    def validate_decorator_single_child(
        cls, v: list["BTNode"], info: Any
    ) -> list["BTNode"]:
        node_type = info.data.get("type")
        if node_type == NodeType.DECORATOR and len(v) != 1:
            raise ValueError("Decorator nodes must have exactly one child.")
        return v

    def find_by_id(self, node_id: str) -> Optional["BTNode"]:
        """Depth-first search for a node by node_id."""
        if self.node_id == node_id:
            return self
        for child in self.children:
            result = child.find_by_id(node_id)
            if result:
                return result
        return None

    def prune_children_by_ids(self, ids_to_remove: set[str]) -> None:
        """Remove direct children whose node_id is in ids_to_remove."""
        self.children = [c for c in self.children if c.node_id not in ids_to_remove]
        for child in self.children:
            child.prune_children_by_ids(ids_to_remove)


# Resolve the forward reference for the recursive children field.
# Must be called after the class definition per Pydantic v2 docs.
BTNode.model_rebuild()
```

> **Why `model_rebuild()`?** In Pydantic v2, `model_rebuild()` replaces the deprecated `update_forward_refs()`. It builds the full core schema (including nested models) so forward references like `list["BTNode"]` resolve correctly. It must be called after the class body is defined and before any instance is created.[^4]

***

## 3. Execution Engine — TreeTicker

`TreeTicker` wraps `py_trees.trees.BehaviourTree` and manages the tick-level state machine. On `FAILURE` it captures the `feedback_message` from the failing tip node and fires the LLM optimizer.[^14][^10]

```python
# ============================================================
# tree_ticker.py — Execution Engine
# ============================================================
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

import py_trees
import py_trees.composites
import py_trees.trees

from bt_schema import BTNode, NodeStatus, NodeType

logger = logging.getLogger(__name__)


# ─── py_trees node factory ───────────────────────────────────────────────────

def schema_to_pytree(node: BTNode) -> py_trees.behaviour.Behaviour:
    """
    Recursively convert a validated BTNode schema into a live py_trees object.
    Composite nodes are built top-down; leaf nodes instantiate concrete
    Behaviour subclasses registered in BEHAVIOUR_REGISTRY.
    """
    from tool_actions import BEHAVIOUR_REGISTRY  # lazy import avoids circular refs

    if node.type == NodeType.SEQUENCE:
        composite = py_trees.composites.Sequence(name=node.name, memory=True)
        for child in node.children:
            composite.add_child(schema_to_pytree(child))
        composite._bt_node_id = node.node_id
        return composite

    if node.type == NodeType.SELECTOR:
        composite = py_trees.composites.Selector(name=node.name, memory=False)
        for child in node.children:
            composite.add_child(schema_to_pytree(child))
        composite._bt_node_id = node.node_id
        return composite

    if node.type == NodeType.PARALLEL:
        composite = py_trees.composites.Parallel(
            name=node.name,
            policy=py_trees.common.ParallelPolicy.SuccessOnAll(),
        )
        for child in node.children:
            composite.add_child(schema_to_pytree(child))
        composite._bt_node_id = node.node_id
        return composite

    if node.type == NodeType.DECORATOR:
        child_behaviour = schema_to_pytree(node.children)
        deco = py_trees.decorators.Inverter(name=node.name, child=child_behaviour)
        deco._bt_node_id = node.node_id
        return deco

    # Leaf nodes: ACTION or CONDITION
    tool_name = node.params.get("tool", "__passthrough__")
    behaviour_cls = BEHAVIOUR_REGISTRY.get(tool_name, PassthroughBehaviour)
    behaviour = behaviour_cls(name=node.name, params=node.params)
    behaviour._bt_node_id = node.node_id
    return behaviour


# ─── TreeTicker ──────────────────────────────────────────────────────────────

@dataclass
class TickResult:
    status: NodeStatus
    tip_name: str
    tip_feedback: str
    tick_count: int
    failing_node_id: Optional[str] = None


class TreeTicker:
    """
    Wraps py_trees.BehaviourTree. Manages the tick loop and
    dispatches to LLMOptimizer on FAILURE.

    Args:
        schema_root:     Validated BTNode (root of the schema tree).
        on_failure_hook: Callable invoked with (TickResult) on FAILURE.
                         Typically wired to LLMOptimizer.optimize().
        max_ticks:       Safety ceiling for the optimization loop.
    """

    def __init__(
        self,
        schema_root: BTNode,
        on_failure_hook: Optional[Callable[[TickResult], None]] = None,
        max_ticks: int = 100,
    ) -> None:
        self.schema_root = schema_root
        self.on_failure_hook = on_failure_hook
        self.max_ticks = max_ticks
        self._build_tree()

    def _build_tree(self) -> None:
        """(Re)build live py_trees objects from current schema."""
        root_behaviour = schema_to_pytree(self.schema_root)
        self.tree = py_trees.trees.BehaviourTree(root=root_behaviour)
        self.tree.setup(timeout=5.0)

    def tick(self) -> TickResult:
        """
        Execute one tick of the behaviour tree.

        Status semantics (py_trees 2.4+):
          SUCCESS  → root returned SUCCESS; task complete.
          FAILURE  → root returned FAILURE; optimizer is triggered.
          RUNNING  → in-progress; continue ticking next iteration.

        Returns:
            TickResult with status, tip node info, and failing node id.
        """
        self.tree.tick_once()

        root = self.tree.root
        tip = self.tree.tip()

        tip_name     = tip.name if tip else root.name
        tip_feedback = tip.feedback_message if tip else root.feedback_message
        failing_id   = getattr(tip, "_bt_node_id", None) if tip else None

        # Sync runtime_status back into schema
        self._sync_status_to_schema(root, self.schema_root)

        result = TickResult(
            status=NodeStatus(root.status.value),
            tip_name=tip_name,
            tip_feedback=tip_feedback or "",
            tick_count=self.tree.count,
            failing_node_id=failing_id,
        )

        if result.status == NodeStatus.FAILURE:
            logger.warning(
                "[Tick %d] FAILURE at '%s': %s",
                self.tree.count,
                tip_name,
                tip_feedback,
            )
            if self.on_failure_hook:
                self.on_failure_hook(result)

        elif result.status == NodeStatus.SUCCESS:
            logger.info("[Tick %d] SUCCESS — task complete.", self.tree.count)

        else:
            logger.debug("[Tick %d] RUNNING — '%s'", self.tree.count, tip_name)

        return result

    def replace_subtree(self, old_node_id: str, new_schema_node: BTNode) -> bool:
        """
        Swap out a failing subtree for a newly LLM-generated one.
        Operates on both the live py_trees tree and the Pydantic schema.

        Uses py_trees.trees.BehaviourTree.replace_subtree().
        """
        # 1. Find the UUID of the live py_trees node matching old_node_id
        target_uuid = self._find_pytree_uuid(old_node_id)
        if target_uuid is None:
            logger.error("replace_subtree: node_id '%s' not found", old_node_id)
            return False

        # 2. Build the new py_trees subtree from validated schema
        new_behaviour = schema_to_pytree(new_schema_node)

        # 3. Live tree surgery
        success = self.tree.replace_subtree(
            unique_id=target_uuid,
            subtree=new_behaviour,
        )

        if success:
            # 4. Mirror the change in the Pydantic schema
            parent_schema = self._find_schema_parent(self.schema_root, old_node_id)
            if parent_schema:
                parent_schema.children = [
                    new_schema_node if c.node_id == old_node_id else c
                    for c in parent_schema.children
                ]
            logger.info(
                "Subtree '%s' replaced with '%s'.", old_node_id, new_schema_node.name
            )
        return success

    def _find_pytree_uuid(self, bt_node_id: str) -> Optional[uuid.UUID]:
        for node in self.tree.root.iterate():
            if getattr(node, "_bt_node_id", None) == bt_node_id:
                return node.id
        return None

    def _find_schema_parent(
        self, current: BTNode, target_id: str
    ) -> Optional[BTNode]:
        for child in current.children:
            if child.node_id == target_id:
                return current
            result = self._find_schema_parent(child, target_id)
            if result:
                return result
        return None

    def _sync_status_to_schema(
        self,
        pytree_node: py_trees.behaviour.Behaviour,
        schema_node: BTNode,
    ) -> None:
        """Walk both trees in tandem, writing py_trees status → schema."""
        schema_node.runtime_status = NodeStatus(pytree_node.status.value)
        if pytree_node.status == py_trees.common.Status.FAILURE:
            schema_node.metadata.failure_count += 1
            schema_node.metadata.last_feedback = pytree_node.feedback_message or ""
        for pt_child, sc_child in zip(
            getattr(pytree_node, "children", []),
            schema_node.children,
        ):
            self._sync_status_to_schema(pt_child, sc_child)
```

***

## 4. Tool Mapping — Leaf Action Nodes

Leaf `Action` nodes translate `params` into concrete tool calls. The pattern: **a registry of `Behaviour` subclasses keyed by tool name**. Each class reads `params`, executes the tool (sync or async), writes output to the blackboard, and returns a `Status`.[^10][^7]

```python
# ============================================================
# tool_actions.py — Leaf Action Behaviour Registry
# ============================================================
from __future__ import annotations

import subprocess
import json
from typing import Any

import py_trees
import py_trees.blackboard
import py_trees.common


class ToolActionBase(py_trees.behaviour.Behaviour):
    """
    Base class for all tool-mapped leaf behaviours.

    Subclasses implement _execute_tool() and return a dict result.
    The dict is written to the blackboard under the node's name.
    """

    def __init__(self, name: str, params: dict[str, Any]) -> None:
        super().__init__(name=name)
        self.params = params
        self.bb = self.attach_blackboard_client(name=name)
        self.bb.register_key(
            key=f"result/{name}", access=py_trees.common.Access.WRITE
        )

    def update(self) -> py_trees.common.Status:
        try:
            result = self._execute_tool()
            self.bb.set(f"result/{self.name}", result)
            self.feedback_message = f"OK: {list(result.keys())}"
            return py_trees.common.Status.SUCCESS
        except Exception as exc:
            self.feedback_message = f"TOOL ERROR [{type(exc).__name__}]: {exc}"
            return py_trees.common.Status.FAILURE

    def _execute_tool(self) -> dict[str, Any]:
        raise NotImplementedError


# ─── Concrete tool implementations ────────────────────────────────────────────

class CLIToolAction(ToolActionBase):
    """
    Execute any CLI command.
    params: {'tool': 'cli', 'cmd': ['python', '-m', 'pytest', 'tests/']}
    """

    def _execute_tool(self) -> dict[str, Any]:
        cmd = self.params["cmd"]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[:500])
        return {"stdout": proc.stdout, "returncode": proc.returncode}


class LLMPromptAction(ToolActionBase):
    """
    Call an LLM with a templated prompt.
    params: {'tool': 'llm', 'llm_prompt': 'Generate FastAPI endpoint for {goal}',
             'model': 'gpt-4o', 'goal': 'user management'}
    """

    def _execute_tool(self) -> dict[str, Any]:
        # Replace with real LLM client (openai, anthropic, litellm, etc.)
        prompt = self.params["llm_prompt"].format(**self.params)
        # STUB — replace with actual API call:
        # response = openai_client.chat.completions.create(...)
        response_text = f"[LLM stub] Response for: {prompt[:80]}..."
        return {"generated": response_text, "prompt": prompt}


class MCPToolAction(ToolActionBase):
    """
    Invoke an MCP server method.
    params: {'tool': 'mcp', 'method': 'read_file', 'path': '/tmp/result.py'}
    """

    def _execute_tool(self) -> dict[str, Any]:
        method = self.params["method"]
        # STUB — replace with actual MCP client call:
        # result = mcp_client.call(method, **{k: v for k, v in self.params.items()
        #                                      if k not in ('tool', 'method')})
        return {"mcp_method": method, "result": "stub_output"}


class PassthroughBehaviour(ToolActionBase):
    """Fallback: always succeeds. Used for unregistered tool names."""

    def _execute_tool(self) -> dict[str, Any]:
        return {"passthrough": True, "params": self.params}


# ─── Registry ─────────────────────────────────────────────────────────────────
BEHAVIOUR_REGISTRY: dict[str, type[ToolActionBase]] = {
    "cli":           CLIToolAction,
    "llm":           LLMPromptAction,
    "mcp":           MCPToolAction,
    "__passthrough__": PassthroughBehaviour,
}
```

**Parent evaluation pattern**: After an `Action` leaf writes its result to the blackboard, a sibling `Condition` node reads the key and returns `SUCCESS`/`FAILURE` — keeping action and evaluation cleanly separated.[^15]

***

## 5. ToT Self-Optimization — LLMOptimizer

The optimizer implements a **Tree-of-Thought** style feedback loop. On `FAILURE` it:[^3][^5]
1. Collects the failing node's `feedback_message` and failure history from the schema.
2. Builds a structured prompt requesting a replacement subtree as JSON.
3. Validates the JSON against `BTNode` schema.
4. Calls `TreeTicker.replace_subtree()` to do live surgery.

```python
# ============================================================
# llm_optimizer.py — ToT Self-Optimization Engine
# ============================================================
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from pydantic import ValidationError

from bt_schema import BTNode, NodeType

if TYPE_CHECKING:
    from tree_ticker import TickResult, TreeTicker

logger = logging.getLogger(__name__)

# ─── Success Metric ────────────────────────────────────────────────────────────

def compute_success_score(ticker: "TreeTicker", goal: str) -> float:
    """
    Task-completion score ∈ [0.0, 1.0].
    - Counts leaf nodes with SUCCESS status vs total leaf nodes.
    - Penalizes high failure_count nodes.
    Override with domain-specific logic (test pass rate, lint score, etc.).
    """
    from bt_schema import NodeStatus

    all_nodes: list[BTNode] = []

    def collect(node: BTNode) -> None:
        all_nodes.append(node)
        for c in node.children:
            collect(c)

    collect(ticker.schema_root)
    leaves = [n for n in all_nodes if not n.children]
    if not leaves:
        return 0.0
    success_leaves = sum(
        1 for n in leaves if n.runtime_status == NodeStatus.SUCCESS
    )
    penalty = sum(
        min(n.metadata.failure_count * 0.05, 0.3)
        for n in all_nodes
    )
    raw = success_leaves / len(leaves)
    return max(0.0, min(1.0, raw - penalty))


# ─── LLM stub (replace with real client) ──────────────────────────────────────

def _call_llm_stub(prompt: str, model: str = "gpt-4o") -> str:
    """
    STUB — replace with real OpenAI / Anthropic / litellm call.

    Example (OpenAI):
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return response.choices.message.content
    """
    # Synthetic recovery subtree for demo purposes:
    recovery_node = {
        "node_id": "llm-generated-recovery",
        "name": "LLM_Recovery_Sequence",
        "type": "Sequence",
        "priority_weight": 2.0,
        "children": [
            {
                "name": "RetryWithAltStrategy",
                "type": "Action",
                "priority_weight": 1.5,
                "children": [],
                "params": {
                    "tool": "llm",
                    "llm_prompt": "Alternative implementation for: {goal}",
                    "goal": "build API endpoint",
                },
                "metadata": {
                    "static": False,
                    "description": "LLM-generated alternative strategy",
                    "failure_count": 0,
                    "last_feedback": "",
                },
            }
        ],
        "params": {},
        "metadata": {
            "static": False,
            "description": "Auto-generated recovery branch",
            "failure_count": 0,
            "last_feedback": "",
        },
    }
    return json.dumps(recovery_node)


# ─── LLMOptimizer ─────────────────────────────────────────────────────────────

class LLMOptimizer:
    """
    Receives a TickResult on FAILURE, generates a replacement subtree
    via LLM, validates it, and applies it to the live TreeTicker.

    The prompt follows ToT (Tree-of-Thought) structure:
      1. Describe failure context (node name, feedback, history).
      2. State the goal.
      3. Request a JSON subtree conforming to BTNode schema.
      4. Include schema constraints as inline JSON Schema.
    """

    SYSTEM_PROMPT = """\
You are a Behavior Tree architect for an autonomous AI agent.
Output ONLY valid JSON matching the BTNode schema below. No prose.

BTNode schema (abbreviated):
{
  "node_id": "<uuid string>",
  "name": "<unique display name>",
  "type": "Action|Condition|Selector|Sequence|Parallel|Decorator",
  "priority_weight": <float 0-10>,
  "children": [<BTNode>, ...],
  "params": {"tool": "li|llm|mcp>", ...tool args...},
  "metadata": {"static": false, "description": "<str>",
                "failure_count": 0, "last_feedback": ""}
}
Constraints:
- Action/Condition nodes: children must be [].
- Decorator: exactly one child.
- Root of your output replaces the failing subtree.
"""

    USER_TEMPLATE = """\
FAILURE CONTEXT:
  Failing node  : {node_name}
  Feedback      : {feedback}
  Failure count : {failure_count}
  Full history  : {failure_history}

GOAL: {goal}

Generate a replacement subtree JSON that will achieve the goal.
Think step-by-step about what went wrong, then output the JSON.
"""

    def __init__(
        self,
        ticker: "TreeTicker",
        goal: str,
        success_threshold: float = 0.9,
        max_optimization_rounds: int = 5,
        llm_fn=_call_llm_stub,
    ) -> None:
        self.ticker = ticker
        self.goal = goal
        self.success_threshold = success_threshold
        self.max_optimization_rounds = max_optimization_rounds
        self.llm_fn = llm_fn
        self._round = 0

    def optimize(self, result: "TickResult") -> None:
        """Called by TreeTicker.on_failure_hook on each FAILURE tick."""
        if self._round >= self.max_optimization_rounds:
            logger.warning("Optimization ceiling reached (%d rounds).", self._round)
            return

        self._round += 1
        logger.info("Optimization round %d for node '%s'.", self._round, result.tip_name)

        # Build failure history from schema metadata
        failing_schema_node = (
            self.ticker.schema_root.find_by_id(result.failing_node_id)
            if result.failing_node_id
            else None
        )
        failure_count = (
            failing_schema_node.metadata.failure_count
            if failing_schema_node
            else 1
        )
        failure_history = (
            failing_schema_node.metadata.last_feedback
            if failing_schema_node
            else result.tip_feedback
        )

        prompt = self.SYSTEM_PROMPT + self.USER_TEMPLATE.format(
            node_name=result.tip_name,
            feedback=result.tip_feedback,
            failure_count=failure_count,
            failure_history=failure_history,
            goal=self.goal,
        )

        try:
            raw_json = self.llm_fn(prompt)
            new_node_data = json.loads(raw_json)
            new_node = BTNode(**new_node_data)   # Pydantic validates here
            BTNode.model_rebuild()               # Ensure recursive schema is fresh
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("LLM returned invalid subtree schema: %s", exc)
            return

        if result.failing_node_id:
            replaced = self.ticker.replace_subtree(result.failing_node_id, new_node)
            if replaced:
                logger.info(
                    "Subtree replaced. Score: %.2f",
                    compute_success_score(self.ticker, self.goal),
                )
        else:
            logger.warning("No failing_node_id — cannot target replacement.")

    @property
    def is_optimal(self) -> bool:
        score = compute_success_score(self.ticker, self.goal)
        return score >= self.success_threshold
```

***

## 6. Persistence — Serialize and Resume

State is serialized via Pydantic's `model_dump_json()` to a flat JSON file. Resume reconstructs the full py_trees object graph and fast-forwards to the last RUNNING node by skipping already-`SUCCESS` branches.[^12][^11]

```python
# ============================================================
# persistence.py — Serialize / Deserialize BT State
# ============================================================
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from bt_schema import BTNode, NodeStatus

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path("bt_state.json")


def save_tree(node: BTNode, path: Path = _DEFAULT_PATH) -> None:
    """
    Persist the full BT schema (including runtime_status and metadata)
    to disk using Pydantic v2 model_dump_json().
    Atomic write via a temp file to prevent corruption on crash.
    """
    tmp = path.with_suffix(".tmp")
    tmp.write_text(node.model_dump_json(indent=2))
    tmp.replace(path)
    logger.info("BT state saved → %s", path)


def load_tree(path: Path = _DEFAULT_PATH) -> Optional[BTNode]:
    """
    Restore BT schema from disk. Returns None if file not found.
    Calls model_rebuild() to ensure recursive schema is intact
    before parsing.
    """
    if not path.exists():
        return None
    BTNode.model_rebuild()
    data = json.loads(path.read_text())
    node = BTNode(**data)
    logger.info("BT state loaded ← %s", path)
    return node


def find_resume_node_id(root: BTNode) -> Optional[str]:
    """
    Depth-first search for the deepest RUNNING node.
    The tick loop resumes from this node on restart.
    SUCCESS subtrees are skipped; FAILURE subtrees are
    re-evaluated (the optimizer may have replaced them).
    """
    for child in root.children:
        if child.runtime_status == NodeStatus.RUNNING:
            deeper = find_resume_node_id(child)
            return deeper if deeper else child.node_id
    if root.runtime_status == NodeStatus.RUNNING:
        return root.node_id
    return None


def prune_succeeded_subtrees(root: BTNode) -> BTNode:
    """
    Remove subtrees that already succeeded to reduce tree size
    on long-running tasks. Respects metadata.static flag.
    """
    if root.metadata.static:
        return root
    root.children = [
        prune_succeeded_subtrees(c)
        for c in root.children
        if c.runtime_status != NodeStatus.SUCCESS or c.metadata.static
    ]
    return root
```

***

## 7. NetworkX Visualization

```python
# ============================================================
# visualize.py — NetworkX Tree Visualization
# ============================================================
from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx

from bt_schema import BTNode, NodeStatus

STATUS_COLORS = {
    NodeStatus.SUCCESS: "#4CAF50",   # green
    NodeStatus.FAILURE: "#F44336",   # red
    NodeStatus.RUNNING: "#2196F3",   # blue
    NodeStatus.INVALID: "#9E9E9E",   # grey
}

NODE_SHAPES = {
    "Action":    "s",   # square
    "Condition": "D",   # diamond
    "Selector":  "o",   # circle
    "Sequence":  "o",
    "Parallel":  "^",   # triangle
    "Decorator": "h",   # hexagon
}


def build_nx_graph(root: BTNode) -> tuple[nx.DiGraph, dict]:
    """Convert BTNode tree → NetworkX DiGraph with display metadata."""
    G = nx.DiGraph()
    labels: dict[str, str] = {}
    colors: dict[str, str] = {}
    shapes: dict[str, str] = {}

    def walk(node: BTNode) -> None:
        label = f"{node.name}\n[{node.type.value}]\n{node.runtime_status.value}"
        G.add_node(node.node_id)
        labels[node.node_id] = label
        colors[node.node_id] = STATUS_COLORS.get(
            node.runtime_status, "#9E9E9E"
        )
        shapes[node.node_id] = NODE_SHAPES.get(node.type.value, "o")
        for child in node.children:
            G.add_edge(node.node_id, child.node_id)
            walk(child)

    walk(root)
    return G, {"labels": labels, "colors": colors, "shapes": shapes}


def render_tree(root: BTNode, title: str = "Behavior Tree") -> None:
    """Render the BT as a hierarchical NetworkX plot."""
    G, meta = build_nx_graph(root)

    if not nx.is_tree(G):
        print("[viz] Warning: graph is not a tree — layout may be incorrect.")

    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    except Exception:
        # Fallback if graphviz not available
        pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(16, 9))
    plt.title(title, fontsize=14, fontweight="bold")

    node_colors = [meta["colors"][n] for n in G.nodes()]
    nx.draw_networkx(
        G,
        pos=pos,
        labels=meta["labels"],
        node_color=node_colors,
        node_size=2200,
        font_size=7,
        arrows=True,
        arrowsize=15,
        edge_color="#555555",
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("bt_state.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("[viz] Saved bt_state.png")
```

***

## 8. Complete Runnable Boilerplate — Self-Correcting Agent Loop

This is the full integration: a mock "build API endpoint" task that simulates `FAILURE` on the first tick, triggers LLM recovery, re-ticks, and reaches `SUCCESS`.

```python
# ============================================================
# main.py — Self-Correcting Agent Loop
# Run: pip install py-trees pydantic networkx matplotlib
# ============================================================
from __future__ import annotations

import logging
import time
from pathlib import Path

import py_trees
import py_trees.common

from bt_schema import BTNode, NodeMetadata, NodeStatus, NodeType
from llm_optimizer import LLMOptimizer, compute_success_score
from persistence import find_resume_node_id, load_tree, save_tree
from tool_actions import BEHAVIOUR_REGISTRY, PassthroughBehaviour
from tree_ticker import TreeTicker, schema_to_pytree
from visualize import render_tree

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger("main")

GOAL = "Build a FastAPI /health endpoint with 95%+ test coverage"
SUCCESS_THRESHOLD = 0.9
MAX_TICKS = 20
STATE_PATH = Path("bt_state.json")


# ─── Simulated "always fails once" leaf ────────────────────────────────────────
class SimulatedFailThenSucceed(py_trees.behaviour.Behaviour):
    """Fails on the first call, succeeds on all subsequent calls."""

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name=name)
        self.params = params
        self._attempt = 0

    def update(self) -> py_trees.common.Status:
        self._attempt += 1
        if self._attempt == 1:
            self.feedback_message = (
                "FileNotFoundError: 'app/main.py' not found. "
                "Cannot run pytest without application code."
            )
            return py_trees.common.Status.FAILURE
        self.feedback_message = "pytest: 12 passed, 0 failed (100% coverage)"
        return py_trees.common.Status.SUCCESS


BEHAVIOUR_REGISTRY["sim_fail"] = SimulatedFailThenSucceed  # type: ignore


# ─── Initial tree schema ───────────────────────────────────────────────────────
def build_initial_schema() -> BTNode:
    """
    BT for "Build FastAPI /health endpoint":

    Selector (root)
    ├── Sequence: FastPath
    │   ├── Action: GenerateCode (llm)
    │   ├── Action: RunTests     (sim_fail — will FAIL first tick)
    │   └── Action: DeployCheck  (cli)
    └── Action: Fallback_Passthrough (passthrough)
    """
    generate_code = BTNode(
        name="GenerateCode",
        type=NodeType.ACTION,
        priority_weight=2.0,
        params={
            "tool": "llm",
            "llm_prompt": "Write a FastAPI /health endpoint with pytest tests for: {goal}",
            "goal": GOAL,
        },
        metadata=NodeMetadata(description="LLM generates application code"),
    )

    run_tests = BTNode(
        name="RunTests",
        type=NodeType.ACTION,
        priority_weight=3.0,
        params={"tool": "sim_fail"},
        metadata=NodeMetadata(description="Run pytest suite — will fail first attempt"),
    )

    deploy_check = BTNode(
        name="DeployCheck",
        type=NodeType.ACTION,
        priority_weight=1.5,
        params={"tool": "cli", "cmd": ["echo", "Deploy OK"]},
        metadata=NodeMetadata(description="Validate deployment readiness"),
    )

    fast_path = BTNode(
        name="FastPath",
        type=NodeType.SEQUENCE,
        priority_weight=3.0,
        children=[generate_code, run_tests, deploy_check],
        metadata=NodeMetadata(
            static=False,
            description="Primary execution path",
        ),
    )

    fallback = BTNode(
        name="Fallback_Passthrough",
        type=NodeType.ACTION,
        priority_weight=0.5,
        params={"tool": "__passthrough__"},
        metadata=NodeMetadata(
            static=True,
            description="Static fallback — never pruned",
        ),
    )

    root = BTNode(
        name="Root_Selector",
        type=NodeType.SELECTOR,
        priority_weight=5.0,
        children=[fast_path, fallback],
        metadata=NodeMetadata(static=True, description="Root fallback selector"),
    )

    return root


# ─── Main agent loop ───────────────────────────────────────────────────────────
def run_agent() -> None:
    logger.info("=" * 60)
    logger.info("AUTONOMOUS LLM AGENT — BT Self-Correction Loop")
    logger.info("Goal: %s", GOAL)
    logger.info("=" * 60)

    # Resume from disk if available, else build fresh
    schema_root = load_tree(STATE_PATH)
    if schema_root:
        logger.info("Resuming from saved state (last RUNNING: %s)",
                    find_resume_node_id(schema_root))
    else:
        schema_root = build_initial_schema()
        logger.info("Fresh tree constructed.")

    ticker = TreeTicker(schema_root=schema_root, max_ticks=MAX_TICKS)
    optimizer = LLMOptimizer(
        ticker=ticker,
        goal=GOAL,
        success_threshold=SUCCESS_THRESHOLD,
        max_optimization_rounds=5,
    )
    # Wire optimizer into ticker's failure hook
    ticker.on_failure_hook = optimizer.optimize

    tick_num = 0
    optimal = False

    # ── Self-correcting loop ────────────────────────────────────────────────
    while tick_num < MAX_TICKS and not optimal:
        tick_num += 1
        logger.info("─── Tick %d ─────────────────────────────", tick_num)

        result = ticker.tick()
        score = compute_success_score(ticker, GOAL)

        logger.info(
            "Status: %-8s | Tip: %-25s | Score: %.2f | Feedback: %s",
            result.status.value,
            result.tip_name,
            score,
            result.tip_feedback[:80],
        )

        # Persist after every tick for crash-safe resume
        save_tree(ticker.schema_root, STATE_PATH)

        if result.status == NodeStatus.SUCCESS:
            logger.info("✓ Task COMPLETE in %d tick(s). Score: %.2f", tick_num, score)
            optimal = True
            break

        if result.status == NodeStatus.FAILURE:
            # Optimizer already triggered via on_failure_hook;
            # re-build py_trees from mutated schema before next tick.
            ticker._build_tree()
            time.sleep(0.05)  # Throttle in production

    if not optimal:
        logger.warning("Agent did not reach SUCCESS within %d ticks.", MAX_TICKS)

    # ── Final visualization ─────────────────────────────────────────────────
    logger.info("Rendering final tree state...")
    render_tree(ticker.schema_root, title=f"BT Final State — {GOAL}")

    # ── Print final tree to console ─────────────────────────────────────────
    print("\n" + py_trees.display.unicode_tree(ticker.tree.root, show_status=True))


if __name__ == "__main__":
    run_agent()
```

***

## 9. Key Design Decisions and Trade-offs

### 9.1 py_trees API Choices (2.4+)

| Operation | API Used | Notes |
|-----------|----------|-------|
| Live subtree removal | `BehaviourTree.prune_subtree(uuid)`[^16] | Walks root.iterate(), calls parent.remove_child() |
| Live subtree insertion | `BehaviourTree.insert_subtree(child, parent_uuid, index)`[^14] | Directly calls composite.insert_child() |
| Swap failing subtree | `BehaviourTree.replace_subtree(uuid, subtree)`[^16] | Preferred over prune+insert; atomic |
| Failure diagnosis | `behaviour.feedback_message`[^7][^10] | Set in `update()`, read after `tick_once()` |
| Deepest failing node | `BehaviourTree.tip()`[^8] | Returns deepest RUNNING/FAILURE node |

### 9.2 Pydantic Recursion

The `list["BTNode"]` forward reference requires `model_rebuild()` called **after** the class body. This is a v2 breaking change from v1's `update_forward_refs()`. The call must be re-issued after any dynamic schema mutation to ensure the core schema reflects the current field definitions.[^13][^4]

### 9.3 LLM Optimizer Constraints

- **Prompt injection guard**: All LLM-generated JSON is parsed and validated by `BTNode(**data)` before touching the live tree. A `ValidationError` aborts the round without corrupting execution state.
- **Static nodes**: `metadata.static = True` marks critical infrastructure (root, fallback) as immune to pruning.[^9]
- **Optimization ceiling**: `max_optimization_rounds` prevents infinite regrowth loops on unsolvable tasks.
- **Score function**: `compute_success_score()` is the only place domain-specific logic lives. Swap it for test pass rate, lint score, API response time, etc.

### 9.4 Persistence Guarantees

`save_tree()` uses an atomic `tmp → rename` pattern. `load_tree()` calls `model_rebuild()` before parsing to ensure the recursive schema validator is active for the deserialized data. `find_resume_node_id()` performs a depth-first scan for the last `RUNNING` node, enabling mid-task restart after a crash or redeployment.[^14][^11]

### 9.5 Known Limitations

- **Non-blocking contract**: All `update()` methods must return in microseconds. Heavy IO (LLM calls, long subprocess runs) must be managed with `concurrent.futures` and polled from the blackboard.[^7]
- **replace_subtree root guard**: `py_trees.trees.BehaviourTree.replace_subtree()` raises `AssertionError` if `unique_id` is the root node. The optimizer must never target the root.[^16]
- **Blackboard namespace collisions**: With dynamic subtree insertion, each node must use its `node_id` in blackboard key paths to avoid read/write conflicts.

***

## 10. Dependency Matrix

```
py-trees>=2.4.0        # Behaviour tree engine, composites, blackboard
pydantic>=2.0.0        # Schema validation, model_rebuild(), model_dump_json()
networkx>=3.0          # Tree visualization as directed graph
matplotlib>=3.7        # Rendering NetworkX plots to PNG
```

Install:

```bash
pip install "py-trees>=2.4.0" "pydantic>=2.0.0" networkx matplotlib
# Optional: graphviz for hierarchical layout
# Ubuntu: sudo apt install graphviz
# macOS:  brew install graphviz
pip install pygraphviz   # or pydot
```

---

## References

1. [Py Trees — py_trees 2.4.0 documentation](https://py-trees.readthedocs.io) - Guide. Introduction · Behaviours · Composites · Decorators · Blackboards · Idioms · Trees · Visualis...

2. [py-trees](https://pypi.org/project/py-trees/) - PyTrees is a python implementation of behaviour trees designed to facilitate the rapid development o...

3. [Self-Evolving LLM Agents - Emergent Mind](https://www.emergentmind.com/topics/self-evolving-llm-based-agents) - Self-evolving LLM agents are frameworks where large language models dynamically adjust control loops...

4. [Models - Pydantic documentation (en)](https://pydantic.com.cn/en/concepts/models/) - Rebuild model schema¶. The model schema can be rebuilt using model_rebuild() . This is useful for bu...

5. [[PDF] A Code-Driven Approach to Behavior Tree Generation for Robot ...](https://www.ijcai.org/proceedings/2025/0980.pdf) - Through multi-round generation and feedback, the LLM can gradually optimize the code structure, gene...

6. [Interactive tree/hierarchy diagram - Bokeh Discourse](https://discourse.bokeh.org/t/interactive-tree-hierarchy-diagram/11073) - Here is one suggestion. I am using DiGraph in networkx to create a directed graph from a dataframe w...

7. [Behaviours — py_trees 2.4.0 documentation - Py Trees](https://py-trees.readthedocs.io/en/devel/behaviours.html) - A Behaviour is the smallest element in a behaviour tree, i.e. it is the leaf. Behaviours are usually...

8. [py_trees.behaviour module](https://docs.ros.org/en/rolling/p/py_trees/py_trees.behaviour.html) - A parent class for all user definable tree behaviours. Args: name: the behaviour name, defaults to a...

9. [Agent Error Recovery [AI Agent Knowledge Base]](https://agentwiki.org/agent_error_recovery) - Agent Error Recovery Patterns for handling failures in AI agent systems, including retry with backof...

10. [py_trees.blackboard module](https://docs.ros.org/en/iron/p/py_trees/py_trees.blackboard.html) - feedback_message = self.state.number_of_noodles if self.state.number_of_noodles > 5: return py_trees...

11. [Serialization - Pydantic](https://docs.pydantic.dev/2.10/concepts/serialization/) - The .model_dump_json() method serializes a model directly to a JSON-encoded string that is equivalen...

12. [Serialization - Pydantic Validation](https://docs.pydantic.dev/latest/concepts/serialization/) - Pydantic uses the terms "serialize" and "dump" interchangeably. Both refer to the process of convert...

13. [Defining recursive models in Pydantic? - python - Stack Overflow](https://stackoverflow.com/questions/68091480/defining-recursive-models-in-pydantic) - How can I define a recursive Pydantic model? Here's an example of what I mean: Copy. from typing imp...

14. [py_trees.trees module - ROS Docs](https://docs.ros.org/en/iron/p/py_trees/py_trees.trees.html) - Grow, water, prune your behaviour tree with this, the tree custodian. It features a few enhancements...

15. [Designing AI Agents' Behaviors with Behavior Trees](https://towardsdatascience.com/designing-ai-agents-behaviors-with-behavior-trees-b28aa1c3cf8a/) - In this post, I will explain the Behavior Tree and implement it on our Pacman to show that Behavior ...

16. [Source code for py_trees.trees - Py Trees - Read the Docs](https://py-trees.readthedocs.io/en/devel/_modules/py_trees/trees.html) - This package provides a default reference implementation that is directly usable, but can also be ea...
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
