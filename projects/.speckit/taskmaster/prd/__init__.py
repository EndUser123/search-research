"""
PRD Parser Module for TaskMaster

Parses PRD.md files with FR-XXX/NF-XXX format requirements.

Includes:
- PRDParser: Parse individual PRD files
- PRDImporter: Import PRD requirements as TaskMaster tasks
- PRDRegistry: Lazy loading and caching for multiple PRDs
- CWO12 Integration: Auto-detect and import PRDs during workflow

Author: Claude Code
Version: 2.1.0
"""

from .cwo12_integration import (
    auto_import_prd,
    cwo12_check_and_import,
    detect_prd,
    get_prd_context,
    should_auto_import,
)
from .importer import (
    ImportResult,
    PRDImporter,
    get_prd_status,
    import_prd,
    list_prds,
)
from .parser import ParsedPRD, PRDParser, PRDRequirement, PRDValidationError
from .registry import (
    PRDCacheEntry,
    PRDRegistry,
    RegistryStats,
    create_registry,
)

__all__ = [
    # Parser
    'PRDParser',
    'PRDRequirement',
    'ParsedPRD',
    'PRDValidationError',
    # Importer
    'PRDImporter',
    'ImportResult',
    'import_prd',
    'get_prd_status',
    'list_prds',
    # CWO12 Integration
    'detect_prd',
    'should_auto_import',
    'auto_import_prd',
    'get_prd_context',
    'cwo12_check_and_import',
    # Registry
    'PRDRegistry',
    'PRDCacheEntry',
    'RegistryStats',
    'create_registry',
]
