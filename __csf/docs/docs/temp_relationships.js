const RELATIONSHIPS = {
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
            "bottleneck detection",
            "profiling",
            "latency analysis"
        ]
    },
    "/design": {
        "next": [
            "/specify",
            "/architecture",
            "/planning"
        ],
        "prev": [
            "/discover",
            "/research",
            "/brainstorm"
        ],
        "capabilities": [
            "system design",
            "component architecture",
            "interface design"
        ]
    },
    "/research": {
        "next": [
            "/planning",
            "/design",
            "/architect"
        ],
        "prev": [
            "/init"
        ],
        "capabilities": [
            "codebase discovery",
            "architecture analysis",
            "pattern discovery",
            "technical debt analysis",
            "semantic code search",
            "research"
        ]
    },
    "/implement": {
        "next": [
            "/test",
            "/verify",
            "/debug"
        ],
        "prev": [
            "/planning",
            "/tdd",
            "/design"
        ],
        "capabilities": [
            "code generation",
            "implementation",
            "coding"
        ]
    },
    "/planning": {
        "next": [
            "/implement",
            "/tdd",
            "/test"
        ],
        "prev": [
            "/design",
            "/architecture",
            "/specify"
        ],
        "capabilities": [
            "planning",
            "task breakdown",
            "roadmap creation"
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
    }
};