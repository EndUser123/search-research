"""Rebuild qmd wiki index — re-indexes any wiki concept files not yet in the qmd collection.

Usage:
    python P:/.agents/scripts/rebuild_qmd_index.py

Forces CPU mode (CUDA_VISIBLE_DEVICES=-1) to avoid GPU OOM on the Qwen3-Embedding model
when processing large batches. CPU is slower (~5s/file) but reliable.

The script:
1. Lists all .md files in P:/.data/wiki/concepts/
2. Checks which are already indexed in the qmd 'wiki' collection
3. Adds unindexed files in batches of 5 with a 1s pause between batches

Run when wiki search quality degrades (qmd search returns stale/missing results).
The wiki index should match the file count in P:/.data/wiki/concepts/.
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # force CPU to avoid GPU OOM

import qmd
from pathlib import Path
import time

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
print(f"Current: {current_count} indexed, {len(unindexed)} remaining (CPU mode)")

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
            print(f"  ERROR {f.name}: {str(e)[:60]}")

    time.sleep(1)

final_count = coll.info().document_count
print(f"\nDone: {total_added} added, {total_errors} errors")
print(f"Wiki docs now: {final_count} (was {current_count})")
