const RELATIONSHIPS = {
    "/analytics": {
        "capabilities": [
            "system analytics and metrics collection\", \"performance monitoring and dashboard\", \"data querying and export\", \"health monitoring and status"
        ]
    },
    "/analyze": {
        "capabilities": [
            "code analysis",
            "pre-mortem analysis",
            "gap analysis",
            "opportunity identification",
            "quality assessment"
        ]
    },
    "/arch": {
        "next": [
            "/planning",
            "/exec"
        ],
        "prev": [
            "/architecture",
            "/design",
            "/structure"
        ]
    },
    "/bgkill": {
        "capabilities": [
            "background tasks",
            "zombie processes",
            "bgkill",
            "kill background",
            "zombie"
        ]
    },
    "/breakdown": {
        "capabilities": [
            "task breakdown",
            "implementation planning",
            "verification steps"
        ]
    },
    "/bug-hunt": {
        "capabilities": [
            "bug hunting",
            "bug finding",
            "bug fixing",
            "defensive programming",
            "type safety"
        ]
    },
    "/cb": {
        "capabilities": [
            "audit system",
            "govern command",
            "refactor architecture"
        ]
    },
    "/cgate": {
        "capabilities": [
            "consultation gateway",
            "cgate"
        ]
    },
    "/cognitive-stack": {
        "capabilities": [
            "cognitive stack management",
            "framework status",
            "system orchestration"
        ]
    },
    "/cognitive-stack-production": {
        "capabilities": [
            "cognitive stack production deployment",
            "system orchestration",
            "cognitive system management"
        ]
    },
    "/command-enhance": {
        "capabilities": [
            "Command enhancement",
            "MVP compliance upgrade",
            "Existing command migration",
            "Strategic gap analysis",
            "Performance optimization"
        ]
    },
    "/complexity": {
        "capabilities": [
            "code complexity",
            "cyclomatic complexity",
            "complex code",
            "refactoring candidates",
            "radon"
        ]
    },
    "/comply": {
        "capabilities": [
            "coding standards validation",
            "constitutional compliance checking (implemented code only)",
            "evidence-based compliance verification",
            "tree-level compliance validation",
            "solo developer compliance checking"
        ]
    },
    "/consult": {
        "capabilities": [
            "consult",
            "consultation",
            "advisory"
        ]
    },
    "/command-create": {
        "capabilities": [
            "command scaffolding",
            "MVP pattern generation",
            "CSF NIP command creation",
            "template generation"
        ]
    },
    "/data-processor": {
        "capabilities": [
            "custom operations",
            "template processing",
            "data processing"
        ]
    },
    "/ddd": {
        "capabilities": [
            "due diligence checklists",
            "comprehensive review questions",
            "quality assurance validation",
            "pre-deployment checks"
        ]
    },
    "/doc-to-skill": {
        "capabilities": [
            "documentation to skill conversion",
            "skill creation from docs",
            "automated skill generation",
            "doc scraping",
            "knowledge extraction"
        ]
    },
    "/dpef": {
        "capabilities": [
            "deterministic prompt execution framework",
            "command template generation",
            "metadata standard",
            "prompt spec generation",
            "quality validation"
        ]
    },
    "/exec": {
        "next": [
            "/truth",
            "/nse"
        ],
        "prev": [
            "/planning",
            "/implement",
            "/build",
            "/create"
        ]
    },
    "/flow": {
        "capabilities": [
            "orchestrate",
            "workflow",
            "pipeline",
            "sequence",
            "coordinate"
        ]
    },
    "/git": {
        "capabilities": [
            "git",
            "smart git",
            "smart_git",
            "smart git cli",
            "git worktree management"
        ]
    },
    "/learn": {
        "capabilities": [
            "learn from session",
            "session review",
            "lessons learned",
            "skill improvement",
            "knowledge promotion"
        ]
    },
    "/llm-codex": {
        "capabilities": [
            "codex cli",
            "codex analysis",
            "code generation",
            "codex"
        ]
    },
    "/llm-edit-coordination": {
        "capabilities": [
            "multi-LLM collaborative editing",
            "document conflict prevention",
            "coordinated section management",
            "atomic editing practices",
            "session recovery and backup"
        ]
    },
    "/llm-gemini": {
        "capabilities": [
            "gemini cli",
            "gemini analysis",
            "large context analysis",
            "gemini"
        ]
    },
    "/llm-health": {
        "capabilities": [
            "llm health",
            "provider health",
            "check provider",
            "health status"
        ]
    },
    "/llm-performance": {
        "capabilities": [
            "llm performance",
            "provider latency",
            "benchmark",
            "llm speed",
            "provider benchmark"
        ]
    },
    "/llm-qwen": {
        "capabilities": [
            "qwen cli",
            "qwen analysis",
            "large context analysis",
            "qwen"
        ]
    },
    "/main": {
        "capabilities": [
            "cognitive steering framework",
            "system initialization"
        ]
    },
    "/ocpa": {
        "capabilities": [
            "architectural validation",
            "completion path analysis",
            "decision optimization"
        ]
    },
    "/prd": {
        "capabilities": [
            "PRD import and task creation",
            "requirements traceability",
            "PRD completion tracking"
        ]
    },
    "/prrp": {
        "capabilities": [
            "production code review",
            "enterprise code analysis",
            "quality assurance validation",
            "constitutional compliance checking",
            "solo developer optimization"
        ]
    },
    "/quadlet": {
        "capabilities": [
            "atomic operations and task management\", \"quadlet creation and execution\", \"task orchestration with rollback\", \"workflow management and safety\", \"concurrent task execution"
        ]
    },
    "/query-alias": {
        "capabilities": [
            "knowledge base queries",
            "cks search",
            "pattern retrieval",
            "vector search"
        ]
    },
    "/quota": {
        "capabilities": [
            "check quota",
            "api quota",
            "credits",
            "quota status",
            "provider quota"
        ]
    },
    "/recent": {
        "capabilities": [
            "recent messages",
            "what happened recently",
            "last N minutes",
            "search recent chat"
        ]
    },
    "/reflect": {
        "capabilities": [
            "reflect",
            "improve skill",
            "learn from this",
            "skill reflection"
        ]
    },
    "/research": {
        "next": [
            "/planning",
            "/arch"
        ],
        "prev": [
            "/research",
            "/explore",
            "/investigate"
        ]
    },
    "/retro": {
        "capabilities": [
            "session review",
            "lessons learned",
            "skill update",
            "knowledge promotion",
            "retrospective analysis"
        ]
    },
    "/review-bundle": {
        "capabilities": [
            "review bundle creation",
            "context audit",
            "architectural review packaging"
        ]
    },
    "/sap": {
        "capabilities": [
            "sapling workflows",
            "git operations",
            "vcs efficiency"
        ]
    },
    "/sap-commit": {
        "capabilities": [
            "sapling atomic operations",
            "backup before risky operations",
            "version control safety",
            "atomic commits with rollback"
        ]
    },
    "/search": {
        "capabilities": [
            "unified search",
            "search everything",
            "search all backends",
            "query knowledge base"
        ]
    },
    "/slc": {
        "capabilities": [
            "solo dev guidelines",
            "pragmatic development",
            "lean development"
        ]
    },
    "/specify": {
        "next": [
            "/planning",
            "/arch"
        ],
        "prev": [
            "/new task",
            "/feature",
            "/project"
        ]
    },
    "/standards": {
        "capabilities": [
            "standards",
            "csf nip standards",
            "compliance",
            "policies"
        ]
    },
    "/tdd": {
        "capabilities": [
            "tdd on",
            "tdd off",
            "tdd approval",
            "tdd status",
            "reset tdd"
        ]
    },
    "/telemetry": {
        "capabilities": [
            "log event",
            "record outcome",
            "track metrics"
        ]
    },
    "/vta": {
        "capabilities": [
            "intent routing",
            "file analysis",
            "command discovery",
            "workflow orchestration"
        ]
    },
    "/wo-advisory": {
        "capabilities": [
            "complex multi-domain tasks requiring coordination",
            "tasks with security, performance, architecture expertise needs",
            "constitutional compliance requirements",
            "TDD methodology enforcement",
            "multi-agent coordination"
        ]
    }
};
