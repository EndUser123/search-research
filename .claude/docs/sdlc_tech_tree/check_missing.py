
import os
import json
import re

SKILLS_DIR = r"P:/.claude/skills"
TECH_DATA_FILE = r"P:/.claude/docs/sdlc_tech_tree/data/tech_data.js"

with open(TECH_DATA_FILE, 'r', encoding='utf-8') as f:
    content = f.read()
    json_match = re.search(r'window\.TECH_DATA = (\{.*\});', content, re.DOTALL)
    tech_data = json.loads(json_match.group(1))

tree_skills = set()
for branch in tech_data.values():
    tree_skills.update(branch.get('skills', []))

dir_skills = []
for d in os.listdir(SKILLS_DIR):
    if os.path.isdir(os.path.join(SKILLS_DIR, d)):
        if not d.startswith('_') and not d.startswith('.'):
            dir_skills.append(d)

missing = []
for d in dir_skills:
    # Check for direct match or variations (underscore/hyphen)
    match_found = False
    variations = [d, d.replace('-', '_'), d.replace('_', '-')]
    for v in variations:
        if v.lstrip('/') in tree_skills:
            match_found = True
            break
    
    # Manual mappings from extract_skills.py
    MAPPING = {
        "agent-orchestrator": "orchestrate",
        "cognitive-stack": "cognitive",
        "memory-system": "memory",
        "session-awareness": "session",
        "aid": "ai_distiller",
        "llm-doc_review": "llm_doc_review"
    }
    if MAPPING.get(d) in tree_skills:
        match_found = True

    if not match_found:
        missing.append(d)

print(f"Total skills in directory: {len(dir_skills)}")
print(f"Total skills in tree: {len(tree_skills)}")
print("\nSkills in directory but NOT in tree:")
for m in sorted(missing):
    print(f"- {m}")
