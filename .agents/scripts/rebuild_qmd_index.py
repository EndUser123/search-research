"""Rebuild qmd wiki index — re-indexes any wiki concept files not yet in the qmd collection.

Usage:
    python P:/.agents/scripts/rebuild_qmd_index.py [--cpu]

By default uses GPU with torch.cuda.empty_cache() between batches to avoid OOM.
Pass --cpu to force CPU mode (slower but reliable if GPU is unavailable or contested).

The script:
1. Lists all .md files in P:/.data/wiki/concepts/
2. Checks which are already indexed in the qmd 'wiki' collection
3. Adds unindexed files in batches of 5
4. Between batches: clears GPU cache (default) or sleeps 1s (--cpu)

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
    """Release fragmented VRAM between batches to prevent OOM."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass

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
mode = "CPU" if force_cpu else "GPU+cache-clear"
print(f"Current: {current_count} indexed, {len(unindexed)} remaining ({mode})")

BATCH_SIZE = 5
total_added = 0
total_errors = 0

for i in range(0, len(unindexed), BATCH_SIZE):
    batch = unindexed[i:i + BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(unindexed) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nBatch {batch_num}/{total_batches}...")

    for f in batch:
        try:
            text = f.read_text(encoding="utf-8")
            coll.add_document(
                document_id=f.stem,
                markdown=text,
                metadata={"source_path": str(f), "filename": f.name}
            )
            total_added += 1
            print(f"  + {f.name}")
        except Exception as e:
            total_errors += 1
            err_str = str(e)[:80]
            if "out of memory" in err_str.lower():
                print(f"  OOM {f.name} — try --cpu mode")
            else:
                print(f"  ERROR {f.name}: {err_str}")

    # Between batches: clear GPU cache (default) or sleep (CPU mode)
    if force_cpu:
        time.sleep(1)
    else:
        _clear_gpu_cache()
        time.sleep(0.5)  # shorter pause for GPU since cache clear handles memory

final_count = coll.info().document_count
print(f"\nDone: {total_added} added, {total_errors} errors")
print(f"Wiki docs now: {final_count} (was {current_count})")
