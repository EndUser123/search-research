#!/usr/bin/env python3
"""
Stop Hook: Verify claims against evidence before allowing session to stop.
This is the main verification gate that decides to block or allow.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_lib import (
    calculate_semantic_similarity,
    get_claims,
    get_evidence,
    insert_violation,
    load_audit_config,
)


def run_theater_detection(claim_text: str, evidence_list: list) -> dict:
    """
    Signal 1: Theater Detection
    Detects success claims without diagnostic evidence.
    """
    success_keywords = ["pass", "passed", "passing", "fixed", "working",
                       "verified", "confirmed", "resolved", "completed", "ready"]

    is_success_claim = any(
        kw in claim_text.lower()
        for kw in success_keywords
    )

    if not is_success_claim:
        return {"detected": False, "score": 1.0}

    # Count evidence types
    diagnostic_count = sum(1 for e in evidence_list if e["category"] == "diagnostic")
    trivial_count = sum(1 for e in evidence_list if e["category"] == "trivial")
    other_count = sum(1 for e in evidence_list if e["category"] == "other")

    # Theater: success claim with only trivial commands
    if diagnostic_count == 0 and trivial_count > 0:
        return {
            "detected": True,
            "score": 0.0,
            "reason": f"Success claim with only {trivial_count} trivial commands (no diagnostic tools)",
            "diagnostics": {
                "diagnostic_count": diagnostic_count,
                "trivial_count": trivial_count,
                "other_count": other_count,
            }
        }

    return {"detected": False, "score": 1.0}

def run_semantic_matching(claim_text: str, evidence_list: list) -> dict:
    """
    Signal 3: Semantic Matching
    Uses embeddings to match claims against evidence.
    """
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return {
            "score": 0.5,
            "reason": "Semantic model not available",
            "evidence_count": len(evidence_list)
        }

    # Get diagnostic evidence
    diagnostic_evidence = [e for e in evidence_list if e["category"] == "diagnostic"]

    if not diagnostic_evidence:
        return {
            "score": 0.0,
            "reason": "No diagnostic evidence available",
            "evidence_count": 0
        }

    try:
        # Load model (will cache after first load)
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Encode claim
        claim_embedding = model.encode(claim_text, convert_to_numpy=True)

        # Collect evidence text
        evidence_texts = []
        for evidence in diagnostic_evidence:
            if evidence.get("tool_name") == "Bash":
                evidence_texts.append(evidence.get("command", ""))
            elif evidence.get("tool_name") == "Read":
                # For read tools, use file path as proxy
                evidence_texts.append(evidence.get("command", ""))
            else:
                evidence_texts.append(str(evidence.get("tool_response", ""))[:200])

        if not evidence_texts:
            return {"score": 0.0, "reason": "No evidence text to match"}

        # Encode evidence (combine all)
        combined_evidence = " ".join(evidence_texts)
        evidence_embedding = model.encode(combined_evidence, convert_to_numpy=True)

        # Calculate similarity
        similarity = calculate_semantic_similarity(claim_embedding, evidence_embedding)

        return {
            "score": max(0.0, min(1.0, similarity)),
            "evidence_count": len(diagnostic_evidence),
            "evidence_combined": combined_evidence[:200],
        }

    except Exception as e:
        return {
            "score": 0.5,
            "reason": f"Semantic matching error: {str(e)}",
            "evidence_count": len(diagnostic_evidence)
        }

def run_evidence_window_check(claim_dict: dict, evidence_list: list,
                             window_minutes: int = 10) -> dict:
    """
    Signal 2 & 4: Evidence Window + Freshness
    Checks if evidence is recent and not invalidated by state changes.
    """
    claim_time = datetime.fromisoformat(claim_dict.get("timestamp", datetime.now().isoformat()))

    # Get evidence within window AFTER claim was made
    recent_evidence = [
        e for e in evidence_list
        if datetime.fromisoformat(e.get("timestamp", "2000-01-01T00:00:00")) >= claim_time
        and (datetime.fromisoformat(e.get("timestamp", "")) - claim_time).total_seconds() <= window_minutes * 60
    ]

    if not recent_evidence:
        return {
            "score": 0.0,
            "reason": f"No evidence within {window_minutes} minute window after claim",
            "window_minutes": window_minutes,
            "evidence_found_before_claim": len([e for e in evidence_list if
                datetime.fromisoformat(e.get("timestamp", "")) < claim_time])
        }

    # Get most recent diagnostic evidence
    diagnostic_evidence = [e for e in recent_evidence if e["category"] == "diagnostic"]

    if diagnostic_evidence:
        freshest = max(
            [datetime.fromisoformat(e.get("timestamp", "2000-01-01T00:00:00"))
             for e in diagnostic_evidence],
            default=datetime.now()
        )
        time_delta = freshest - claim_time
        recency_minutes = time_delta.total_seconds() / 60
        recency_score = max(0.0, 1.0 - (recency_minutes / window_minutes))

        return {
            "score": recency_score,
            "reason": f"Evidence {recency_minutes:.1f} min after claim (window {window_minutes} min)",
            "freshest_evidence_minutes_after_claim": recency_minutes,
            "diagnostic_evidence_count": len(diagnostic_evidence),
        }

    return {
        "score": 0.5,
        "reason": "Only non-diagnostic evidence found",
        "evidence_count": len(recent_evidence)
    }

def run_claim_specificity_check(claim_text: str) -> dict:
    """
    Signal 5: Claim Specificity
    Specific claims (file paths, function names) are higher risk.
    """
    specificity_indicators = [
        "/" in claim_text,  # File path
        "." in claim_text and ".py" not in claim_text,  # Dotted name
        "::" in claim_text,  # C++ namespace
        claim_text[0].isupper(),  # Starts with capital (class name)
    ]

    is_specific = sum(specificity_indicators) >= 2
    specificity_risk = 0.7 if is_specific else 0.3

    # Higher specificity = higher risk = lower score
    specificity_score = 1.0 - specificity_risk

    return {
        "score": specificity_score,
        "is_specific": is_specific,
        "specificity_risk": specificity_risk,
        "indicators": sum(specificity_indicators)
    }

def calculate_final_score(signals: dict, config: dict) -> dict:
    """
    Combine all signals into a final verification score.
    """
    semantic_weight = config.get("semantic_weight", 0.4)
    freshness_weight = config.get("freshness_weight", 0.3)
    specificity_weight = config.get("specificity_weight", 0.3)

    # Extract signal scores
    theater_score = 0.0 if signals["theater"].get("detected") else 1.0
    semantic_score = signals["semantic"].get("score", 0.5)
    freshness_score = signals["freshness"].get("score", 0.0)
    specificity_score = signals["specificity"].get("score", 0.5)

    # Theater is binary - if detected, immediate fail
    if signals["theater"].get("detected"):
        return {
            "final_score": 0.0,
            "reason": "Theater detection triggered",
            "components": {
                "theater": 0.0,
                "weighted_score": 0.0,
            }
        }

    # Combine signals
    weighted_score = (
        semantic_score * semantic_weight +
        freshness_score * freshness_weight +
        specificity_score * specificity_weight
    )

    return {
        "final_score": weighted_score,
        "components": {
            "semantic": semantic_score,
            "freshness": freshness_score,
            "specificity": specificity_score,
            "weighted_score": weighted_score,
        }
    }

@hook_main
def main():
    # Read hook input
    hook_input = json.loads(sys.stdin.read())

    # Load config
    config = load_audit_config()

    if not config.get("enabled", True):
        sys.exit(0)  # Allow stop if disabled

    session_id = hook_input.get("session_id", "unknown")

    # Load session data
    claims = get_claims(session_id)
    evidence = get_evidence(session_id)

    if not claims:
        # No claims extracted - allow stop
        sys.exit(0)

    violations = []

    # Verify each claim
    for claim_dict in claims:
        claim_text = claim_dict.get("claim_text", "")

        # Run all signals
        signals = {
            "theater": run_theater_detection(claim_text, evidence),
            "semantic": run_semantic_matching(claim_text, evidence),
            "freshness": run_evidence_window_check(claim_dict, evidence,
                config.get("evidence_window_minutes", 10)),
            "specificity": run_claim_specificity_check(claim_text),
        }

        # Calculate final score
        final_result = calculate_final_score(signals, config)
        final_score = final_result.get("final_score", 0.5)
        threshold = config.get("min_score_threshold", 0.5)

        # Check if violation
        if final_score < threshold:
            violation = {
                "type": "claim_unverified",
                "claim": claim_text,
                "reason": final_result.get("reason", "Score below threshold"),
                "signals": signals,
                "final_score": final_score,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat(),
            }

            violations.append(violation)
            insert_violation(session_id, violation)

    # Decision
    if violations and config.get("block_on_violations", True):
        output = {
            "decision": "block",
            "reason": f"Assumption audit: {len(violations)} unverified claim(s) detected",
            "violations": [
                {
                    "claim": v["claim"],
                    "reason": v["reason"],
                    "final_score": v["final_score"],
                    "threshold": v["threshold"],
                    "signals": {
                        "theater": {
                            "detected": v["signals"]["theater"].get("detected", False),
                            "reason": v["signals"]["theater"].get("reason", ""),
                        },
                        "semantic_score": round(v["signals"]["semantic"].get("score", 0), 3),
                        "freshness_score": round(v["signals"]["freshness"].get("score", 0), 3),
                        "specificity_score": round(v["signals"]["specificity"].get("score", 0), 3),
                    }
                }
                for v in violations
            ]
        }
        print(json.dumps(output, indent=2))
        sys.exit(2)  # Block
    else:
        # Allow stop
        sys.exit(0)

if __name__ == "__main__":
    main()
