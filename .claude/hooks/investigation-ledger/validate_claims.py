"""
Claim Validator - Hardened Implementation
Blocks claims about topics not in the investigation ledger.

Addresses critique concerns:
- Expanded pattern list (not just 3 patterns)
- Tightened evidence marker validation (rejects "according to my dreams")
- Validates evidence markers reference actual investigated files
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Import ledger (same directory)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger import get_files_read, get_investigated_topics, get_investigation_stats

# === Claim Detection Patterns ===
# Expanded from critique's "only 3 patterns"

CLAIM_PATTERNS = [
    # System/architecture explanations
    r"(?:the|this)\s+(?:system|code|module|function|class|method)\s+(?:works|does|uses|handles|processes|manages|validates|checks|verifies|creates|generates)",
    r"(?:the|this)\s+\w+\s+(?:system|handler|module|manager|service|controller)\s+(?:works|does|handles|dispatches|validates|creates|processes)",

    # Behavioral claims
    r"(?:it|this|the \w+)\s+(?:reads|writes|calls|invokes|dispatches|triggers|emits|sends|receives)",
    r"(?:when|if)\s+(?:called|invoked|triggered),?\s+(?:it|this|the)",

    # Causal explanations
    r"(?:because|since|as)\s+(?:the|it)\s+(?:is|does|has|uses|calls)",
    r"(?:this|that)\s+(?:is why|explains why|causes)",

    # Implementation claims
    r"(?:the|this)\s+(?:implementation|logic|algorithm|approach)\s+(?:is|does|works|handles)",
    r"(?:internally|under the hood),?\s+(?:it|this|the)",

    # Data flow claims
    r"(?:data|requests?|events?|messages?)\s+(?:flows?|passes?|moves?|goes?)\s+(?:through|to|from|into)",
    r"(?:the|this)\s+(?:flow|pipeline|chain|sequence)\s+(?:is|goes|starts|begins)",

    # State/behavior claims
    r"(?:the|this)\s+(?:state|status|flag|variable)\s+(?:is set|gets set|becomes|changes)",
    r"(?:it|this)\s+(?:maintains|tracks|stores|keeps)\s+(?:the|a)",
]

# Compiled for performance
CLAIM_REGEX = [re.compile(p, re.IGNORECASE) for p in CLAIM_PATTERNS]


# === Evidence Marker Patterns ===
# Tightened: must reference actual file paths, not vague claims

VALID_EVIDENCE_PATTERNS = [
    # File:line references (strongest)
    r"(?:in|at|from|see)\s+[`'\"]?([a-zA-Z0-9_\-./\\]+\.(py|js|ts|md|json|yaml|yml|toml|cfg|ini|txt))[`'\"]?\s*(?::|,\s*)?(?:lines?\s*)?(\d+)?",

    # Explicit file references
    r"(?:reading|examining|looking at|checking|from)\s+[`'\"]?([a-zA-Z0-9_\-./\\]+\.(py|js|ts|md|json|yaml|yml))[`'\"]?",

    # Output/result references (requires execution)
    r"(?:the|this)\s+(?:output|result|error|log|trace)\s+(?:shows|indicates|says|reads)",

    # Grep/search result references
    r"(?:grep|search|find)\s+(?:shows|found|returns|reveals)",
]

EVIDENCE_REGEX = [re.compile(p, re.IGNORECASE) for p in VALID_EVIDENCE_PATTERNS]

# Reject these fake evidence patterns
FAKE_EVIDENCE_PATTERNS = [
    r"according to (?:my|the|common|general)",
    r"(?:i|we)\s+(?:believe|think|assume|expect)",
    r"(?:typically|usually|generally|normally),?\s+(?:it|this|the)",
    r"based on (?:my|experience|knowledge|understanding)",
    r"(?:it|this)\s+(?:should|would|could|might)\s+(?:be|work|do)",
]

FAKE_EVIDENCE_REGEX = [re.compile(p, re.IGNORECASE) for p in FAKE_EVIDENCE_PATTERNS]


def _contains_claims(text: str) -> List[str]:
    """
    Detect claim patterns in text.
    Returns list of matched claim snippets.
    """
    matches = []
    for regex in CLAIM_REGEX:
        for match in regex.finditer(text):
            # Get surrounding context
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            matches.append(text[start:end].strip())
    return matches


def _has_valid_evidence(text: str, investigated_files: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Check if text has valid evidence markers that reference investigated files.
    
    Returns:
        (is_valid, reason)
    """
    # First check for fake evidence patterns
    for regex in FAKE_EVIDENCE_REGEX:
        if regex.search(text):
            return (False, "Contains speculation markers, not evidence")

    # Look for valid evidence patterns
    for regex in EVIDENCE_REGEX:
        match = regex.search(text)
        if match:
            # Extract referenced file if present
            groups = match.groups()
            if groups and groups[0]:
                referenced_file = groups[0]
                # Check if this file was actually investigated
                for investigated in investigated_files:
                    if referenced_file in investigated or investigated.endswith(referenced_file):
                        return (True, f"References investigated file: {referenced_file}")
                # File referenced but not investigated
                return (False, f"References uninvestigated file: {referenced_file}")
            else:
                # Output/result reference - check if we have executions
                return (True, "References execution output")

    return (False, "No valid evidence markers found")


def _extract_referenced_topics(text: str) -> Set[str]:
    """
    Extract topics that the response is making claims about.
    """
    topics = set()

    # Look for specific file/module/class references
    file_pattern = r"[`'\"]?([a-zA-Z][a-zA-Z0-9_\-]+)\.(py|js|ts|md)[`'\"]?"
    for match in re.finditer(file_pattern, text, re.IGNORECASE):
        topics.add(match.group(1).lower())

    # Look for module/class/function names in claims
    name_pattern = r"(?:the|this)\s+[`'\"]?([A-Z][a-zA-Z0-9_]+)[`'\"]?\s+(?:class|module|function|method|handler|system)"
    for match in re.finditer(name_pattern, text):
        topics.add(match.group(1).lower())

    # Look for quoted identifiers
    quoted_pattern = r"[`'\"]([a-zA-Z][a-zA-Z0-9_\-]{2,})[`'\"]"
    for match in re.finditer(quoted_pattern, text):
        name = match.group(1).lower()
        if len(name) >= 3 and not name.startswith(('http', 'www')):
            topics.add(name)

    return topics


def _normalize_topics_for_comparison(topics: Set[str]) -> Set[str]:
    """Normalize referenced topics to match ledger tokenization.

    Keep compound identifiers intact by default.
    Splitting `skill_registry` into `skill` and `registry` caused high
    false-positive rates when generic sub-tokens were treated as claims.
    """
    normalized = set()
    noise = {
        "src", "lib", "test", "tests", "spec", "specs", "tmp", "temp",
        "the", "and", "for", "with", "from", "this", "that", "py", "js",
        "ts", "md", "json", "yaml", "yml", "txt", "log", "cfg", "ini",
    }
    for topic in topics:
        token = topic.lower().strip()
        if len(token) < 3:
            continue
        if token in noise:
            continue
        # Keep alnum/underscore/hyphen compounds as one token.
        if re.fullmatch(r"[a-z0-9][a-z0-9_-]*", token):
            normalized.add(token)
    return normalized


def validate_claims(response_text: str) -> Dict:
    """
    Validate that claims in the response are substantiated by investigation.
    
    Returns:
        {"valid": bool, "message": str|None, "details": dict}
    """
    # Skip very short responses (greetings, acknowledgments)
    if len(response_text) < 100:
        return {
            "valid": True,
            "message": None,
            "details": {"reason": "Short response (< 100 chars)"}
        }

    # Skip responses that are clearly questions or requests
    if response_text.strip().endswith('?'):
        return {
            "valid": True,
            "message": None,
            "details": {"reason": "Response is a question"}
        }

    # Detect claims
    claims_found = _contains_claims(response_text)
    if not claims_found:
        return {
            "valid": True,
            "message": None,
            "details": {"reason": "No claim patterns detected"}
        }

    # Get investigation state
    investigated_topics = get_investigated_topics()
    investigated_files = get_files_read()
    stats = get_investigation_stats()

    # If nothing investigated yet, but claims present
    if stats["files_read"] == 0 and stats["searches"] == 0:
        # Check for valid evidence markers (might be referencing execution output)
        has_evidence, evidence_reason = _has_valid_evidence(response_text, investigated_files)

        if not has_evidence:
            return {
                "valid": False,
                "message": "⛔ CLAIM WITHOUT INVESTIGATION\n\nYou're making claims about system behavior but haven't read any files.\n\nRead the relevant files first, then explain.",
                "details": {
                    "claims_found": claims_found[:3],
                    "investigation_stats": stats,
                    "evidence_check": evidence_reason
                }
            }

    # Check for valid evidence markers
    has_evidence, evidence_reason = _has_valid_evidence(response_text, investigated_files)
    if has_evidence:
        return {
            "valid": True,
            "message": None,
            "details": {"reason": evidence_reason}
        }

    # Extract topics referenced in claims
    referenced_topics = _extract_referenced_topics(response_text)

    if referenced_topics:
        comparable_topics = _normalize_topics_for_comparison(referenced_topics)
        if not comparable_topics:
            return {
                "valid": True,
                "message": None,
                "details": {"reason": "No comparable topic tokens after normalization"},
            }

        # Check for topic mismatch
        unsubstantiated = comparable_topics - investigated_topics

        if unsubstantiated and len(unsubstantiated) > len(comparable_topics) * 0.5:
            # More than half of referenced topics are uninvestigated
            return {
                "valid": False,
                "message": f"⛔ UNSUBSTANTIATED CLAIMS\n\nYou're making claims about: {', '.join(sorted(unsubstantiated)[:5])}\n\nBut you've only investigated: {', '.join(sorted(investigated_topics)[:5]) or '(nothing)'}\n\nRead the relevant files first.",
                "details": {
                    "referenced_topics": list(referenced_topics),
                    "comparable_topics": list(comparable_topics),
                    "investigated_topics": list(investigated_topics),
                    "unsubstantiated": list(unsubstantiated),
                    "investigation_stats": stats
                }
            }

    # Claims present, some investigation done, no strong mismatch
    return {
        "valid": True,
        "message": None,
        "details": {
            "reason": "Claims present with sufficient investigation",
            "investigation_stats": stats
        }
    }


# === CLI for testing ===

if __name__ == "__main__":
    # Test mode: validate text from stdin or argument
    if len(sys.argv) > 1:
        test_text = " ".join(sys.argv[1:])
    else:
        test_text = sys.stdin.read()

    result = validate_claims(test_text)
    print(json.dumps(result, indent=2))
