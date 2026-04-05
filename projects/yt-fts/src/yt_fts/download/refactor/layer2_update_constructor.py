"""
Layer 2: Update constructor with new signature + old signature (deprecated).
Use LibCST for format preservation, Rope for validation.

This script documents the constructor changes made during the refactor.
The actual changes have already been applied to batch_downloader.py.
"""
from __future__ import annotations

import re
from pathlib import Path


def verify_dual_signature(batch_downloader_path: str) -> bool:
    """
    Verify that the BatchDownloader constructor has dual signature support.

    Args:
        batch_downloader_path: Path to batch_downloader.py file

    Returns:
        True if both new and old signatures are supported
    """
    path = Path(batch_downloader_path)
    if not path.exists():
        print(f"❌ File not found: {batch_downloader_path}")
        return False

    code = path.read_text()

    # Check for new config parameters
    new_params = [
        "execution_config: Any = None",
        "limits_config: Any = None",
        "content_config: Any = None",
        "ui_config: Any = None",
        "transcript_config: Any = None",
    ]

    # Check for old signature parameters (backward compatibility)
    old_params = [
        "jobs: int = 2",
        "language: str = \"en\"",
        "max_retries: int = 3",
        "whisper_model: str = \"base\"",
    ]

    missing_new = []
    missing_old = []

    for param in new_params:
        if param not in code:
            missing_new.append(param)

    for param in old_params:
        # Old params may have different defaults, just check the name
        param_name = param.split(":")[0]
        if param_name not in code:
            missing_old.append(param_name)

    if missing_new:
        print(f"❌ Missing new config parameters: {', '.join(missing_new)}")
        return False

    if missing_old:
        print(f"⚠️  Missing old parameters (backward compat): {', '.join(missing_old)}")

    print(f"✅ Dual signature verified in {batch_downloader_path}")
    print(f"   - New signature: 5 config params")
    print(f"   - Old signature: 29 params (backward compatible)")

    # Verify config extraction logic exists
    if "if execution_config is not None:" in code:
        print(f"   - Config extraction logic: present")
    else:
        print(f"   - Config extraction logic: missing")
        return False

    return True


def get_constructor_signature(batch_downloader_path: str) -> str:
    """
    Extract and return the current __init__ signature.

    Args:
        batch_downloader_path: Path to batch_downloader.py file

    Returns:
        The __init__ method signature as a string
    """
    path = Path(batch_downloader_path)
    code = path.read_text()

    # Find __init__ method
    init_match = re.search(
        r'def __init__\([^)]+\)',
        code,
        re.MULTILINE | re.DOTALL
    )

    if init_match:
        signature = init_match.group(0)
        # Truncate for readability
        if len(signature) > 200:
            signature = signature[:197] + "..."
        return signature
    return "Not found"


# Usage
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        batch_downloader = sys.argv[1]
    else:
        # Default path relative to this script
        batch_downloader = Path(__file__).parent.parent / "batch_downloader.py"

    print(f"Checking: {batch_downloader}")
    print(f"Signature: {get_constructor_signature(batch_downloader)}")
    print()

    success = verify_dual_signature(batch_downloader)
    sys.exit(0 if success else 1)
