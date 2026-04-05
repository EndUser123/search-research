# Evidence Validation System Refactor

**Date:** 2025-02-09
**Template:** Python
**Intent:** IMPROVE_SYSTEM - Refactor evidence validation architecture

## Decision

Refactor to a **layered evidence validation system** that treats hash-verified content validity as sufficient, with workflow tracking only when content changes.

## Rationale

1. **Separation of concerns** - Content validity (hash) is orthogonal to workflow causality (receipts). Current system conflates them.
2. **Reduced ceremony** - When file hasn't changed, requiring fresh observation is wasteful (no new information gained).
3. **Python 3.12+ patterns** - Use `dataclasses`, `TypeDict`, and `functools.lru_cache` instead of manual JSON serialization.
4. **Research-backed** - [LabChain (2026)](https://www.sciencedirect.com/science/article/pii/S2352711026000373) demonstrates hash-based caching architecture for reproducible workflows.

## Current Architecture Problems

The evidence validation system has **multiple orthogonal mechanisms** that are conflated:

| Mechanism | File | Purpose | Current Problem |
|-----------|------|---------|-----------------|
| **File hash cache** | `empirical_claims_gate.py:861-881` | Content validity (file unchanged?) | Works correctly, but ignored post-block |
| **Observation receipts** | `Stop_router.py:640-704` | "Tool was used this turn" | Required even when hash is valid |
| **Evidence tokens** | `Stop_router.py:725-897` | One-time use, state tracking | Disqualified if reused |
| **Observation signature** | `Stop_router.py:531-545` | MD5 of {tool, path, command} | Compared against block-time signature |
| **Freshness token** | `Stop_router.py:552-588` | `tool_use_id` + timestamps | Proves NEW observation |
| **Structured fields** | `Stop_router.py:96` | `observed_via`, `observed_at`, `evidence_type` | Required in response text |

**The architectural flaw:** These serve **two different purposes** but are treated as equivalent:

1. **Content validity** (hash cache) - "Has this file changed?"
2. **Workflow causality** (receipts/tokens) - "Did you observe THIS turn?"

## Proposed Architecture

```python
# Unified evidence contract
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

@dataclass(frozen=True)
class EvidenceValidity:
    """Result of evidence validation check"""
    is_valid: bool
    source: Literal["hash_verified", "fresh_observation", "none"]
    cached_hash: str | None
    observation_age_seconds: float | None

class EvidenceValidator:
    """Unified evidence validation"""

    @lru_cache(maxsize=1024)
    def _file_hash(self, path: Path) -> str:
        """Cached file hash computation"""
        # ... hashlib.sha256 implementation

    def validate_claim_evidence(
        self,
        claimed_paths: set[Path],
        observation_receipt: dict | None,
        post_block_required: bool = False
    ) -> EvidenceValidity:
        """
        Unified validation:
        1. Check hash cache for claimed paths
        2. If hash matches and within TTL → VALID
        3. If post_block_required and no hash match → require fresh observation
        4. Otherwise, accept observation receipt if available
        """
```

## Implementation Steps

1. Create `evidence/__package__` with:
   - `validator.py` - Unified `EvidenceValidator` class
   - `cache.py` - LRU-cache backed file hash storage
   - `receipt.py` - Type-safe observation receipts
   - `migrate.py` - JSON → new format migration

2. Refactor `Stop_router.py`:
   - Replace `_post_block_requirement_violation()` to call `EvidenceValidator`
   - Accept hash-verified evidence as satisfying post-block requirement

3. Refactor `empirical_claims_gate.py`:
   - Use shared `EvidenceValidator` instead of local hash cache
   - Remove duplicate hash computation

## Alternatives Considered

| Alternative | Trade-off | Not Chosen Because |
|-------------|-----------|-------------------|
| **Status quo** - Keep current system | Zero transition cost | User identified genuine inefficiency |
| **Remove hash cache entirely** | Simpler code | Loses content validity optimization |
| **Async rewrite** | Future-proof | High complexity for solo dev context |
| **SQLite for all evidence** | Type-safe, ACID | Over-engineering for JSON-based hooks |

## Risk

- **Transition complexity** - 6+ files reference current APIs
- **State migration** - Existing JSON state files need migration path
- **Hook coordination** - `empirical_claims_gate.py` and `Stop_router.py` must agree on evidence contracts
- **Testing gap** - Current tests may assume redundant observation requirements

## Confidence

75% - Evidence from codebase analysis and user's valid critique. Not 100% because transition details need verification.

## Adversarial Self-Review

**Weakest assumption:** That hash-verified evidence can fully substitute for "fresh observation" post-block.

**Consequence if wrong:** Some edge case where content unchanged but context requires re-verification (e.g., environment state changed, not file state).

**Mitigation:** Keep workflow tracking for non-file evidence types (Bash execution, git state).

## Sources

- [LabChain: Enabling reproducible and modular scientific workflows (2026)](https://www.sciencedirect.com/science/article/pii/S2352711026000373)
- [Advanced Caching Strategies for Python LLM Applications (2023)](https://python.useinstructor.com/blog/2023/11/26/python-caching-llm-optimization/)
