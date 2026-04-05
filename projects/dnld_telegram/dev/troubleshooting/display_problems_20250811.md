PS C:\_Python\_Projects\dnld_telegram> python -m src.download --max-concurrent 2 --ui A
2025-08-11 14:13:35.220 | DEBUG    | src.download.storage:<module>:19 - Database storage layer initialized - using SQLite backend
2025-08-11 14:13:35.345 | DEBUG    | src.download.config.logging_config:set_run_id:18 - Set global run ID to: c8eccd09-f54f-446b-943f-f4df162418a2
2025-08-11 14:13:35.347 | DEBUG    | config.manager:_load_app_config:121 - Applied development environment overrides
2025-08-11 14:13:35.347 | DEBUG    | config.manager:reload:90 - Configuration reloaded successfully
[08/11/25 14:13:35] WARNING  2025-08-11 14:13:35.356 | WARNING  | src.config.config_manager:_load_configs:27 - Configuration file config_manager.py:27
                             not found at C:\_Python\_Projects\dnld_telegram\src\config\..\..\config.toml. Using empty
                             configuration.
jcexclusive, .\channels\jcexclusive\_media
⚠️ Press Ctrl+C to stop gracefully ⚠️
  ✨ Starting database-filesystem sync (dry_run=False)
  💽 Filesystem Status
        Files on disk: 80
            Video: 80
            Image: 0
            Audio: 0
            Txt/PDF: 0
            Other: 0
        Database pending: 0
        Matches found: 80
        Updated to completed: 0
        Unmatched files: 0
        Errors: 0
  💾 Database Status
        Media files tracked in database: 80
            Video: 0 (already downloaded)
            Image: 0 (already downloaded)
            Audio: 0
            Txt/PDF: 0
            Other: 0
  ✨ Incremental Telegram sync starting
  ✨ Incremental Telegram sync completed
  📤 Telegram (Incremental update)
                New Messages: 0
        New Media files: 0
            Video: 0
            Image: 0
            Audio: 0
            Txt/PDF: 0
            Other: 0
  📋 Download Queue
        New media files to download: 0
  ✨ Starting database-filesystem sync (dry_run=False)
  💽 Filesystem Status
        Files on disk: 80
            Video: 80
            Image: 0
            Audio: 0
            Txt/PDF: 0
            Other: 0
        Database pending: 0
        Matches found: 80
        Updated to completed: 0
        Unmatched files: 0
        Errors: 0
  💾 Database Status
        Media files tracked in database: 80
            Video: 0 (already downloaded)
            Image: 0 (already downloaded)
            Audio: 0
            Txt/PDF: 0
            Other: 80
  ✨ Incremental Telegram sync starting
  ✨ Incremental Telegram sync completed
  📤 Telegram (Incremental update)
                New Messages: 0
        New Media files: 0
            Video: 0
            Image: 0
            Audio: 0
            Txt/PDF: 0
            Other: 0
  📋 Download Queue
        New media files to download: 0
  💾 Database Status
        Old media files tracked: 153
        Completed media files skipped: 153
  ✨ Incremental Telegram sync starting
[08/11/25 14:13:37] ERROR    2025-08-11 14:13:37.038 | ERROR    | src.download.plugins.enumeration:enumerate_media_in_channel:192 - enumeration.py:192
                             Unexpected error enumerating media in channel -1002436706028: 'dict' object has no attribute
                             '_enumeration_stats' and no __dict__ for setting new attributes
  ✨ Incremental Telegram sync completed
  📤 Telegram (Incremental update)
        No enumeration statistics available
  📋 Download Queue
        New media files to download: 0
---
koreannarchive, .\channels\koreannarchive\_media
⚠️ Press Ctrl+C to stop gracefully ⚠️
                    WARNING  2025-08-11 14:13:37.722 | WARNING  |                                                                  reverse_sync.py:205
                             src.download.reverse_sync:sync_channel_database_with_filesystem:205 - Found 1 files on disk in
                             channel 'koreannarchive' with no database match:
                               - E:\dnld_media\telegram\channels\koreannarchive\_media\photo_2024-07-31_11-36-23.jpg
[08/11/25 14:13:38] WARNING  2025-08-11 14:13:38.239 | WARNING  |                                                                  reverse_sync.py:205
                             src.download.reverse_sync:sync_channel_database_with_filesystem:205 - Found 1 files on disk in
                             channel 'koreannarchive' with no database match:
                               - E:\dnld_media\telegram\channels\koreannarchive\_media\photo_2024-07-31_11-36-23.jpg
  ✨ Starting database-filesystem sync (dry_run=False)
        Found 1 files on disk in channel 'koreannarchive' with no database match:
          - channels\koreannarchive\_media\photo_2024-07-31_11-36-23.jpg
  💽 Filesystem Status
        Files on disk: 728
            Video: 398
            Image: 329
            Audio: 0
            Txt/PDF: 0
            Other: 1
        Database pending: 0
        Matches found: 727
        Updated to completed: 0
        Unmatched files: 1
        Errors: 0
  💾 Database Status
        Media files tracked in database: 743
            Video: 410 (already downloaded)
            Image: 332 (already downloaded)
            Audio: 0
            Txt/PDF: 0
            Other: 0
  ✨ Incremental Telegram sync starting
  ✨ Incremental Telegram sync completed
  📤 Telegram (Incremental update)
                New Messages: 999
        New Media files: 888
            Video: 111
            Image: 222
            Audio: 0
            Txt/PDF: 0
            Other: 0
  📋 Download Queue
        New media files to download: 0
[08/11/25 14:13:39] WARNING  2025-08-11 14:13:39.053 | WARNING  |                                                                  reverse_sync.py:205
                             src.download.reverse_sync:sync_channel_database_with_filesystem:205 - Found 1 files on disk in
                             channel 'koreannarchive' with no database match:
                               - E:\dnld_media\telegram\channels\koreannarchive\_media\photo_2024-07-31_11-36-23.jpg
                    WARNING  2025-08-11 14:13:39.642 | WARNING  |                                                                  reverse_sync.py:205
                             src.download.reverse_sync:sync_channel_database_with_filesystem:205 - Found 1 files on disk in
                             channel 'koreannarchive' with no database match:
                               - E:\dnld_media\telegram\channels\koreannarchive\_media\photo_2024-07-31_11-36-23.jpg
  ✨ Starting database-filesystem sync (dry_run=False)
        Found 1 files on disk in channel 'koreannarchive' with no database match:
          - channels\koreannarchive\_media\photo_2024-07-31_11-36-23.jpg
  💽 Filesystem Status
        Files on disk: 728
            Video: 398
            Image: 329
            Audio: 0
            Txt/PDF: 0
            Other: 1
        Database pending: 0
        Matches found: 727
        Updated to completed: 0
        Unmatched files: 1
        Errors: 0
  💾 Database Status
        Media files tracked in database: 743
            Video: 410 (already downloaded)
            Image: 332 (already downloaded)
            Audio: 0
            Txt/PDF: 0
            Other: 0
  ✨ Incremental Telegram sync starting
  ✨ Incremental Telegram sync completed
  📤 Telegram (Incremental update)
                New Messages: 999
        New Media files: 888
            Video: 111
            Image: 222
            Audio: 0
            Txt/PDF: 0
            Other: 0
  📋 Download Queue
        New media files to download: 0
  💾 Database Status
        Old media files tracked: 742
        Completed media files skipped: 742
  ✨ Incremental Telegram sync starting
  ✨ Incremental Telegram sync completed
[08/11/25 14:13:40] ERROR    2025-08-11 14:13:40.307 | ERROR    | src.download.plugins.enumeration:enumerate_media_in_channel:192 - enumeration.py:192
                             Unexpected error enumerating media in channel -1001518888395: 'dict' object has no attribute
                             '_enumeration_stats' and no __dict__ for setting new attributes
  📤 Telegram (Incremental update)
        No enumeration statistics available
  📋 Download Queue
        New media files to download: 0
---
leaksasian, .\channels\leaksasian\_media
⚠️ Press Ctrl+C to stop gracefully ⚠️
[08/11/25 14:13:42] ERROR    2025-08-11 14:13:42.299 | ERROR    |                                                                  reverse_sync.py:208
                             src.download.reverse_sync:sync_channel_database_with_filesystem:208 - Error during
                             database-filesystem sync: Channel 'leaksasian' not found and no telegram_id provided
Could not get final download count: Channel 'leaksasian' not found and no telegram_id provided
                    ERROR    2025-08-11 14:13:42.304 | ERROR    | __main__:process_channel_operations:355 - Error processing channel   __main__.py:355
                             operations for 'leaksasian': Channel 'leaksasian' not found and no telegram_id provided
channel_2226701349, .\channels\channel_2226701349\_media
⚠️ Press Ctrl+C to stop gracefully ⚠️
                    ERROR    2025-08-11 14:13:42.304 | ERROR    | __main__:process_single_channel:224 - Error in                       __main__.py:224
                             process_single_channel for 'leaksasian': Channel 'leaksasian' not found and no telegram_id provided
                    ERROR    2025-08-11 14:13:42.304 | ERROR    | __main__:main:718 - ❌ Error processing channel 'leaksasian':        __main__.py:718
                             Channel 'leaksasian' not found and no telegram_id provided
[08/11/25 14:13:44] WARNING  2025-08-11 14:13:44.231 | WARNING  |                                                                  reverse_sync.py:205
                             src.download.reverse_sync:sync_channel_database_with_filesystem:205 - Found 3 files on disk in
                             channel 'channel_2226701349' with no database match:
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\00001.mp4
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\449693898667cbc6b40ca4.mp4
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\IMG_2800.mp4
[08/11/25 14:13:45] WARNING  2025-08-11 14:13:45.934 | WARNING  |                                                                  reverse_sync.py:205
                             src.download.reverse_sync:sync_channel_database_with_filesystem:205 - Found 3 files on disk in
                             channel 'channel_2226701349' with no database match:
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\00001.mp4
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\449693898667cbc6b40ca4.mp4
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\IMG_2800.mp4
  ✨ Starting database-filesystem sync (dry_run=False)
        Found 4 files on disk in channel 'channel_2226701349' with no database match:
          - channels/channel_2226701349/_media/00001.mp4
          - channels/channel_2226701349/_media/146.jpg
          - channels/channel_2226701349/_media/449693898667cbc6b40ca4.mp4
          - channels/channel_2226701349/_media/IMG_2800.mp4
  💽 Filesystem Status
        Files on disk: 1504
            Video: 677
            Image: 826
            Audio: 0
            Txt/PDF: 0
            Other: 1
        Database pending: 0
        Matches found: 1500
        Updated to completed: 0
        Unmatched files: 4
        Errors: 0
  💾 Database Status
        Media files tracked in database: 1504
            Video: 0 (already downloaded)
            Image: 0 (already downloaded)
            Audio: 0
            Txt/PDF: 0
            Other: 0
  ✨ Incremental Telegram sync starting
  ✨ Incremental Telegram sync completed
  📤 Telegram (Incremental update)
                New Messages: 0
        New Media files: 0
            Video: 0
            Image: 0
            Audio: 0
            Txt/PDF: 0
            Other: 0
  📋 Download Queue
        New media files to download: 0
[08/11/25 14:13:47] WARNING  2025-08-11 14:13:47.933 | WARNING  |                                                                  reverse_sync.py:205
                             src.download.reverse_sync:sync_channel_database_with_filesystem:205 - Found 3 files on disk in
                             channel 'channel_2226701349' with no database match:
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\00001.mp4
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\449693898667cbc6b40ca4.mp4
                               - E:\dnld_media\telegram\channels\channel_2226701349\_media\IMG_2800.mp4

Interrupted by user
PS C:\_Python\_Projects\dnld_telegram>
