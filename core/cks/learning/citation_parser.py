"""Citation parser for extracting file:line references from text.

Parses citations in format: path/to/file.py:123 or P:\\\\\\absolute/path.py:123
Returns structured metadata for CKS storage.
"""

from __future__ import annotations

import re
from typing import Any


def extract_citations(text: str) -> dict[str, Any]:
    """Extract file:line citations from text.

    Supports formats:
    - Relative: path/to/file.py:123
    - Absolute (Windows): P:\\\\\\path/to/file.py:123
    - Extensions: py, md, ts, js, yaml, yml, json, sh

    Args:
        text: Text containing potential citations

    Returns:
        Dict with 'file_path' and 'line_number' if found, empty dict otherwise.
        Example: {"file_path": "contract_api.py", "line_number": 142}

    """
    # Pattern matches:
    # - Optional P:\\\\\\ prefix (Windows absolute paths)
    # - File path with alphanumeric, underscore, dash, dot, forward slash
    # - File extension from supported set
    # - Colon followed by line number
    pattern = r"(?:P:\\\\\\)?([A-Za-z0-9_\-./]+)\.(py|md|ts|js|yaml|yml|json|sh):(\d+)"
    match = re.search(pattern, text)

    if match:
        file_path = match.group(1) + "." + match.group(2)
        line_number = int(match.group(3))
        return {"file_path": file_path, "line_number": line_number}

    return {}
