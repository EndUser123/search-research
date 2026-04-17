
# Script to read relationships.js and replace the CLUSTERS object
import re

SOURCE_FILE = r"P:/.claude/docs/sdlc_tech_tree/data/relationships.js"

NEW_CLUSTERS = """window.CLUSTERS = {
    "strategy": [
        {
            "hub": "/design",
            "satellites": [
                "/specify",
                "/arch",
                "/planning",
                "/prd",
                "/triage",
                "/brainstorm",
                "@architect",
                "@product-manager"
            ],
            "tags": ["design", "architecture", "planning"],
            "reason": "Synthesize all design roles and specs into the /design orchestration engine."
        }
    ],
    "execution": [
        {
            "hub": "/build",
            "satellites": [
                "/exec",
                "/artifact-add",
                "/artifact-done",
                "@python-core",
                "@csf-nip-development"
            ],
            "tags": ["implementation", "build", "code"],
            "reason": "The Implementer role should handle the atomic loop of building and artifacting."
        },
        {
            "hub": "/commit",
            "satellites": [
                "/git",
                "/sap",
                "/checkpoint",
                "@deepgit",
                "@smart_git_commit"
            ],
            "tags": ["vcs", "git", "persistence"],
            "reason": "All persistence should be handled by a single 'Save State' authority."
        }
    ],
    "quality": [
        {
            "hub": "@csf-nip-quality",
            "satellites": [
                "/library-first",
                "/truth",
                "/catchup",
                "/session-handoff",
                "@csf-nip-constitution-specialist"
            ],
            "tags": ["standards", "pre-flight", "constitution"],
            "reason": "Establishing standards and context is the first step of Quality."
        },
        {
            "hub": "@csf-nip-security",
            "satellites": [
                "/nse",
                "/analysis-audit",
                "/analytics",
                "@risk-manager",
                "@csf-sr-risk-assessment",
                "@csf-sr-multimodal-analysis"
            ],
            "tags": ["security", "audit", "risk"],
            "reason": "Security and deep analysis scans should run before or parallel to functional QA."
        },
        {
            "hub": "/qa",
            "satellites": [
                "/verify",
                "/testing-skills",
                "/artifact-audit",
                "/multi-instance-coherence",
                "@qa-engineer",
                "@code-critic"
            ],
            "tags": ["verification", "certification", "testing"],
            "reason": "The core functional verification and certification gate."
        },
        {
            "hub": "@rca-specialist",
            "satellites": [
                "/debug",
                "/rca",
                "/bug-hunt",
                "/investigate",
                "/analysis-logs",
                "/recent_chat_search",
                "/test-bisect",
                "@rca-learning-specialist"
            ],
            "tags": ["forensics", "debugging", "recovery"],
            "reason": "Deep dive investigation and root cause analysis for failures."
        }
    ],
    "evolution": [
        {
            "hub": "/evolve",
            "satellites": [
                "/refactor",
                "/cleanup",
                "/aid",
                "@every-style-editor"
            ],
            "tags": ["refactoring", "maintenance", "evolution"],
            "reason": "System-wide improvements should all stem from the /evolve command."
        }
    ],
    "control": [
        {
            "hub": "/cwo",
            "satellites": [
                "/tm",
                "/workflow",
                "/catchup",
                "/retro",
                "@csf-nip-orchestration"
            ],
            "tags": ["orchestration", "management", "workflow"],
            "reason": "Multi-agent management and session continuity belong in the /cwo hub."
        }
    ]
};"""

with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace existing CLUSTERS definition using regex
# Matches window.CLUSTERS = { ... };
# We use DOTALL to match newlines
new_content = re.sub(
    r'window\.CLUSTERS\s*=\s*{.*?};', 
    NEW_CLUSTERS, 
    content, 
    flags=re.DOTALL
)

with open(SOURCE_FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated CLUSTERS in relationships.js")
