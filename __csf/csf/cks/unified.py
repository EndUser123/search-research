# Redirect cks.unified imports to the actual CKS implementation.
import sys
from pathlib import Path

# Navigate from csf/cks/unified.py -> csf -> P:/__csf -> marketplace search-research/core
_packages_root = (
    Path(__file__).parent.parent.parent.parent
    / "packages"
    / ".claude-marketplace"
    / "plugins"
    / "search-research"
    / "core"
)

if str(_packages_root) not in sys.path:
    sys.path.insert(0, str(_packages_root))

# Import from the actual CKS implementation
from cks.unified import CKS, VALID_ENTRY_TYPES

__all__ = ["CKS", "VALID_ENTRY_TYPES"]
