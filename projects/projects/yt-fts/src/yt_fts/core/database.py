"""
Database Facade Module

This module acts as a facade, re-exporting functionality from the specialized
repository modules in `src/yt_fts/db/`. This maintains backward compatibility
for existing code that imports from `yt_fts.core.database`.
"""

from yt_fts.db.channels import (
    add_channel_info,
    add_channel_info_batch,
    check_if_channel_exists,
    delete_channel,
    get_batch_channel_ids_from_urls,
    get_channel_api_total,
    get_channel_id_from_input,
    get_channel_stats,
    get_channels,
    get_fresh_channels,
    set_channel_api_total,
    update_channel_id,
)
from yt_fts.db.channels import get_channel_name_from_db as get_channel_name_from_id
from yt_fts.db.infra import (
    BatchCommitManager,
    FileLock,
    enable_wal_mode,
    get_batch_manager,
    get_db_connection,
    retry_on_locked,
)
from yt_fts.db.maintenance import (
    cleanup_channels,
    ensure_last_checked_column,
    make_db,
    migrate_empty_title_videos,
    migrate_unavailable_videos,
    run_migrations,
)
from yt_fts.db.search import search_all, search_channel, search_video
from yt_fts.db.search_history import (
    clear_search_history,
    delete_saved_query,
    get_saved_queries,
    get_saved_query_by_name,
    get_search_history,
    save_query,
    save_search,
)
from yt_fts.db.skipped import (
    SKIPPED_REASON_DELETED,
    SKIPPED_REASON_EMPTY,
    SKIPPED_REASON_PRIVATE,
    add_skipped_channel,
    clear_skipped_channels,
    get_skipped_channels,
    is_channel_skipped,
    remove_skipped_channel,
    should_skip_permanent,
)
from yt_fts.db.utils import escape_fts5_query, parse_query, parse_query_with_proximity
from yt_fts.db.videos import (
    add_video,
    add_videos_bulk,
    get_channel_info_from_video_id,
    get_channel_name_from_video_id,
    get_metadata_from_db,
    get_num_vids,
    get_subs_by_video_id,
    get_vid_ids_by_channel_id,
    get_video_ids_without_subtitles,
    get_videos_needing_recheck,
    update_video_last_checked,
)
from yt_fts.utils.config import get_db_path

__all__ = [
    # Skipped Channels
    "SKIPPED_REASON_DELETED",
    "SKIPPED_REASON_EMPTY",
    "SKIPPED_REASON_PRIVATE",
    # Infra
    "BatchCommitManager",
    "FileLock",
    # Channels
    "add_channel_info",
    "add_channel_info_batch",
    "add_skipped_channel",
    # Videos
    "add_video",
    "add_videos_bulk",
    "check_if_channel_exists",
    # Maintenance
    "cleanup_channels",
    # Search History
    "clear_search_history",
    "clear_skipped_channels",
    "delete_channel",
    "delete_saved_query",
    "enable_wal_mode",
    "ensure_last_checked_column",
    # Utils
    "escape_fts5_query",
    "get_batch_channel_ids_from_urls",
    "get_batch_manager",
    "get_channel_api_total",
    "get_channel_id_from_input",
    "get_channel_info_from_video_id",
    "get_channel_name_from_id",
    "get_channel_name_from_video_id",
    "get_channel_stats",
    "get_channels",
    "get_db_connection",
    "get_db_path",
    "get_fresh_channels",
    "get_metadata_from_db",
    "get_num_vids",
    "get_saved_queries",
    "get_saved_query_by_name",
    "get_search_history",
    "get_skipped_channels",
    "get_subs_by_video_id",
    "get_vid_ids_by_channel_id",
    "get_video_ids_without_subtitles",
    "get_videos_needing_recheck",
    "is_channel_skipped",
    "make_db",
    "migrate_empty_title_videos",
    "migrate_unavailable_videos",
    "parse_query",
    "parse_query_with_proximity",
    "remove_skipped_channel",
    "retry_on_locked",
    "run_migrations",
    "save_query",
    "save_search",
    # Search
    "search_all",
    "search_channel",
    "search_video",
    "set_channel_api_total",
    "should_skip_permanent",
    "update_channel_id",
    "update_video_last_checked",
]
