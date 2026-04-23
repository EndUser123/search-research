#!/usr/bin/env python3
"""Batch gitingest runner — one notebook per repo."""

import subprocess
from pathlib import Path

REPOS = [
    ("revfactory/harness",                    "25bc09d7-d97d-4c87-89ae-ddd1a14301c8"),
    ("mohi-devhub/antivibe",                   "2ab976ef-7540-4ca2-ba81-58641c43ac30"),
    ("midudev/autoskills",                     "39ce7120-0b06-466b-9995-60e377a1755a"),
    ("op7418/logo-generator-skill",             "c1893eb6-35f8-49b2-bce1-44210b3e19ee"),
    ("LichAmnesia/lich-skills",                 "ecca2d0c-2ac2-47bf-8734-ef5c424e8541"),
    ("robonuggets/marp-slides",                 "ff5f20b8-7d59-4a99-85f6-f33d8c4bbdca"),
    ("AMAP-ML/SkillClaw",                      "80f23186-2e0c-4d3a-ab75-79d948a78b3e"),
    ("agi-now/buffett-skills",                  "d43e6d33-f525-4e6e-9961-8a2bfbcedf57"),
    ("poteto/how",                              "c98c8641-3897-4ee1-8a77-71c5864ed6c6"),
    ("WoJiSama/skill-based-architecture",      "c67234eb-a32a-41f6-bf5f-fee11a25af77"),
    ("maiobarbero/my-ai-workflow",              "936448f5-643c-41f9-b413-8e9c1d627cb5"),
    ("yamadashy/repomix",                      "fecc09da-98a0-4da5-96de-840cd4aa592d"),
]

SCRIPT = Path("P:/") / ".claude/skills/gitingest/scripts/gitingest_runner.py"
STAGING = Path("P:/") / ".staging"


def main() -> None:
    import yaml

    total = len(REPOS)
    for idx, (repo_name, nb_id) in enumerate(REPOS, 1):
        print(f"\n{'=' * 60}\n=== [{idx}/{total}] {repo_name} ===\n{'=' * 60}")

        config = {
            "notebooklm_id": nb_id,
            "repos": [{"url": f"https://github.com/{repo_name}"}],
        }
        tmp_path = STAGING / f"repo-{repo_name.replace('/', '_')}.yaml"
        with open(tmp_path, "w") as f:
            yaml.dump(config, f)

        result = subprocess.run(
            ["python", str(SCRIPT), "--config", str(tmp_path)],
            cwd="P:/",
        )
        tmp_path.unlink(missing_ok=True)

        if result.returncode != 0:
            print(f"FAILED: {repo_name} (exit {result.returncode})")
        else:
            print(f"OK: {repo_name}")


if __name__ == "__main__":
    main()
