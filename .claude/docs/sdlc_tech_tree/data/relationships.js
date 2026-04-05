// Auto-extracted data

        window.RELATIONSHIPS = {
    "/analytics": {
        "next": [
            "/refactor",
            "/optimize",
            "/fix"
        ],
        "prev": [
            "/test",
            "/verify",
            "/benchmark"
        ],
        "capabilities": [
            "performance analysis",
            "metric tracking",
            "insight generation"
        ]
    },
    "@csf-nip-planning-command": {
        "next": [
            "/plan",
            "@architect"
        ],
        "prev": [
            "/brainstorm",
            "/research"
        ],
        "capabilities": [
            "planning synthesis",
            "protocol alignment",
            "strategic mapping"
        ]
    },
    "@architect": {
        "next": [
            "/design",
            "/arch",
            "/plan"
        ],
        "prev": [
            "/brainstorm",
            "/research",
            "/prd"
        ]
    },
    "/brainstorm": {
        "prev": ["/init", "/triage"],
        "next": ["/research", "/plan", "@product-manager"]
    },
    "/research": {
        "prev": ["/brainstorm"],
        "next": ["/plan", "/docs", "@researcher"]
    },
    "/plan": {
        "prev": ["/research", "/brainstorm"],
        "next": ["/arch", "/design", "@architect"]
    },
    "/design": {
        "prev": ["/plan", "/arch"],
        "next": ["/spec", "@ui-ux-expert"]
    },
    "/build": {
        "prev": ["/spec", "/design"],
        "next": ["/test", "/git", "@api-builder"]
    },
    "/test": {
        "prev": ["/build"],
        "next": ["/debug", "/verify", "@qa-engineer"]
    },
    "/git": {
        "prev": ["/build", "/test"],
        "next": ["/push", "@smart_git_commit"]
    },

    "/implement": {
        "next": [
            "/test",
            "/verify",
            "/debug"
        ],
        "prev": [
            "/plan",
            "/tdd",
            "/design"
        ],
        "capabilities": [
            "code generation",
            "implementation",
            "coding"
        ]
    },

    "/tdd": {
        "next": [
            "/implement",
            "/refactor",
            "/verify"
        ],
        "prev": [
            "/implement",
            "/fix",
            "/debug"
        ],
        "capabilities": [
            "test generation",
            "test execution",
            "refactoring",
            "verification"
        ]
    },
    "@product-manager": {
        "prev": ["/brainstorm", "/triage"],
        "next": ["/prd", "/specify", "/plan"],
        "capabilities": ["requirements", "roadmap", "prioritization"]
    },
    "@python-core": {
        "prev": ["/plan", "/specify"],
        "next": ["/code-python-2025", "/tdd", "/implement"],
        "capabilities": ["backend", "api", "typing"]
    },
    "@csf-nip-development": {
        "prev": ["/architecture", "/design"],
        "next": ["/csf-nip-integration", "/scaffold"],
        "capabilities": ["framework", "patterns", "integration"]
    },
    "@deepgit": {
        "prev": ["/git-safety", "/merge-conflict"],
        "next": ["/git-sapling", "/clean"],
        "capabilities": ["git-ops", "history", "recovery"]
    },
    "@smart_git_commit": {
        "prev": ["/artifact-done", "/diff"],
        "next": ["/commit", "/push"],
        "capabilities": ["semantic-commits", "convention", "summarization"]
    },
    "@qa-engineer": {
        "prev": ["/implement", "/build"],
        "next": ["/verify", "/test", "/certify"],
        "capabilities": ["testing", "quality", "automation"]
    },
    "@code-critic": {
        "prev": ["/pull-request", "/refactor"],
        "next": ["/lint", "/style-check"],
        "capabilities": ["review", "static-analysis", "best-practices"]
    },
    "@rca-specialist": {
        "prev": ["/failure", "/bug-report"],
        "next": ["/investigate", "/fix", "/test-bisect"],
        "capabilities": ["debugging", "root-cause", "analysis"]
    },
    "@rca-learning-specialist": {
        "prev": ["/rca", "/post-mortem"],
        "next": ["/knowledge-base", "/pattern-update"],
        "capabilities": ["learning", "distillation", "prevention"]
    },
    "@rca-verification-specialist": {
        "prev": ["/fix", "/patch"],
        "next": ["/verify", "/regression-test"],
        "capabilities": ["verification", "reproduction", "validation"]
    },
    "@every-style-editor": {
        "prev": ["/save", "/commit-hook"],
        "next": ["/format", "/prettify"],
        "capabilities": ["formatting", "style", "consistency"]
    },
    "@csf-nip-orchestration": {
        "prev": ["/session-start", "/trigger"],
        "next": ["/delegate", "/context-sync"],
        "capabilities": ["orchestration", "coordination", "context"]
    },
    "@csf-nip-knowledge": { "prev": ["/ingest", "/docs"], "next": ["/search", "/rag"], "capabilities": ["knowledge", "retrieval", "context"] },
    "@csf-sr-architecture-solid-principles": { "prev": ["/design", "/refactor"], "next": ["/lint", "/review"], "capabilities": ["solid", "design", "principles"] },
    "@csf-sr-explainable-reasoning": { "prev": ["/think", "/plan"], "next": ["/log", "/trace"], "capabilities": ["reasoning", "explainability", "transparency"] },
    "@csf-sr-optimization-strategy": { "prev": ["/analyze", "/profile"], "next": ["/optimize", "/refactor"], "capabilities": ["optimization", "performance", "efficiency"] },
    "@graphql-architect": { "prev": ["/api-design", "/schema"], "next": ["/codegen", "/mock"], "capabilities": ["graphql", "schema", "api"] },
    "@prompt-architect": { "prev": ["/task", "/user-request"], "next": ["/prompt", "/context"], "capabilities": ["prompt-engineering", "optimization", "context"] },
    "@quant-analyst": { "prev": ["/data", "/metrics"], "next": ["/report", "/visualize"], "capabilities": ["analysis", "metrics", "quant"] },
    "@rag-architect": { "prev": ["/query", "/search"], "next": ["/context", "/answer"], "capabilities": ["rag", "retrieval", "vector"] },
    "@researcher": { "prev": ["/question", "/unknown"], "next": ["/answer", "/report"], "capabilities": ["research", "investigation", "synthesis"] },
    "@vector-db-expert": { "prev": ["/embedding", "/index"], "next": ["/search", "/retrieve"], "capabilities": ["vector-db", "embeddings", "search"] },
    
    "@api-builder": { "prev": ["/spec", "/design"], "next": ["/implement", "/test"], "capabilities": ["api", "rest", "graphql"] },
    "@csf-sr-framework-react-hooks": { "prev": ["/react", "/logic"], "next": ["/hook", "/component"], "capabilities": ["react", "hooks", "framework"] },
    "@python-web": { "prev": ["/flask", "/django"], "next": ["/route", "/middleware"], "capabilities": ["python", "web", "backend"] },
    "@react-specialist": { "prev": ["/design", "/mockup"], "next": ["/component", "/page"], "capabilities": ["react", "frontend", "ui"] },
    "@tdd-implementer": { "prev": ["/test-fail", "/spec"], "next": ["/code-pass", "/implement"], "capabilities": ["tdd", "implementation", "testing"] },
    "@tdd-refactorer": { "prev": ["/code-pass", "/smell"], "next": ["/refactor", "/optimize"], "capabilities": ["refactoring", "cleanup", "quality"] },
    "@tdd-test-writer": { "prev": ["/requirement", "/bug"], "next": ["/test-fail", "/coverage"], "capabilities": ["testing", "tdd", "quality"] },
    "@ui-ux-expert": { "prev": ["/wireframe", "/user-story"], "next": ["/design", "/prototype"], "capabilities": ["ui", "ux", "design"] },

    "@csf-nip-constitution-specialist": { "prev": ["/policy", "/check"], "next": ["/enforce", "/report"], "capabilities": ["constitution", "safety", "alignment"] },
    "@csf-nip-quality": { "prev": ["/code", "/process"], "next": ["/audit", "/certify"], "capabilities": ["quality", "standards", "process"] },
    "@csf-nip-security": { "prev": ["/audit", "/scan"], "next": ["/report", "/harden"], "capabilities": ["security", "audit", "hardening"] },
    "@csf-sr-multimodal-analysis": { "prev": ["/image", "/video"], "next": ["/analyze", "/describe"], "capabilities": ["multimodal", "analysis", "vision"] },
    "@csf-sr-risk-assessment": { "prev": ["/plan", "/change"], "next": ["/assess", "/mitigate"], "capabilities": ["risk", "assessment", "security"] },
    "@csf-sr-temporal-analysis": { "prev": ["/timeline", "/history"], "next": ["/pattern", "/prediction"], "capabilities": ["temporal", "time-series", "analysis"] },
    "@risk-manager": { "prev": ["/project", "/decision"], "next": ["/assess", "/approve"], "capabilities": ["risk", "management", "strategy"] },

    "@chaos-engineer": { "prev": ["/stable", "/deploy"], "next": ["/attack", "/monitor"], "capabilities": ["chaos", "resilience", "testing"] },
    "@csf-sr-adaptive-learning": { "prev": ["/feedback", "/error"], "next": ["/adapt", "/improve"], "capabilities": ["learning", "adaptation", "feedback"] },
    "@ml-engineer": { "prev": ["/data", "/model"], "next": ["/train", "/deploy"], "capabilities": ["ml", "ai", "engineering"] },
    "@mlops-engineer": { "prev": ["/model", "/pipeline"], "next": ["/deploy", "/monitor"], "capabilities": ["mlops", "deployment", "infrastructure"] },

    "@context-manager": { "prev": ["/history", "/token"], "next": ["/prune", "/optimize"], "capabilities": ["context", "memory", "tokens"] },
    "@csf-nip-infrastructure": { "prev": ["/config", "/env"], "next": ["/provision", "/scale"], "capabilities": ["infrastructure", "ops", "system"] },
    "@csf-sr-cognitive-integration": { "prev": ["/think", "/reason"], "next": ["/integrate", "/act"], "capabilities": ["cognitive", "integration", "reasoning"] },
    "@csf-sr-monitoring-instrumentation": { "prev": ["/run", "/deploy"], "next": ["/monitor", "/alert"], "capabilities": ["monitoring", "metrics", "observability"] },
    "@csf-sr-predictive-analytics": { "prev": ["/history", "/trend"], "next": ["/predict", "/forecast"], "capabilities": ["predictive", "analytics", "forecasting"] },
    "@n8n-expert": { "prev": ["/trigger", "/webhook"], "next": ["/workflow", "/action"], "capabilities": ["n8n", "automation", "workflow"] },

    // QUALITY BRANCH PROGRESSION
    "@csf-nip-quality": { "prev": ["/implement", "/build"], "next": ["@csf-nip-security", "/library-first"], "capabilities": ["standards", "gatekeeping"] },
    "/library-first": { "prev": ["@csf-nip-quality"], "next": ["/truth"], "capabilities": ["reuse", "efficiency"] },
    "@csf-nip-security": { "prev": ["@csf-nip-quality"], "next": ["/qa", "/nse"], "capabilities": ["security", "risk"] },
    "/qa": { "prev": ["@csf-nip-security", "/build"], "next": ["/artifact-audit", "@rca-specialist"], "capabilities": ["verification", "certification"] },
    "/artifact-audit": { "prev": ["/qa"], "next": ["/release"], "capabilities": ["audit", "compliance"] },
    "@rca-specialist": { "prev": ["/qa", "/debug"], "next": ["/fix", "/test-bisect"], "capabilities": ["rca", "forensics"] },
    "/debug": { "prev": ["/verify"], "next": ["/rca", "/log"], "capabilities": ["debugging", "inspection"] }
};


window.ONBOARDING_STAGES = [
    {
        id: 'mindset',
        title: 'Agentic Concepts',
        description: 'Understand how agents differ from standard tools. Agents analyze context and propose plans rather than just executing static commands.',
        icon: 'brain',
        tasks: [
            { id: 'm1', text: 'Read the Agentic Design summary.', type: 'concept' },
            { id: 'm2', text: 'Learn how to provide file context using --context.', type: 'concept' }
        ],
        proTips: [
            "Agents work best when you provide specific file targets or narrow search queries."
        ],
        linkedItems: ['@product-manager', '@architect']
    },
    {
        id: 'workbench',
        title: 'Core CLI Tools',
        description: 'Explore and plan your work using the primary CLI commands.',
        icon: 'terminal',
        tasks: [
            { id: 'w1', text: 'Initiate a brainstorming session.', command: '/brainstorm' },
            { id: 'w2', text: 'Search the codebase for specific patterns.', command: '/research' },
            { id: 'w3', text: 'Generate a step-by-step implementation plan.', command: '/plan' }
        ],
        proTips: [
            "Use /research to find implementation examples before writing new code."
        ],
        linkedItems: ['/brainstorm', '/research', '/plan', '/arch']
    },
    {
        id: 'council',
        title: 'Agent Coordination',
        description: 'Direct specialized agents to handle complex tasks or review your work.',
        icon: 'users',
        tasks: [
            { id: 'c1', text: 'Ask the Architect to review your logic.', command: '/arch' },
            { id: 'c2', text: 'Have the QA Engineer check your implementation.', command: '/verify' }
        ],
        proTips: [
            "You can ask an agent to critique another agent's output for higher accuracy."
        ],
        linkedItems: ['@architect', '@qa-engineer', '/verify']
    },
    {
        id: 'shipping',
        title: 'Safety & Quality',
        description: 'Verify your work against project standards and commit with clear history.',
        icon: 'ship',
        tasks: [
            { id: 's1', text: 'Run final quality and compliance checks.', command: '/verify' },
            { id: 's2', text: 'Generate a semantic git commit.', command: '/git' }
        ],
        proTips: [
            "Always run /verify before pushing a PR to catch lint or logic issues."
        ],
        linkedItems: ['/verify', '/git', '@smart_git_commit']
    }
];


window.CLUSTERS = {
    "strategy": [
        {
            "hub": "/health-monitor",
            "satellites": [
                "/llm_health",
                "/telemetry",
                "/perf",
                "/quota",
                "/context_status"
            ],
            "tags": ["environment", "health", "telemetry"],
            "reason": "Centralized health and environment monitoring hub."
        },
        {
            "hub": "/design",
            "satellites": [
                "/specify",
                "/arch",
                "/plan",
                "/prd",
                "/triage",
                "/brainstorm",
                "@architect",
                "@product-manager",
                "/agentic-validation",
                "/arch-v2",
                "/rca"
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
                "@csf-nip-development",
                "/data-processor-v2",
                "/debug"
            ],
            "tags": ["implementation", "build", "code"],
            "reason": "The Implementer role should handle the atomic loop of building and artifacting."
        },
        {
            "hub": "/git",
            "satellites": [
                "/git-safety",
                "/git-worktrees",
                "/git-conventional-commits",
                "/git-sapling",
                "/commit",
                "/push"
            ],
            "tags": ["vcs", "git"],
            "reason": "The central git command hub."
        },
        {
            "hub": "/commit",
            "satellites": [
                "/sap",
                "/checkpoint",
                "@deepgit",
                "@smart_git_commit"
            ],
            "tags": ["persistence", "history"],
            "reason": "Persistence authority for saving state."
        }
    ],
    "control": [
        {
            "hub": "/orchestrate",
            "satellites": [
                "/quadlet",
                "/step_6_5",
                "/cwo",
                "/cwo_orchestrator"
            ],
            "tags": ["orchestration", "management"],
            "reason": "Central orchestration hub."
        },
        {
            "hub": "/workflow",
            "satellites": [
                "/flow",
                "/tm",
                "/catchup",
                "/retro",
                "@csf-nip-orchestration"
            ],
            "tags": ["workflow", "planning"],
            "reason": "Workflow management hub."
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
        },
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
    ]
};


