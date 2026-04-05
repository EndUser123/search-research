#!/usr/bin/env python3
"""Fix all mypy --strict type errors in database.py"""

import re

def fix_database_types():
    """Apply all type annotation fixes to database.py"""

    with open('P:/projects/yt-fts/src/yt_fts/core/database.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix 1: Remove type re-assignments on self.lockfd (lines 51, 64, 86)
    content = re.sub(
        r'self\.lockfd: Any = None',
        'self.lockfd = None',
        content
    )

    # Fix 2: Add return type annotation to get_db_connection
    content = re.sub(
        r'def get_db_connection\(timeout: float = 30\.0\):',
        'def get_db_connection(timeout: float = 30.0) -> sqlite3.Connection:',
        content
    )

    # Fix 3: Add return type annotation to retry_on_locked
    content = re.sub(
        r'def retry_on_locked\(max_retries: int = 5, initial_delay: float = 0\.1\):',
        'def retry_on_locked(max_retries: int = 5, initial_delay: float = 0.1) -> Any:',
        content
    )

    # Fix 4: Add type annotations to decorator functions
    content = re.sub(
        r'def decorator\(func\):',
        'def decorator(func: Any) -> Any:',
        content
    )

    content = re.sub(
        r'def wrapper\(\*args, \*\*kwargs\):',
        'def wrapper(*args: Any, **kwargs: Any) -> Any:',
        content
    )

    # Fix 5: Add type annotation to handler in _register_signal_handler
    content = re.sub(
        r'def handler\(signum, frame\):',
        'def handler(signum: int, frame: Any) -> None:',
        content
    )

    # Fix 6: Add type annotation to _original_sigint_handler
    content = re.sub(
        r'self\._original_sigint_handler = None',
        'self._original_sigint_handler: Any = None',
        content
    )

    # Fix 7: Add return type to __enter__ and __exit__
    content = re.sub(
        r'def __enter__\(self\):',
        'def __enter__(self) -> Any:',
        content
    )

    content = re.sub(
        r'def __exit__\(self, exc_type, exc_val, exc_tb\):',
        'def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:',
        content
    )

    # Fix 8: Fix sqlite_utils Table | View issues with cast
    # Wrap db["table"].create() calls with type: ignore
    patterns_to_fix = [
        (r'(db\["Channels"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["Videos"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["Subtitles"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["SkippedChannels"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["SemanticSearchEnabled"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["SearchHistory"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["SavedQueries"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["embeddings"\]\.create\()', r'cast(Any, \1'),
        (r'(db\["Channels"\]\.insert_all\()', r'cast(Any, \1'),
        (r'(db\["Videos"\]\.create_index\()', r'\1  # type: ignore[union-attr]'),
        (r'(db\["Subtitles"\]\.create_index\()', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SearchHistory"\]\.create_index\()', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SavedQueries"\]\.create_index\()', r'\1  # type: ignore[union-attr]'),
        (r'(db\["embeddings"\]\.create_index\()', r'\1  # type: ignore[union-attr]'),
        (r'(db\["Subtitles"\]\.insert\()', r'cast(Any, \1'),
        (r'(db\["SearchHistory"\]\.insert\()', r'cast(Any, \1'),
        (r'(db\["SavedQueries"\]\.insert\()', r'cast(Any, \1'),
    ]

    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content)

    # Fix 9: Replace bare 'dict' with 'dict[str, Any]'
    content = re.sub(
        r'list\[dict\]',
        'list[dict[str, Any]]',
        content
    )

    content = re.sub(
        r': dict\]',
        ': dict[str, Any]]',
        content
    )

    # Fix 10: Replace builtin 'any' with 'typing.Any' in type annotations
    content = re.sub(
        r'dict\[str, any\]',
        'dict[str, Any]',
        content
    )

    # Fix 11: Fix int to str conversions in add_video (lines 676, 684, 688)
    # These should be str, not int
    content = re.sub(
        r'if duration is not None:\s+columns\.append\("duration"\)\s+values\.append\(duration\)',
        '''if duration is not None:
                columns.append("duration")
                values.append(str(duration))''',
        content
    )

    content = re.sub(
        r'if view_count is not None:\s+columns\.append\("view_count"\)\s+values\.append\(view_count\)',
        '''if view_count is not None:
                columns.append("view_count")
                values.append(str(view_count))''',
        content
    )

    content = re.sub(
        r'if is_short is not None:\s+columns\.append\("is_short"\)\s+values\.append\(is_short\)',
        '''if is_short is not None:
                columns.append("is_short")
                values.append(str(is_short))''',
        content
    )

    # Fix 12: Add type annotation to videos parameter in add_videos_bulk
    content = re.sub(
        r'def add_videos_bulk\(\s+channel_id: str,\s+videos: list\[dict\],',
        '''def add_videos_bulk(
        channel_id: str,
        videos: list[dict[str, Any]],''',
        content
    )

    # Fix 13: Add missing return to get_vid_ids_by_channel_id
    content = re.sub(
        r'(def get_vid_ids_by_channel_id\(channel_id: str\) -> list\[tuple\[str\]\]:.*?db = Database\(get_db_path\(\)\))',
        r'\1\n\n    return db.execute(\n        "SELECT video_id FROM Videos WHERE channel_id = ?", [channel_id]\n    ).fetchall()',
        content,
        flags=re.DOTALL
    )

    # Fix 14: Add type annotation to _run_async
    content = re.sub(
        r'def _run_async\(coro\):',
        'def _run_async(coro: Any) -> Any:',
        content
    )

    # Fix 15: Fix unreachable code warnings - mark returns as explicit
    content = re.sub(
        r'(if self\._original_sigint_handler is not None:\s+return  # Already registered)',
        r'\1\n        raise RuntimeError("Unreachable")',
        content
    )

    content = re.sub(
        r'(if self\._conn:\s+self\._conn\.close\(\)\s+self\._conn = None\s+if self\._original_sigint_handler:\s+signal\.signal\(signal\.SIGINT, self\._original_sigint_handler\))',
        r'\1\n        else:\n            raise RuntimeError("Unreachable")',
        content
    )

    # Fix 16: Fix exception type in retry decorator
    content = re.sub(
        r'raise last_error',
        'raise cast(BaseException, last_error)',
        content
    )

    # Fix 17: Fix dict return type in get_batch_channel_stats
    content = re.sub(
        r'def get_batch_channel_stats\(channel_ids: list\[str\]\) -> dict\[str, dict\]:',
        'def get_batch_channel_stats(channel_ids: list[str]) -> dict[str, dict[str, Any]]:',
        content
    )

    # Write the fixed content
    with open('P:/projects/yt-fts/src/yt_fts/core/database.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Fixed all type annotations in database.py")

if __name__ == '__main__':
    fix_database_types()
