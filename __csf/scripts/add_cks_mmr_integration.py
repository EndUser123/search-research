#!/usr/bin/env python3
"""Add MMR integration to CKS reranking."""

import sys

file_path = "P:/worktrees/w1t2/__csf/src/cks/reranking.py"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add the import at the top
old_imports = """import math
from datetime import UTC, datetime"""

new_imports = """import math
from datetime import UTC, datetime

# Import MMR from unified search system
try:
    from search.reranking import mmr_rerank
    MMR_AVAILABLE = True
except ImportError:
    # search.reranking not available, MMR disabled
    MMR_AVAILABLE = False"""

if old_imports not in content:
    print("ERROR: Old imports pattern not found")
    sys.exit(1)

content = content.replace(old_imports, new_imports)

# Step 2: Update the function signature
old_sig = """def apply_length_aware_reranking(
    results: list[dict],
    base_score_field: str = "rrf_score",
    density_weight: float = 0.3,
    type_boost: float = 0.15,
    query: str = "",
) -> list[dict]:"""

new_sig = """def apply_length_aware_reranking(
    results: list[dict],
    base_score_field: str = "rrf_score",
    density_weight: float = 0.3,
    type_boost: float = 0.15,
    query: str = "",
    enable_mmr: bool = False,
    mmr_lambda: float = 0.5,
) -> list[dict]:"""

if old_sig not in content:
    print("ERROR: Old signature not found")
    sys.exit(1)

content = content.replace(old_sig, new_sig)

# Step 3: Update the docstring
old_doc = """    query: Search query (used to make pattern boost conditional)

    Returns:
        Re-ranked list with adjusted scores
    \"\"\""""

new_doc = """    query: Search query (used to make pattern boost conditional)
        enable_mmr: Enable MMR diversity reranking after density adjustment
        mmr_lambda: MMR lambda parameter (0=favor diversity, 1=favor relevance, 0.5=balanced)

    Returns:
        Re-ranked list with adjusted scores and MMR metadata if enabled
    \"\"\""""

if old_doc not in content:
    print("ERROR: Old docstring not found")
    sys.exit(1)

content = content.replace(old_doc, new_doc)

# Step 4: Add MMR logic before return
old_return = """    # Re-sort by adjusted score
    results.sort(key=lambda x: x.get("length_adjusted_score", 0), reverse=True)

    return results"""

new_return = """    # Re-sort by adjusted score
    results.sort(key=lambda x: x.get("length_adjusted_score", 0), reverse=True)

    # Apply MMR for diversity if enabled and available
    if enable_mmr and MMR_AVAILABLE and len(results) > 1:
        # Use length_adjusted_score as relevance input to MMR
        for r in results:
            r["score"] = r.get("length_adjusted_score", r.get(base_score_field, 0))

        results = mmr_rerank(results, lambda_param=mmr_lambda)

        # Restore original score field for reference
        for r in results:
            if "score" in r:
                r["_original_length_adjusted_score"] = r.pop("score")

    return results"""

if old_return not in content:
    print("ERROR: Old return not found")
    sys.exit(1)

content = content.replace(old_return, new_return)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("MMR integration added successfully")
