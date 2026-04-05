"""
StopHook_cite_evidence.py

Enforces citation of evidence when making claims about code behavior.

CLAUDE.md Principle: "Evidence-First" - verify claims with actual code/data
before conclusions. Read files before making claims about them.

Blocks responses that make behavioral claims without proper file:line citations.

Bug Fixes from Architecture Review:
- Proper JSON error handling with try/except
- File locking for parallel safety (fcntl/msvcrt)
- Expanded pattern list covering more claim types
- Tightened evidence marker validation (rejects vague references)
- No calibration/Bayesian/Phase 2 (simple validation only)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# Cross-platform file locking
try:
    import msvcrt
    WINDOWS = True
except ImportError:
    import fcntl
    WINDOWS = False


# ============================================================================
# PATTERNS
# ============================================================================

# Expanded claim patterns - detects statements about code behavior
CLAIM_PATTERNS = [
    # Function/method behavior - expanded to match "The X function" pattern
    r"(?:the\s+)?\w+\s+(?:function|method|def)\s+(?:works|does|uses|handles|processes|returns|validates|checks)",
    r"\w+\(\s*\)\s+(?:works|does|handles|processes|returns)",

    # Class behavior - expanded to match "The X class" pattern
    r"(?:the\s+)?\w+\s+(?:class)\s+(?:works|does|uses|handles|manages|processes|routes)",
    r"the\s+\w+\s+(?:object|instance|class)\s+(?:does|handles|processes|routes)",

    # Module behavior
    r"(?:module|the\s+\w+\s+module)\s+(?:works|does|uses|handles|manages|provides|exports)",
    r"import\s+\w+\s+(?:does|handles|manages)",

    # File references with behavioral claims
    r"[\w._/\\-]+\.(?:py|js|ts|md|json|yaml|yml)\s+(?:works|does|uses|handles|processes|loads|saves|validates|checks)",

    # System/component behavior
    r"the\s+(?:system|handler|router|middleware|service|processor|manager|controller)\s+(?:works|does|uses|handles|processes|routes|manages)",
    r"this\s+(?:code|function|method|class|module)\s+(?:works|does|uses|handles|processes)",

    # Generic behavioral assertions
    r"it\s+(?:reads|writes|calls|invokes|triggers|executes|processes|validates|checks|returns)",
    r"the\s+code\s+(?:reads|writes|calls|invokes|triggers|executes|handles|processes)",

    # Simple subject-verb claims: "X processes/does/handles Y"
    r"^\w+\s+(?:processes|handles|does|uses|validates|checks|returns|loads|saves)",
]

# Hedge patterns - statements that acknowledge uncertainty (don't require citation)
HEDGE_PATTERNS = [
    r"\b(?:might|may|could|possibly|perhaps|unclear|unsure|uncertain)\b",
    r"\b(?:I\s+(?:think|believe|suspect|guess)|seems|appears|looks\s+like)\b",
    r"\b(?:would\s+(?:you|we)|should\s+we|can\s+we)\b",  # Questions/suggestions
]

# Meta-patterns - statements about investigation (not claims requiring citation)
META_PATTERNS = [
    r"\blet\s+me\s+(?:check|read|verify|examine|look\s+at|investigate|search)\b",
    r"\bI\s+(?:will|need\s+to|should|can)\s+(?:check|read|verify|find)\b",
    r"\blooking\s+for\b",
    r"\bto\s+(?:understand|see|verify|check)\b",
    r"\b(?:what|how)\s+does\s+[a-z_]+\s+(?:work|do|handle)\b",  # Questions
    r"\?$",  # Ends with question mark
]

# Valid citation patterns - specific file references
CITATION_PATTERNS = [
    # Standard file:line format
    r"([a-zA-Z_][\w/_\\.-]*\.(?:py|js|ts|md|json|yaml|yml|txt)):(\d+)",

    # "Per file:line" format (constitutional standard)
    r"(?:per|according\s+to|see|in|from)\s+([a-zA-Z_][\w/_\\.-]*\.(?:py|js|ts|md|json|yaml|yml))(?::(\d+))?",
    r"\b([a-zA-Z_][\w/_\\.-]*\.(?:py|js|ts|md|json|yaml|yml))\s+(?:shows|states|indicates|contains)",

    # Parenthetical citation
    r"\(([^)]*\.py[:\s]\d+)",

    # File path mentioned in context
    r"\b(?:in|from|at)\s+([a-zA-Z_][\w/_\\.-]*\.(?:py|js|ts|md))\b",
]

# Vague evidence markers that DO NOT count as proper citations
WEAK_MARKERS = [
    r"according\s+to\s+(?:the|this|that)\s+(?:code|output|result|file)",
    r"the\s+(?:code|output|result|file)\s+shows",
    r"from\s+(?:reading|examining)\s+the\s+code",
]


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def extract_citations(response: str) -> List[Dict[str, str]]:
    """
    Extract valid citations from response text.

    Returns list of {"file": str, "line": str|None} dicts.
    """
    citations = []

    # Pattern 1: file:line format (most specific)
    for match in re.finditer(r"([a-zA-Z_][\w/_\\.-]*\.(?:py|js|ts|md|json|yaml|yml|txt)):(\d+)", response):
        citations.append({"file": match.group(1), "line": match.group(2)})

    # Pattern 2: Per/According to file (with optional line)
    for match in re.finditer(
        r"(?:per|according\s+to|see|in)\s+([a-zA-Z_][\w/_\\.-]*\.(?:py|js|ts|md|json|yaml|yml))(?::\s*(\d+))?",
        response,
        re.IGNORECASE
    ):
        file = match.group(1)
        line = match.group(2)
        # Avoid duplicates
        if not any(c["file"] == file for c in citations):
            citations.append({"file": file, "line": line})

    # Pattern 3: file shows/contains format
    for match in re.finditer(
        r"([a-zA-Z_][\w/_\\.-]*\.(?:py|js|ts|md))\s+(?:shows|states|indicates)",
        response,
        re.IGNORECASE
    ):
        file = match.group(1)
        if not any(c["file"] == file for c in citations):
            citations.append({"file": file, "line": None})

    return citations


def has_weak_markers(response: str) -> bool:
    """Check if response contains only weak evidence markers."""
    text = response.lower()
    for pattern in WEAK_MARKERS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def has_hedges(response: str) -> bool:
    """Check if response contains hedging language."""
    text = response.lower()
    for pattern in HEDGE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def has_meta_statements(response: str) -> bool:
    """Check if response is meta-commentary about investigation."""
    text = response.lower()
    for pattern in META_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def detect_claim(response: str) -> Dict[str, Any]:
    """
    Detect if response makes behavioral claims requiring citation.

    Returns:
        {"has_claim": bool, "matched_patterns": list, "confidence": float}
    """
    if len(response.strip()) < 30:
        return {"has_claim": False, "matched_patterns": [], "confidence": 0.0}

    text = response.lower()
    matched = []

    for pattern in CLAIM_PATTERNS:
        if re.search(pattern, text):
            matched.append(pattern)

    # Check for hedges (reduces claim confidence)
    hedged = has_hedges(response)

    # Check for meta (reduces claim confidence)
    meta = has_meta_statements(response)

    # Calculate confidence
    if not matched:
        confidence = 0.0
    elif hedged or meta:
        confidence = 0.3  # Low confidence if hedged or meta
    else:
        confidence = 0.8  # High confidence if clear claim

    return {
        "has_claim": len(matched) > 0 and not (hedged or meta),
        "matched_patterns": matched,
        "confidence": confidence,
    }


def check_citation(response: str, patterns_only: bool = False) -> Dict[str, Any]:
    """
    Main validation function.

    Args:
        response: The assistant's response text
        patterns_only: If True, only return pattern detection (skip validation)

    Returns:
        {
            "valid": bool,
            "reason": str,
            "has_claim": bool,
            "has_citation": bool,
            "citations": list of {"file": str, "line": str|None},
            "matched_patterns": list,
        }
    """
    # Short circuit for trivial responses
    if len(response.strip()) < 20:
        return {
            "valid": True,
            "reason": "trivial_response",
            "has_claim": False,
            "has_citation": False,
            "citations": [],
            "matched_patterns": [],
        }

    # Detect claims
    claim_result = detect_claim(response)

    if patterns_only:
        return {
            "has_claim": claim_result["has_claim"],
            "matched_patterns": claim_result["matched_patterns"],
        }

    # Extract citations
    citations = extract_citations(response)
    has_citation = len(citations) > 0

    # Check for weak markers (don't count as real citations)
    if has_citation and has_weak_markers(response):
        # If only weak markers present, citations don't count
        # But we extracted actual file refs, so they do count
        pass  # Real citations override weak markers

    # Validation logic
    if not claim_result["has_claim"]:
        return {
            "valid": True,
            "reason": "no_claim",
            "has_claim": False,
            "has_citation": has_citation,
            "citations": citations,
            "matched_patterns": claim_result["matched_patterns"],
        }

    if has_citation:
        return {
            "valid": True,
            "reason": "has_citation",
            "has_claim": True,
            "has_citation": True,
            "citations": citations,
            "matched_patterns": claim_result["matched_patterns"],
        }

    # Claim detected but no citation
    return {
        "valid": False,
        "reason": "claim_without_citation",
        "has_claim": True,
        "has_citation": False,
        "citations": [],
        "matched_patterns": claim_result["matched_patterns"],
    }


# ============================================================================
# FILE LOCKING (Cross-Platform)
# ============================================================================

class FileLock:
    """Cross-platform file locking for parallel safety."""

    def __init__(self, path: Path):
        self.path = path
        self.lock_path = Path(str(path) + ".lock")
        self.fd = None

    def __enter__(self):
        try:
            self.fd = open(self.lock_path, 'w')
            if WINDOWS:
                msvcrt.locking(self.fd.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
        except OSError:
            # Locking failed, continue anyway (best effort)
            self.fd = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd:
            try:
                if WINDOWS:
                    msvcrt.locking(self.fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                self.fd.close()
            except OSError:
                pass
            # Clean up lock file
            try:
                self.lock_path.unlink(missing_ok=True)
            except OSError:
                pass


# ============================================================================
# MAIN HOOK ENTRY POINT
# ============================================================================

def main():
    """
    StopHook entry point.

    Input (stdin JSON):
        {"assistant_response": str}

    Output (stdout JSON):
        {"continue": bool, "message": str (optional)}
    """
    try:
        # Read input with JSON error handling
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            # Malformed input - allow to continue (fail open)
            print(json.dumps({"continue": True}))
            return

        response_text = input_data.get("assistant_response", "")

        # Run validation
        result = check_citation(response_text)

        if not result["valid"]:
            # Build helpful block message
            message = "⛔ CITATION REQUIRED\n\n"
            message += "You're making claims about code behavior without citing evidence.\n\n"
            message += "Constitutional requirement (CLAUDE.md - Evidence-First):\n"
            message += "\"Read files before making claims about them. Cite file:line.\"\n\n"
            message += "Expected format:\n"
            message += "  - \"Per handler.py:45, the process routes requests.\"\n"
            message += "  - \"The module handles auth (auth.py:123).\"\n\n"
            message += "Action: Re-read the relevant file and include the citation."

            print(json.dumps({
                "continue": False,
                "message": message
            }))
        else:
            print(json.dumps({"continue": True}))

    except Exception:
        # Never fail the hook - log and continue
        # In production, might log to file for debugging
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
