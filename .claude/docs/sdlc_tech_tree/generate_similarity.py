import json
import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import glob

# Paths
BASE_DIR = r"P:/.claude/docs/sdlc_tech_tree"
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILLS_DIR = r"P:/.claude/skills"
OUTPUT_FILE = os.path.join(DATA_DIR, "similarity.js")

def load_js_object(filepath, var_name):
    """
    Crude parser to extract JSON from a JS assignment like 'window.VAR = { ... };'
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to find the object start
    # specific to the known format: window.VAR = { ...
    pattern = re.compile(rf"window\.{var_name}\s*=\s*(.*)", re.DOTALL)
    match = pattern.search(content)
    
    if not match:
        raise ValueError(f"Could not find window.{var_name} in {filepath}")
        
    json_str = match.group(1).strip()
    
    # Remove trailing semicolon if present
    if json_str.endswith(';'):
        json_str = json_str[:-1]
        
    # The file might contain comments or trailing commas which standard JSON doesn't like.
    # However, based on previous file reads, tech_data.js is generated with json.dumps, so it should be clean.
    # metadata.js might be messier.
    # We'll try standard loading first.
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If standard load fails, we might need a more robust parser or just 'eval' it (unsafe but effectively we are trusted)
        # or use a js parser. But for now let's hope it's clean enough or try to clean comments.
        # Simple comment stripper:
        json_str = re.sub(r'//.*', '', json_str)
        return json.loads(json_str)

def get_skill_content(skill_name):
    """
    Reads the SKILL.md content for a given skill.
    """
    # Skill names in tech_data usually match the directory name in skills/
    # tech_data has names like "plan", skills dir has "plan/SKILL.md"
    
    # strip leading / if present
    clean_name = skill_name.lstrip('/')
    
    # Special handling for @agent names if they exist as folders (unlikely based on ls output)
    # But let's check exact match first
    skill_path = os.path.join(SKILLS_DIR, clean_name, "SKILL.md")
    
    if os.path.exists(skill_path):
        with open(skill_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
            
    return ""

def main():
    print("Loading data...")
    tech_data = load_js_object(os.path.join(DATA_DIR, "tech_data.js"), "TECH_DATA")
    
    # We might not strictly need metadata.js if we iterate through tech_data, 
    # but it has descriptions which are useful text features.
    # metadata.js might be harder to parse due to hand-editing. 
    # Let's try to just use tech_data structure to get the ID list, 
    # and maybe try to parse metadata.js if possible, or skip it if too hard.
    # Actually, looking at file view earlier, metadata.js looked like valid JS object but maybe not strict JSON 
    # (keys might not be quoted? no, they were quoted in line 4: "/learn").
    # But it had comments.
    
    try:
        metadata = load_js_object(os.path.join(DATA_DIR, "metadata.js"), "COMMAND_METADATA")
    except Exception as e:
        print(f"Warning: Could not parse metadata.js fully: {e}. Proceeding with sparse metadata.")
        metadata = {}

    # Collect all items
    items = []
    
    # Iterate through tech_data branches
    for branch, branch_data in tech_data.items():
        if "skills" in branch_data:
            for skill in branch_data["skills"]:
                # Skill IDs in tech_data.js seem to be stripped of leading slash in the "skills" array?
                # line 109 of update_tech_data_final.py: skills = [item.lstrip('/') for item in all_items]
                # So they are "plan", "test". 
                # But in metadata.js they are "/plan".
                # Let's standardize on the ID with Slash for consistency with UI which usually uses the ID.
                # Actually earlier UI code uses what? 
                # visual: tech_data.js lists them as strings. 
                # Let's assume the ID is the string with Slash if it's a command, or @ if agent.
                
                # Wait, "skills" list in tech_data.js are just names. "bullets" has the slashes.
                # Let's use "bullets" to get the full IDs.
                pass
                
        if "bullets" in branch_data:
            for item_id in branch_data["bullets"]:
                items.append(item_id)

    # Agents are also in tech_data?
    # line 221: "agents": [] - seems empty in the file dump I saw?
    # But metadata.js has AGENT_METADATA.
    # Let's check metadata.js for AGENT_METADATA if we can parse it.
    
    # Deduplicate
    items = sorted(list(set(items)))
    
    print(f"Found {len(items)} primitives.")
    
    documents = []
    valid_items = []
    
    for item_id in items:
        text_parts = []
        
        # Add ID itself (semantic value?)
        text_parts.append(item_id.replace('/', ' ').replace('-', ' '))
        
        # From Metadata
        if item_id in metadata:
            meta = metadata[item_id]
            if "desc" in meta:
                text_parts.append(meta["desc"])
            if "usage" in meta:
                text_parts.append(meta["usage"])
            if "whenToUse" in meta:
                text_parts.append(meta["whenToUse"])
            # richCard title/summary
            if "richCard" in meta:
                rc = meta["richCard"]
                if "title" in rc: text_parts.append(rc["title"])
                if "summary" in rc: text_parts.append(rc["summary"])
        
        # From SKILL.md
        # item_id is like "/plan", skill dir is "plan"
        skill_content = get_skill_content(item_id)
        if skill_content:
            text_parts.append(skill_content)
            
        full_text = " ".join(text_parts)
        
        # Only include if we have some text
        if len(full_text.strip()) > 0:
            documents.append(full_text)
            valid_items.append(item_id)
            
    print(f"Processing {len(documents)} documents with content.")
    
    # TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english', min_df=1)
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Cosine Similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Build result dict
    similarity_data = {}
    
    for idx, item_id in enumerate(valid_items):
        # Get scores
        sim_scores = list(enumerate(cosine_sim[idx]))
        
        # Sort by score desc
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top 21 (including self) -> top 20 others
        # Filter out self (score ~1.0)
        top_matches = []
        for i, score in sim_scores:
            if i == idx:
                continue # Skip self
            
            other_id = valid_items[i]
            # Convert float32 to float for json serialization
            top_matches.append({
                "id": other_id, 
                "score": round(float(score), 4)
            })
            
            if len(top_matches) >= 20:
                break
        
        similarity_data[item_id] = top_matches
        
    # Output
    print(f"Writing results to {OUTPUT_FILE}...")
    
    js_output = f"window.SIMILARITY_DATA = {json.dumps(similarity_data, indent=2)};"
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_output)
        
    print("Done.")

if __name__ == "__main__":
    main()
