#!/usr/bin/env python3
"""Fix the syntax error in tensor_utils.py by removing the duplicate import."""


def fix_tensor_utils_syntax():
    """Fix the syntax error in tensor_utils.py"""
    file_path = r"C:\_Python\_Projects\ai_studio\src\ai_studio\tensor_utils.py"

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Find and fix the problematic line 304
    fixed_lines = []
    for i, line in enumerate(lines):
        if i == 303:  # Line 304 (0-indexed)
            # Remove the problematic import line
            if (
                line.strip()
                == "from .unified_audio_error_handler import get_audio_error_handler, handle_audio_error"
            ):
                continue  # Skip this line
        fixed_lines.append(line)

    # Write the fixed file
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(fixed_lines)

    print("✅ Fixed syntax error in tensor_utils.py")
    return True


if __name__ == "__main__":
    fix_tensor_utils_syntax()
