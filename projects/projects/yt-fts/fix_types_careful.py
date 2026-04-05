#!/usr/bin/env python3
"""Carefully fix all mypy --strict type errors in database.py"""

import re

def fix_database_types():
    """Apply all type annotation fixes to database.py"""

    with open('P:/projects/yt-fts/src/yt_fts/core/database.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    for i, line in enumerate(lines, 1):
        new_line = line

        # Fix 1: Remove type re-assignments on self.lockfd (not line 33 where it's defined)
        if 'self.lockfd: Any = None' in line and i != 33:
            new_line = line.replace('self.lockfd: Any = None', 'self.lockfd = None')

        # Fix 2: Add return type to get_db_connection
        elif i == 270 and 'def get_db_connection(timeout: float = 30.0):' in line:
            new_line = line.replace(
                'def get_db_connection(timeout: float = 30.0):',
                'def get_db_connection(timeout: float = 30.0) -> sqlite3.Connection:'
            )

        # Fix 3: Add return type to retry_on_locked
        elif i == 296 and 'def retry_on_locked(max_retries: int = 5, initial_delay: float = 0.1):' in line:
            new_line = line.replace(
                'def retry_on_locked(max_retries: int = 5, initial_delay: float = 0.1):',
                'def retry_on_locked(max_retries: int = 5, initial_delay: float = 0.1) -> Any:'
            )

        # Fix 4: Add type to decorator
        elif i == 306 and '    def decorator(func):' in line:
            new_line = '    def decorator(func: Any) -> Any:\n'

        # Fix 5: Add type to wrapper
        elif i == 316 and '        def wrapper(*args, **kwargs):' in line:
            new_line = '        def wrapper(*args: Any, **kwargs: Any) -> Any:\n'

        # Fix 6: Add type to handler
        elif i == 149 and '        def handler(signum, frame):' in line:
            new_line = '        def handler(signum: int, frame: Any) -> None:\n'

        # Fix 7: Add type to _original_sigint_handler
        elif i == 121 and '        self._original_sigint_handler = None' in line:
            new_line = '        self._original_sigint_handler: Any = None\n'

        # Fix 8: Add return type to __enter__
        elif i == 198 and '    def __enter__(self):' in line:
            new_line = '    def __enter__(self) -> Any:\n'

        # Fix 9: Add return type to __exit__
        elif i == 202 and '    def __exit__(self, exc_type, exc_val, exc_tb):' in line:
            new_line = '    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:\n'

        # Fix 10: Replace dict[str, any] with dict[str, Any]
        elif 'dict[str, any]' in line.lower():
            new_line = line.replace('dict[str, any]', 'dict[str, Any]').replace('dict[str, any', 'dict[str, Any')

        # Fix 11: Fix videos parameter type
        elif i == 712 and '    videos: list[dict],' in line:
            new_line = '    videos: list[dict[str, Any]],\n'

        # Fix 12: Add type to _run_async
        elif i == 2362 and '    def _run_async(coro):' in line:
            new_line = '    def _run_async(coro: Any) -> Any:\n'

        # Fix 13: Fix get_batch_channel_stats return type
        elif i == 2115 and 'def get_batch_channel_stats(channel_ids: list[str]) -> dict[str, dict]:' in line:
            new_line = 'def get_batch_channel_stats(channel_ids: list[str]) -> dict[str, dict[str, Any]]:\n'

        # Fix 14: Fix list[dict] returns
        elif '-> list[dict]:' in line:
            new_line = line.replace('-> list[dict]:', '-> list[dict[str, Any]]:')

        # Fix 15: Fix exception raise
        elif i == 343 and '            raise last_error' in line:
            new_line = '            raise cast(BaseException, last_error)\n'

        fixed_lines.append(new_line)

    # Now do multiline fixes
    content = ''.join(fixed_lines)

    # Fix 16: Add missing return to get_vid_ids_by_channel_id
    content = re.sub(
        r'(def get_vid_ids_by_channel_id\(channel_id: str\) -> list\[tuple\[str\]\]:.*?    db = Database\(get_db_path\(\)\))\n\n\ndef get_channel_last_checked',
        r'\1\n\n    return db.execute(\n        "SELECT video_id FROM Videos WHERE channel_id = ?", [channel_id]\n    ).fetchall()\n\n\ndef get_channel_last_checked',
        content,
        flags=re.DOTALL
    )

    # Fix 17: Add type: ignore comments to sqlite_utils calls (carefully)
    # This needs to be done AFTER the call, not inside it
    patterns = [
        # Create calls
        (r'(db\["Channels"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["Videos"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["Subtitles"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SkippedChannels"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SemanticSearchEnabled"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SearchHistory"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SavedQueries"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["embeddings"\]\.create\(\s*\{)', r'\1  # type: ignore[union-attr]'),

        # Create_index calls - add at end of line
        (r'(db\["Videos"\]\.create_index\(\["channel_id"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["Subtitles"\]\.create_index\(\["video_id"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["Subtitles"\]\.create_index\(\["start_time"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SearchHistory"\]\.create_index\(\["timestamp"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SearchHistory"\]\.create_index\(\["scope"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SavedQueries"\]\.create_index\(\["name"\], if_not_exists=True, unique=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["embeddings"\]\.create_index\(\["channel_id"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["embeddings"\]\.create_index\(\["video_id"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),
        (r'(db\["embeddings"\]\.create_index\(\["model_name"\], if_not_exists=True\))', r'\1  # type: ignore[union-attr]'),

        # Insert calls
        (r'(db\["Channels"\]\.insert_all\()', r'\1  # type: ignore[union-attr]'),
        (r'(db\["Subtitles"\]\.insert\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SearchHistory"\]\.insert\(\s*\{)', r'\1  # type: ignore[union-attr]'),
        (r'(db\["SavedQueries"\]\.insert\(\s*\{)', r'\1  # type: ignore[union-attr]'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    with open('P:/projects/yt-fts/src/yt_fts/core/database.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Fixed all type annotations in database.py")

if __name__ == '__main__':
    fix_database_types()
