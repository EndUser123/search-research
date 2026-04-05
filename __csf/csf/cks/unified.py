# Stub module to redirect cks.unified imports to the archived CKS location.
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# Navigate from csf/cks/unified.py -> csf -> P:/__csf
_csf_root = Path(__file__).parent.parent.parent

# Add the archive path where CKS actually lives
_archive_root = _csf_root / ".archive" / "src_archived_20260325"
_archive_unified_path = _archive_root / "cks" / "unified.py"

if str(_archive_root) not in sys.path:
    sys.path.insert(0, str(_archive_root))

# Load the archived module directly by file path to avoid circular import
_spec = spec_from_file_location("cks.unified", _archive_unified_path)
_archived_unified = module_from_spec(_spec)
_spec.loader.exec_module(_archived_unified)

CKS = _archived_unified.CKS
VALID_ENTRY_TYPES = _archived_unified.VALID_ENTRY_TYPES

__all__ = ["CKS", "VALID_ENTRY_TYPES"]
