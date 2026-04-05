
import json

# Metadata
META = {
    "strategy": {"label": "Strategy (Discover & Plan)", "icon": "compass", "color": "indigo"},
    "execution": {"label": "Execution (Act & TDD)", "icon": "hammer", "color": "blue"},
    "control": {"label": "Control (The Human)", "icon": "cpu", "color": "rose"},
    "quality": {"label": "Quality (Verify)", "icon": "shield-check", "color": "emerald"},
}

# Refined Structure with Canonical Homes
STRUCTURE = {
    "strategy": {
        "Initialization/Setup": [
            "/init", "/session", "/llm-models", "/health-monitor", "/telemetry", 
            "/llm-health", "/perf", "/quota", "/context-status", "/deps", 
            "/library-first", "/pwsh", "/q"
        ],
        "Knowledge & Context": [
            "/triage", "/search", "/research", "/discover", "/discovery", "/explore",
            "/cks", "/cks-usage", "/chs", "/notebooklm",
            "/progressive-search", "/crawl", "/recent", "/query_alias",
            "/memory-integration", "/read-before-write", 
            "/session-awareness", "/sharing-skills", "/writing-skills", "/timeline",
            "/solo-dev-authority", "/scratchpad", "/hod"
        ],
        "Planning/Analysis": [
            "/breakdown", "/breakdown-task", "/docs", "/reports", "/wo-advisory",
            "/sequential-thinking", 
            "/problem-statement", "/value", "/think", "/val", "/analytics", 
            "/memory-system"
        ],
        "Design & Architecture": [
            "/arch", "/acef", "/csaf", "/cognitive-frameworks", "/constitutional-patterns", 
            "/prd", "/specify", "/design", "/ddd", "/architecture-decision-framework", 
            "/prd", "/specify", "/design", "/ddd", "/architecture-decision-framework", 
            "/prd", "/specify", "/design", "/ddd", "/architecture-decision-framework", 
            "/ocpa", "/agentic-validation", "/arch-v2", "/rca", "/rca-old"
        ]
    },
    "execution": {
        "Development": [
            "/build", "/code-python-2025", "/code-typescript-2025", "/refactor", 
            "/tdd", "/subagent-first", "/multi-file-refactor", "/command-create", 
            "/command-enhance", "/doc-to-skill", "/ai_distiller", "/complexity", 
            "/exec", "/execution-clarity", "/web-artifacts-builder", "/sar-inst",
            "/rich-skill", "/disler-start", "/disler-stop", "/multi-instance-coherence",
            "/bug-hunt", "/cco", "/fix"
        ],
        "Git & VCS": [
            "/git", "/commit", "/push", "/git-safety", "/git-worktrees", 
            "/git-conventional-commits", "/git-sapling", "/git-sync"
        ],
        "Automation & Tracking": [
            "/artifact", "/artifact-add", "/artifact-audit", "/artifact_done",
            "/write-file", "/ask", "/bgkill", "/data-processor", "/data-processor-v2",
            "/debug", "/debug-old"
        ]
    },
    "control": {
        "Control Branch": [
           "/workflow", "/orchestrate", # HUBS
           "/task", "/tm", "/cb", 
           "/constraints", "/hooks-edit", "/artifact", 
           "/artifact-add", "/artifact_audit", "/artifact_done",
           "/cgate", "/quadlet", "/step_6_5", "/flow", "/sap", "/sap_commit",
           "/consult", "/llm_edit_coordination", "/main", "/search_more",
           "/clear_notifications", "/clear_restore", "/restore", "/cwo", "/cwo_orchestrator"
        ]
    },
    "quality": {
        "Testing & QA": [
            "/test", "/tdd-cycle", "/qa", "/test-bisect", "/testing-skills",
            "/integration-test-phase2", "/verify"
        ],
        "Review & Audit": [
            "/analysis-audit", "/analysis-logs", "/analysis-profile", "/diffbro", 
            "/p2", "/p3", "/llm-doc_review", "/validate_spec", "/validate-safety-patterns",
            "/comply", "/standards", "/prrp", "/truth", "/slc", "/llm-review",
            "/catchup", "/session-handoff", "/r", "/ralph"
        ],
        "Advanced Analysis": [
            "/debug", "/analyze", "/rca", "/obs", "/investigate", "/nse", 
            "/session-transcript-w1t2", "/apply_safety_patterns", "/llm-debate"
        ],
        "Modernization": [
            "/learn", "/reflect", "/retro", "/cleanup", "/evolve", 
            "/update_state", "/r", "/sp", "/skills_migrate", "/value-maximization"
        ]
    }
}

# Generate the JS object
data = {}

for branch, categories in STRUCTURE.items():
    meta = META[branch]
    
    # Flatten items for bullets and skills
    all_items = []
    for cat_items in categories.values():
        all_items.extend(cat_items)
    
    # Deduplicate
    all_items = sorted(list(set(all_items)))
    
    # Skills (remove leading /)
    skills = [item.lstrip('/') for item in all_items]
    
    data[branch] = {
        "label": meta["label"],
        "icon": meta["icon"],
        "color": meta["color"],
        "commands": [],
        "categories": categories,
        "bullets": all_items,
        "skills": skills,
        "agents": []
    }

# Write to file
js_content = "window.TECH_DATA = " + json.dumps(data, indent=4) + ";"

with open(r"P:/.claude/docs/sdlc_tech_tree/data/tech_data.js", "w", encoding="utf-8") as f:
    f.write("// Auto-generated by update_tech_data_final.py\n")
    f.write(js_content)

print("Updated tech_data.js with Consolidated Primitives")
