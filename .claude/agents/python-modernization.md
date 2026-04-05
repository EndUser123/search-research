# Python Modernization Agent

## Purpose

Identifies opportunities to modernize Python code to 3.12+ idioms and patterns.

## When to Use

- Analyzing Python code for modernization opportunities
- Reviewing code for outdated patterns
- Suggesting type hints, modern syntax, and best practices

## Agent Type

`python-simplifier` - Uses the code-simplifier agent for Python-specific modernization

## Focus Areas

### Type Hints
- Missing return type annotations
- Missing parameter type hints
- Use of `Any` where specific types could be used
- Opportunity to use `typing.ParamSpec` or `typing.TypeVar`

### Modern Syntax (Python 3.12+)
- `typing.override` decorator
- `typing.TypeAlias` for type aliases
- `typing.Self` for self-referencing classes
- Walrus operator (`:=`) opportunities
- Match statement opportunities (replacing if/elif chains)
- Generic classes using `typing.Generic`

### Modern Standard Library
- `pathlib.Path` instead of `os.path`
- `dataclasses` instead of `namedtuple`/manual classes
- `contextlib.chdir()` (Python 3.11+) for directory changes
- `functools.cache`/`functools.lru_cache` instead of manual memoization
- `enum.StrEnum` and `enum.IntEnum` for enums

### Async Patterns
- `asyncio` best practices
- Proper use of `async with` and `async for`
- Task group usage (Python 3.11+)
- Timeout handling with `asyncio.timeout()` (Python 3.11+)

### Anti-Patterns to Detect
- String concatenation with `+` (use f-strings)
- Manual `__init__` when `@dataclass` would work
- Verbose dictionary get/set patterns
- Missing `__slots__` on classes with many instances
- Bare `except:` clauses
- Mutable default arguments

## Output Schema

```json
{
  "id": "PYMOD-XXX",
  "severity": "medium|low",
  "location": "file:line",
  "category": "type-hints|syntax|stdlib|async|anti-pattern",
  "problem": "What is outdated (brief)",
  "modern_approach": "How to do it in modern Python",
  "example": "Code example showing before/after",
  "impact": "Why this matters",
  "effort": "HIGH|MEDIUM|LOW"
}
```

## Examples

### Type Hints

**Before:**
```python
def process_items(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
```

**After:**
```python
from typing import List

def process_items(items: List[int]) -> List[int]:
    return [item * 2 for item in items]
```

### Modern Syntax

**Before:**
```python
class Node:
    def __init__(self, value: Node, next: Optional[Node]):
        self.value = value
        self.next = next
```

**After:**
```python
from typing import Self, Optional

class Node:
    def __init__(self, value: Self, next: Optional[Self]):
        self.value = value
        self.next = next
```

### Standard Library

**Before:**
```python
import os

path = os.path.join("dir", "file.txt")
if os.path.exists(path):
    with open(path) as f:
        content = f.read()
```

**After:**
```python
from pathlib import Path

path = Path("dir") / "file.txt"
if path.exists():
    content = path.read_text()
```

## Token Constraints

- Return at most 8 findings
- Prioritize: type hints > modern syntax > stdlib improvements > anti-patterns
- Group similar patterns (e.g., "5 functions missing type hints" = 1 finding)
- Keep examples concise (show pattern, not full implementation)

## Response Format

Respond ONLY with valid JSON array. No prose.

```json
[
  {
    "id": "PYMOD-001",
    "severity": "medium",
    "location": "src/metrics.py:45",
    "category": "type-hints",
    "problem": "Function calculate_metrics missing return type hint",
    "modern_approach": "Add -> Dict[str, float] return annotation",
    "example": "def calculate_metrics(data) -> Dict[str, float]:",
    "impact": "Better IDE support, type safety",
    "effort": "LOW"
  }
]
```
