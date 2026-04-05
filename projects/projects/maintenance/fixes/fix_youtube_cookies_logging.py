#!/usr/bin/env python3
"""Fix the logging format issue in youtube_cookies.py that causes 'function' object has no attribute 'name' error"""


def fix_youtube_cookies_logging():
    """Fix the logging format string that uses {function} which may not be available"""
    file_path = r"C:\_Python\_Projects\ai_studio\src\ai_studio\youtube_cookies.py"

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Fix the problematic format string that uses {function}
    old_format = 'format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"'
    new_format = (
        'format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}"'
    )

    content = content.replace(old_format, new_format)

    # Write the fixed file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Fixed logging format issue in youtube_cookies.py")
    return True


if __name__ == "__main__":
    fix_youtube_cookies_logging()
