# Stub package to redirect csf imports to src
import sys
from pathlib import Path

# Add parent directory to sys.path FIRST, before any imports
_csf_root = Path(__file__).parent.parent
if str(_csf_root) not in sys.path:
    sys.path.insert(0, str(_csf_root))

# Now import and expose cks submodule
from . import cks  # noqa: F401

__all__ = ['cks']
