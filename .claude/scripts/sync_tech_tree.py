import os
import re
import json
from datetime import datetime

# Paths
BASE_DIR = r"p:\.claude"
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
UNIFIED_INDEX = os.path.join(BASE_DIR, "UNIFIED_INDEX.md")
TECH_TREE_HTML = os.path.join(BASE_DIR, "docs", "sdlc_tech_tree.html")

def parse_markdown_metadata(file_path):
    """Simple parser for markdown headers and frontmatter."""
    metadata = {"name": os.path.splitext(os.path.basename(file_path))[0], "desc": "", "capabilities": []}
    if not os.path.exists(file_path):
        return metadata
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract Title/Name
    title_match = re.search(r'^# (.*)$', content, re.MULTILINE)
    if title_match:
        metadata["label"] = title_match.group(1).strip()
        
    # Extract Description (first paragraph after title)
    desc_match = re.search(r'^# .*?\n\n(.*?)\n', content, re.DOTALL)
    if desc_match:
        metadata["desc"] = desc_match.group(1).strip().replace('\n', ' ')

    # Extract Capabilities list
    cap_section = re.search(r'## Capabilities\n(.*?)(?=\n##|$)', content, re.DOTALL)
    if cap_section:
        caps = re.findall(r'[-*] (.*)', cap_section.group(1))
        metadata["capabilities"] = [c.strip() for c in caps]
        
    return metadata

def get_skills_from_index():
    """Parses UNIFIED_INDEX.md to get categorized skills."""
    skills_by_phase = {
        "strategy": [],
        "execution": [],
        "quality": [],
        "evolution": [],
        "control": []
    }
    
    if not os.path.exists(UNIFIED_INDEX):
        return skills_by_phase

    mapping = {
        "Strategy": "strategy",
        "Analysis": "quality",
        "Debug": "quality",
        "Development": "execution",
        "Evolution": "evolution",
        "Test": "quality",
        "Testing": "quality",
        "Testing-Workflow": "quality",
        "Control": "control"
    }

    current_phase = None
    with open(UNIFIED_INDEX, 'r', encoding='utf-8') as f:
        for line in f:
            header_match = re.match(r'^## (.*) \(', line)
            if header_match:
                section = header_match.group(1).strip()
                current_phase = mapping.get(section, None)
                continue
            
            if current_phase and "|" in line and line.count("|") >= 3:
                name_match = re.search(r'`/(.*?)`', line)
                if name_match:
                    skills_by_phase[current_phase].append("/" + name_match.group(1))
                    
    return skills_by_phase

def sync():
    print(f"[{datetime.now().isoformat()}] Starting Sync...")
    
    # 1. Get Agents
    agents_metadata = {}
    for f in os.listdir(AGENTS_DIR):
        if f.endswith(".md") and not f.startswith("_"):
            meta = parse_markdown_metadata(os.path.join(AGENTS_DIR, f))
            agents_metadata["@" + meta["name"]] = {
                "role": meta.get("label", meta["name"]),
                "desc": meta["desc"],
                "capabilities": meta["capabilities"]
            }
    
    # 2. Get Skills from Index
    skills_data = get_skills_from_index()
    
    # 3. Build TECH_DATA Structure
    # We maintain the existing manual categorization but augment with disc discovery
    # In a real tool, we might want a config file for phase mapping.
    
    # Load current file to preserve color/icon/labels
    with open(TECH_TREE_HTML, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Regex to find existing TECH_DATA to extract phase configs (colors/icons)
    tech_data_match = re.search(r'const TECH_DATA = (\{.*?\});', html_content, re.DOTALL)
    if not tech_data_match:
        print("Error: Could not find TECH_DATA block in HTML.")
        return

    current_tech_data = json.loads(tech_data_match.group(1).replace("'", '"')) # Basic normalization
    
    # Update bullets with discovered agents and skills
    for phase, data in current_tech_data.items():
        discovered_skills = skills_data.get(phase, [])
        # Find agents for this phase (this part is tricky without a mapping, 
        # for now we'll keep existing but ensure they exist on HDD)
        
        # Merge: Remove duplicates, keep existing order as base
        existing_bullets = set(data.get("bullets", []))
        all_phase_items = list(existing_bullets.union(set(discovered_skills)))
        
        # Sort reasonably: Agents first (@), then Commands (/)
        all_phase_items.sort(key=lambda x: (not x.startswith('@'), x))
        
        data["bullets"] = all_phase_items
        data["skills"] = [s.replace("/", "") for s in discovered_skills]
        data["agents"] = [a for a in all_phase_items if a.startswith("@")]

    # 4. Generate New Blocks
    new_tech_data_json = json.dumps(current_tech_data, indent=12)
    # Fix the trailing comma/format to match JS style a bit better
    new_tech_data_json = "const TECH_DATA = " + new_tech_data_json + ";"
    
    # 5. Inject into HTML
    start_marker = "// BEGIN AUTO-GENERATED TECH_DATA"
    end_marker = "// END AUTO-GENERATED TECH_DATA"
    
    pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
    new_block = f"{start_marker}\n        {new_tech_data_json}\n        {end_marker}"
    
    updated_html = pattern.sub(new_block, html_content)
    
    with open(TECH_TREE_HTML, 'w', encoding='utf-8') as f:
        f.write(updated_html)
        
    print(f"[{datetime.now().isoformat()}] Sync Complete. Updated {TECH_TREE_HTML}")

if __name__ == "__main__":
    sync()
