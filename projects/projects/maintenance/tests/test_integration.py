#!/usr/bin/env python3
import sys

sys.path.insert(0, "__csf.wip/shared")

try:
    from utils.integration_workflow.auto_axiom_integration import (
        axiom_is_available,
        get_integration_status,
    )

    print("✅ Import successful")
    print(f"AXIOM available: {axiom_is_available()}")
    print(f"Integration status: {get_integration_status()}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
