"""Rebuild qmd wiki index — re-indexes any wiki concept files not yet in the qmd collection.

Usage:
    python P:/.agents/scripts/rebuild_qmd_index.py [--cpu]

By default uses GPU with retry-on-OOM: catches CUDA out-of-memory errors,
clears cache, and retries the file. Pass --cpu to force CPU mode (slower
but reliable if GPU is unavailable or contested).

The script:
1. Lists all .md files in P:/.data/wiki/concepts/
2. Checks which are already indexed in the qmd 'wiki' collection
3. Adds unindexed files one at a time with OOM retry (up to 3 attempts)

Run when wiki search quality degrades (qmd search returns stale/missing results).
The wiki index should match the file count in P:/.data/wiki/concepts/.
"""
import sys
from pathlib import Path
import time

# Parse --cpu flag before importing torch/qmd
force_cpu = "--cpu" in sys.argv
if force_cpu:
    import os
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import qmd


def _clear_gpu_cache():
    """Release fragmented VRAM to prevent OOM."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def _add_with_retry(coll, filepath, text, max_retries=3):
    """Add a document with OOM retry. Returns True on success, False on failure."""
    for attempt in range(max_retries):
        try:
            coll.add_document(
                document_id=filepath.stem,
                markdown=text,
                metadata={"source_path": str(filepath), "filename": filepath.name}
            )
            return True, None
        except Exception as e:
            err_str = str(e).lower()
            if "out of memory" in err_str and attempt < max_retries - 1:
                _clear_gpu_cache()
                time.sleep(1 + attempt)  # backoff: 1s, 2s, 3s
                continue
            return False, str(e)[:100]
    return False, "max retries exceeded"


client = qmd.connect()
coll = client.collection("wiki")

current_count = coll.info().document_count
wiki_files = sorted(Path("P:/.data/wiki/concepts").glob("*.md"))

indexed_ids = set()
for doc_id in coll.list_documents():
    if isinstance(doc_id, str):
        indexed_ids.add(doc_id)
    elif hasattr(doc_id, 'document_id'):
        indexed_ids.add(doc_id.document_id)
    else:
        indexed_ids.add(str(doc_id))

unindexed = [f for f in wiki_files if f.stem not in indexed_ids]
mode = "CPU" if force_cpu else "GPU+retry-on-OOM"
print(f"Current: {current_count} indexed, {len(unindexed)} remaining ({mode})")

total_added = 0
total_errors = 0

for f in unindexed:
    try:
        text = f.read_text(encoding="utf-8")
    except Exception as e:
        total_errors += 1
        print(f"  READ ERROR {f.name}: {str(e)[:80]}")
        continue

    success, error = _add_with_retry(coll, f, text)
    if success:
        total_added += 1
        print(f"  + {f.name}")
    else:
        total_errors += 1
        if "out of memory" in (error or "").lower():
            print(f"  OOM {f.name} (after retries) — try --cpu mode")
        else:
            print(f"  ERROR {f.name}: {error}")

final_count = coll.info().document_count
print(f"\nDone: {total_added} added, {total_errors} errors")
print(f"Wiki docs now: {final_count} (was {current_count})")
