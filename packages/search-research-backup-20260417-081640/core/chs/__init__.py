"""CHS v2 - Chat History Search System Version 2."""

__version__ = "2.0.0-dev"
from .clustering import cluster_results, filter_results_by_cluster
from .critical import CHSIndexer, CHSMigrator, CHSSearcher, CHSValidator
from .intelligent_defaults import (
    IntelligentDefaults,
    get_feature_config,
    should_cluster,
    should_enable_session,
    should_explain,
)
from .normalized import (
    get_events_by_hash,
    query_opportunities,
    query_tasks,
    upsert_event,
)
from .projections import (
    health_check,
    query_events,
    query_events_by_session,
)
from .task_projection import open_tasks, resolve_task
from .search import (
    CHSSearchV2,
    CHSSearchWithSession,
    SearchSession,
    SearchSessionManager,
    get_session_manager,
    search_turns,
)
from .verify_backup import (
    BackupMetadata,
    compute_directory_sha256,
    compute_sha256,
    create_backup_metadata,
    get_exact_message_count,
    set_restrictive_permissions,
    verify_database_backup,
    verify_database_integrity,
    verify_faiss_backup,
)

__all__ = [
    "BackupMetadata",
    "CHSIndexer",
    "CHSValidator",
    "CHSSearcher",
    "CHSMigrator",
    "CHSSearchV2",
    "CHSSearchWithSession",
    "SearchSession",
    "SearchSessionManager",
    "cluster_results",
    "compute_directory_sha256",
    "compute_sha256",
    "create_backup_metadata",
    "filter_results_by_cluster",
    "get_events_by_hash",
    "get_exact_message_count",
    "get_feature_config",
    "get_session_manager",
    "health_check",
    "IntelligentDefaults",
    "query_events",
    "query_events_by_session",
    "query_opportunities",
    "query_tasks",
    "open_tasks",
    "resolve_task",
    "search_turns",
    "set_restrictive_permissions",
    "should_cluster",
    "should_enable_session",
    "should_explain",
    "upsert_event",
    "verify_database_backup",
    "verify_database_integrity",
    "verify_faiss_backup",
]
