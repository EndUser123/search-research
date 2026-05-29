"""Local search backends for code, documentation, and knowledge systems.

This module provides search backends that operate on local data sources:
- Code Documentation Search (CDS): AST-based docstring search
- Code Pattern Search (Grep): AST-based function/class name search
- Multi-Language Code Backend: Tree-sitter based multi-language code search
- Skills Backend: Progressive disclosure for Claude Code skills
- CHS Incremental: Incremental FAISS index updates
- CKS Metadata: Structured metadata queries for knowledge system
- KG Backend: Knowledge graph entity search
- RLM Backend: Template-based code generation search
- Claude History Backend: Fast keyword search for Claude Code chat history
- QMD Wiki Backend: Obsidian vault search via qmd CLI
- yt-is Backend: YouTube transcript FTS search via SQLite FTS5
"""

from .cds_backend import CDSBackend
from .chs_incremental import IncrementalIndexUpdater
from .cks_metadata_backend import (
    BACKEND_CKS_METADATA,
    CKSMetadataBackend,
    create_cks_metadata_backend,
)
from .claude_history_backend import (
    BACKEND_CLAUDE_HISTORY,
    ClaudeHistoryBackend,
    create_claude_history_backend,
)
from .enhanced_cds_backend import EnhancedCDSBackend
from .grep_backend import GrepBackend
from .kg_backend import BACKEND_KG, KGBackend
from .multilang_backend import (
    BACKEND_MULTILANG,
    SOURCE_RELIABILITY_MULTILANG,
    MultiLangCodeBackend,
    create_multilang_backend,
)
from .notebooklm_backend import (
    BACKEND_NOTEBOOKLM,
    NotebookLMBackend,
    create_notebooklm_backend,
)
from .rlm_backend import (
    BACKEND_RLM,
    RLMBackend,
    create_rlm_backend,
    is_rlm_available,
)
from .skills_backend import BACKEND_SKILLS, SkillsBackend
from .ast_code_backend import ASTCodeBackend, create_ast_backend, BACKEND_AST_CODE
from .call_graph_backend import CallGraphBackend, BACKEND_NAME_CALL_GRAPH
from .cpg_backend import CPGBackend, CPG_AVAILABLE
from .hdma_backend import HDMABackend, HDMA_AVAILABLE
from .lsp_backend import LSPSymbolBackend, create_lsp_backend, BACKEND_LSP_SYMBOL
from .dependency_backend import DependencyBackend, DEP_GRAPH_AVAILABLE
from .qmd_wiki_backend import QMDWikiBackend
from .yt_is_backend import YtIsBackend
from .vault_backend import (
    BACKEND_VAULT,
    VaultBackend,
    create_vault_backend,
)

BACKEND_QMD_WIKI = "QMD_WIKI"
BACKEND_YT_IS = "yt-is"

__all__ = [
    # Core backends
    "CDSBackend",
    "EnhancedCDSBackend",
    "GrepBackend",
    "MultiLangCodeBackend",
    "SkillsBackend",
    "IncrementalIndexUpdater",
    "CKSMetadataBackend",
    "KGBackend",
    "RLMBackend",
    "ClaudeHistoryBackend",
    "NotebookLMBackend",
    "VaultBackend",
    # Extended backends (graceful degradation)
    "ASTCodeBackend",
    "CallGraphBackend",
    "CPGBackend",
    "HDMABackend",
    "LSPSymbolBackend",
    "DependencyBackend",
    "QMDWikiBackend",
    "YtIsBackend",
    # Backend constants
    "BACKEND_NOTEBOOKLM",
    "BACKEND_SKILLS",
    "BACKEND_CKS_METADATA",
    "BACKEND_KG",
    "BACKEND_MULTILANG",
    "BACKEND_RLM",
    "BACKEND_CLAUDE_HISTORY",
    "BACKEND_VAULT",
    "BACKEND_AST_CODE",
    "BACKEND_LSP_SYMBOL",
    "BACKEND_NAME_CALL_GRAPH",
    "BACKEND_QMD_WIKI",
    "BACKEND_YT_IS",
    "SOURCE_RELIABILITY_MULTILANG",
    # Factory functions
    "create_cks_metadata_backend",
    "create_notebooklm_backend",
    "create_multilang_backend",
    "create_rlm_backend",
    "create_claude_history_backend",
    "create_vault_backend",
    "create_ast_backend",
    "create_lsp_backend",
    # Availability flags
    "CPG_AVAILABLE",
    "HDMA_AVAILABLE",
    "DEP_GRAPH_AVAILABLE",
]
