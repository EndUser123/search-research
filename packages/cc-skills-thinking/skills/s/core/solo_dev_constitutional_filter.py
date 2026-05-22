"""Solo Dev Constitutional Filter — stubs the constitutional-checking interface.

The actual constitutional filter logic lives in __csf (Constitutional Safety Framework).
This stub exists solely to satisfy the import contract in run_heavy.py when the
__csf package is not available. It permits all ideas through.

Real implementation: check_action_item() evaluates whether an idea violates
solo-dev constitutional constraints (e.g., autonomous background services,
LLM-generated code without human director guardrails, etc.).
"""

from dataclasses import dataclass


@dataclass
class ConstitutionalVerdict:
    violates_constitution: bool
    reason: str | None = None
    alternative: str | None = None


class SoloDevConstitutionalFilter:
    """No-op constitutional filter — all ideas pass."""

    def check_action_item(self, content: str) -> ConstitutionalVerdict:
        return ConstitutionalVerdict(violates_constitution=False)