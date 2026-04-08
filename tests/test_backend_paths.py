#!/usr/bin/env python3
"""
Test backend path detection.
"""

import sys
from pathlib import Path

# Add paths
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.backends.local import CDSBackend, GrepBackend

print("=" * 80)
print("BACKEND PATH DETECTION TEST")
print("=" * 80)

print(f"\n[INFO] Current working directory: {Path.cwd()}")

# Test CDS backend with auto-detection
print("\n" + "-" * 80)
print("Testing CDSBackend with auto-detected paths")
print("-" * 80)

cds = CDSBackend(enable_cache=False)
print(f"CDS root_paths: {cds.root_paths}")

# Build index
print("\n[INFO] Building CDS index...")
cds.build_index()
print("[INFO] CDS index built")

# Search
results = cds.search("AsyncSearchRouter", limit=5)
print(f"[INFO] CDS search returned {len(results)} results")
for i, r in enumerate(results[:3]):
    print(f"  [{i+1}] {r}")

# Test Grep backend with auto-detection
print("\n" + "-" * 80)
print("Testing GrepBackend with auto-detected paths")
print("-" * 80)

grep = GrepBackend()
print(f"Grep root_paths: {grep.root_paths}")

# Build index
print("\n[INFO] Building Grep index...")
grep.build_index()
print(f"[INFO] Grep index built, {len(grep._index)} entries")

# Search
results = grep.search("AsyncSearchRouter", limit=5)
print(f"[INFO] Grep search returned {len(results)} results")
for i, r in enumerate(results[:3]):
    print(f"  [{i+1}] {r}")

print("\n" + "=" * 80)
print("CONCLUSION:")
if len(cds._index) > 0 or len(grep._index) > 0:
    print("✅ SUCCESS: Backends are auto-detecting paths correctly")
    print(f"   CDS: {len(cds._index)} indexed files")
    print(f"   Grep: {len(grep._index)} indexed files")
else:
    print("❌ FAILURE: Backends are not finding files to index")
    print(f"   CDS root_paths: {cds.root_paths}")
    print(f"   Grep root_paths: {grep.root_paths}")
print("=" * 80)
