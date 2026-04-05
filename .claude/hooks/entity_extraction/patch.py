"""
Integration patch for assumption_audit_v2.py

This module patches the entity extraction functions in assumption_audit_v2
to use the new tiered extraction system.

To enable: Set USE_NEW_ENTITY_EXTRACTION=true (default)
To disable: Set USE_NEW_ENTITY_EXTRACTION=false

The patch is applied at import time by importing this module.
"""

import os
import sys

# Feature flag
ENABLED = os.environ.get("USE_NEW_ENTITY_EXTRACTION", "true").lower() == "true"

def apply_patch():
    """
    Apply the entity extraction patch to assumption_audit_v2.
    
    This replaces the following functions:
    - extract_entities_from_text
    - extract_entities_from_claims  
    - extract_entities_from_evidence
    - check_entity_overlap
    """
    if not ENABLED:
        return False

    try:
        # Import the target module
        import assumption_audit_v2 as target

        # Import new implementations
        from entity_extraction.migrate import (
            check_entity_overlap,
            extract_entities_from_claims,
            extract_entities_from_evidence,
            extract_entities_from_text,
        )

        # Patch the functions
        target.extract_entities_from_text = extract_entities_from_text
        target.extract_entities_from_claims = extract_entities_from_claims
        target.extract_entities_from_evidence = extract_entities_from_evidence
        target.check_entity_overlap = check_entity_overlap

        # Log if debug enabled
        if os.environ.get("ENTITY_EXTRACTOR_DEBUG", "").lower() == "true":
            print("[entity_extraction] Patch applied to assumption_audit_v2", file=sys.stderr)

        return True

    except ImportError as e:
        print(f"[entity_extraction] Patch failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[entity_extraction] Patch error: {e}", file=sys.stderr)
        return False


# Auto-apply on import
_patched = apply_patch()

def is_patched() -> bool:
    """Check if patch was successfully applied."""
    return _patched
