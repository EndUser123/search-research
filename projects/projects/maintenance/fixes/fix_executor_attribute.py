#!/usr/bin/env python3
"""Fix the executor attribute reference in main.py"""


def fix_executor_attribute():
    """Fix the executor.max_workers reference to executor._max_workers"""
    file_path = r"C:\_Python\_Projects\ai_studio\src\ai_studio\main.py"

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Fix the executor attribute
    content = content.replace(
        'logger.info(f"Unified executor configured with {executor.max_workers} workers")',
        'logger.info(f"Unified executor configured with {executor._max_workers} workers")',
    )

    # Write the fixed file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Fixed executor attribute reference in main.py")
    return True


if __name__ == "__main__":
    fix_executor_attribute()
