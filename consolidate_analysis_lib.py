import os
import hashlib
import shutil
from pathlib import Path

files = ["detectors.py", "render.py", "machine_render.py", "transcript.py", "state.py", "clustering.py", "dedupe.py", "evidence.py", "impact_radius.py", "invocation_tracker.py", "stuckness.py", "verification_debt.py", "workflow_hygiene.py", "targeting.py", "util.py", "resolve.py", "route.py", "normalize.py", "carryover.py", "context.py", "context_boundaries.py", "coverage.py", "docs_followup.py", "freshness.py", "merge.py", "verify.py"]
shared_dir = Path("P:/packages/cc-skills-analysis/__lib")
shared_dir.mkdir(exist_ok=True)

def get_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

for f in files:
    f1 = Path("P:/packages/cc-skills-analysis/skills/gto/__lib") / f
    f2 = Path("P:/packages/cc-skills-analysis/skills/gto_v2/__lib") / f
    if f1.exists() and f2.exists():
        if get_hash(f1) == get_hash(f2):
            shutil.copy2(f1, shared_dir / f)
            print(f"SHARED: {f}")
        else:
            print(f"DIFFERENT: {f}")
    elif f1.exists():
        shutil.copy2(f1, shared_dir / f)
        print(f"ONLY IN GTO: {f}")
    elif f2.exists():
        shutil.copy2(f2, shared_dir / f)
        print(f"ONLY IN GTO_V2: {f}")
