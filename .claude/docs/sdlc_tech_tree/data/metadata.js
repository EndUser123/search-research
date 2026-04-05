// Auto-extracted data

        window.COMMAND_METADATA = {
    "/learn": {
        "desc": "Central Hub for learning and retrospectives.",
        "usage": "/learn [insight]",
        "whenToUse": "Use to capture insights or run retrospectives.",
        "richCard": {
                "title": "Learning & Retro Hub",
                "summary": "Captures insights, failures, and success patterns. It ensures the system gets smarter over time by crystallizing 'lessons learned' into permanent skills.",
                "workflowPosition": "Evolution Branch > Learning Phase",
                "howToUse": [
                        {
                                "label": "Start Retro",
                                "cmd": "/retro"
                            },
                        {
                                "label": "Log Insight",
                                "cmd": "/learn 'New API pattern'"
                            },
                        {
                                "label": "Search Lessons",
                                "cmd": "/search --lessons"
                            }
                ]
            }
    },
    "/artifact": {
        "desc": "Manages project deliverables and outputs.",
        "usage": "/artifact [action]",
        "whenToUse": "Use to create, list, or audit official project artifacts.",
        "richCard": {
                "title": "Artifact Management Hub",
                "summary": "The central registry for all project deliverables (PRDs, Plans, Reports). Ensures every outputs is versioned, indexed, and accessible.",
                "workflowPosition": "Control Branch > Artifacts Phase",
                "howToUse": [
                        {
                                "label": "Create Artifact",
                                "cmd": "/artifact create"
                            },
                        {
                                "label": "List Artifacts",
                                "cmd": "/artifact list"
                            },
                        {
                                "label": "Audit",
                                "cmd": "/artifact_audit"
                            }
                ]
            }
    },
            "/brainstorm": { 
                usage: "/brainstorm [topic] --context [file]",
                desc: "Initiates a divergent thinking session to explore ideas."
            },
            "/research": { 
                usage: "/research [query] --depth [1-3]",
                desc: "Performs deep web research and improved HyDE query expansion."
            },
            "/plan": {
                usage: "/plan [goal] --breakdown",
                desc: "Generates a structured implementation plan."
            },
            "/arch": {
                usage: "/arch [component] --check-compliance",
                desc: "Invokes the Architect to review systemic design."
            },
            "/git": {
                usage: "/git [status|commit|push|log]",
                desc: "Wrapper for git operations with safety checks.",
                whenToUse: "Use for all VCS operations to ensure safety checks run.",
                richCard: {
                    title: "Git Version Control Hub",
                    summary: "A safe wrapper around standard Git commands. It enforces conventional commits, prevents accidental pushes to protected branches, and manages worktrees.",
                    workflowPosition: "Execution Branch > VCS Phase",
                    howToUse: [
                        { label: "View Status", cmd: "/git status" },
                        { label: "Smart Commit", cmd: "/git commit -m 'feat: add login'" },
                        { label: "Safe Push", cmd: "/git push" }
                    ]
                }
            },
            "/refactor": {
                usage: "/refactor [file] [instructions]",
                desc: "Applies sophisticated code modifications using AST awareness."
            },
            "/test": {
                usage: "/test [file] --watch",
                desc: "Runs test suites with output parsing.",
                whenToUse: "Use after making changes to verify correctness.",
                richCard: {
                    title: "Testing Hub",
                    summary: "The central command for all verification activities. It unifies unit tests, integration tests, and linting into a single interface.",
                    workflowPosition: "Quality Branch > Verification Phase",
                    howToUse: [
                        { label: "Run All Tests", cmd: "/test" },
                        { label: "Watch Mode", cmd: "/test --watch" },
                        { label: "Specific File", cmd: "/test src/utils.ts" }
                    ]
                }
            },
            "/master-orchestrator": {
                "desc": "Intelligent central orchestrator for unified skill routing and workflow management.",
                "usage": "/orchestrate --suggest <skill>",
                "whenToUse": "Use to discover skill relationships, validate workflows, or route to any of the 192+ skills.",
                "richCard": {
                    "title": "Master Skill Orchestrator",
                    "summary": "Consolidates skill orchestration by parsing suggest fields, enforcing state machine transitions, and routing to unified implementations. It lives as both a Python API and a CLI interface.",
                    "workflowPosition": "Control Branch > Steering Phase",
                    "howToUse": [
                        { "label": "Show Suggestions", "cmd": "/orchestrate --suggest /nse" },
                        { "label": "View Skill Info", "cmd": "/orchestrate --info /arch" },
                        { "label": "Show Graph", "cmd": "/orchestrate --graph" },
                        { "label": "Show Stats", "cmd": "/orchestrate --stats" }
                    ],
                    "commonUseCases": [
                        "Validating complex multi-step workflows",
                        "Discovering optimal next steps via dynamic graph",
                        "Auditing decision trails for strategic skills",
                        "Unified routing for Python and CLI skills"
                    ],
                    "pitfalls": [
                        "Avoid invalid transitions that bypass the state machine",
                        "Ensure SKILL.md suggest fields are up to date"
                    ],
                    "modules": [
                        "orchestrator.py - Core API",
                        "suggest_parser.py - Relationship Discovery",
                        "workflow_state.py - State Machine",
                        "skill_router.py - Execution Dispatcher",
                        "test_orchestrator.py - Quality Gate"
                    ]
                }
            },
            "/debug": {
                usage: "/debug [error_log] --analyze",
                desc: "Unified debugging suite with RCA capabilities."
            },
            "/notebooklm": {
                usage: "/notebooklm query [question] --notebook [id]",
                desc: "Queries your NotebookLM corpus for grounded answers."
            },
            "/library-first": {
                usage: "/library-first [topic]",
                desc: "Checks existing libraries to avoid reinventing the wheel.",
                useCase: "You need to parse a CSV file. Instead of writing a new parser function, run this command to see if the project already prefers 'pandas' or the standard 'csv' module, ensuring consistency.",
                example: "/library-first csv parsing"
            },
            "/truth": {
                usage: "/truth [statement] --verify",
                desc: "Validates assumptions against ground truth sources.",
                useCase: "The LLM suggests using a method you suspect is deprecated (e.g., 'React.createClass'). Use this to verify its status against the official documentation before implementing.",
                example: "/truth 'React.createClass is deprecated' --verify"
            },
            "/catchup": {
                usage: "/catchup --since [time]",
                desc: "Summarizes missed context and recent events."
            },
            "/session-handoff": {
        usage: "/session-handoff [save|load] --id [session_id]",
        desc: "Transfers context state between agent sessions."
    },
    "/llm_models": {
        usage: "/llm_models [list|set|get] [model_id]",
        desc: "Manages and configures active LLM models for the current session.",
        useCase: "Switching between models to balance cost vs. capability (e.g., Flash for bulk tasks, Opus for reasoning)."
    },
    "/init": {
        usage: "/init [project_type] --name [name]",
        desc: "Initializes a new project or workspace component with standard scaffolding.",
        useCase: "Kickstarting a new microservice or module with all required boilerplate and config files."
    },
    "/cgate": {
        usage: "/cgate [status|optimize|clear]",
        desc: "Controls the Context Gate to manage token usage and context window efficiency.",
        useCase: "When context is full or irrelevant history is confusing the model."
    },
    // --- HUBS ---
    "/design": {
        usage: "/design [feature] --interactive",
        desc: "Orchestrates the creation of design artifacts (PRD, Specs) before implementation.",
        useCase: "Starting a complex new feature where requirements are fuzzy."
    },
    "/build": {
        usage: "/build [component] --scaffold",
        desc: "Compiles, transpiles, or constructs project artifacts.",
        useCase: "Generating boilerplate code or running build scripts.",
        whenToUse: "Use when creating new components or running the build pipeline.",
        richCard: {
            title: "Build & Scaffold Hub",
            summary: "The implementation engine. Handles compilation, transpilation, and scaffolding of new project components using standard templates.",
            workflowPosition: "Execution Branch > Development Phase",
            howToUse: [
                { label: "Scaffold Component", cmd: "/build --scaffold react/Button" },
                { label: "Run Build", cmd: "/build" },
                { label: "Clean Artifacts", cmd: "/build --clean" }
            ]
        }
    },
    "/ask": {
        desc: "Universal CLI router for intelligent command discovery, routing, and orchestration. It triages requests, validates claims, and hands off to the specialized tool.",
        usage: "/ask \"how do I...\"     # Intent-based routing\n/ask \"plan feature X\"  # Routes to /breakdown\n/ask \"debug failure\"   # Routes to /debug\n/ask \"help\"            # Command discovery",
        useCase: [
            "Route complex intents to the right tool (e.g. 'research', 'plan', 'debug')",
            "Validate claims about completed work ('Truth Validation')",
            "Discover available commands with natural language queries",
            "Maintain session context across multiple command executions"
        ],
        mechanics: "1. Triage & Parse: Calculates a 'Reversibility Score' (1.0-2.0) and 'Dependency Count' to mathematically determine the cognitive path (Fast, Standard, or Careful). It simultaneously extracts user intent, explicit command invocations, and context markers from the raw input string.\n\n2. Context Exploration: For complex requests, it executes a `csf` deep scan (`csf/cli/nip/search.py --layer 3`) to map file dependencies and proactively queries the skills backend to construct a comprehensive context graph before any routing decision is made.\n\n3. Truth Validation: Validates assertions of completed work by auditing evidence (Tier 1: logs/diffs to Tier 4: comments). It calculates a weighted 'Truth Score'; if this score falls below the 0.7 threshold, the router strictly blocks execution and demands manual verification.\n\n4. Intelligent Routing: Matches the validated intent against the `commands.toml` registry using semantic analysis. It resolves architecture queries to `/arch`, debugging to `/debug`, etc., ensuring the most specialized tool is utilized.\n\n5. Execution Handoff: Serializes the original request, the constructed context graph, session history, and all validation artifacts into a payload object, which is then injected into the target command's entry point for a fully contextualized start."
    },
    "/deps": {
        usage: "/deps [add|remove|check|list|visualize] [project]",
        desc: "Dependency management for TaskMaster projects.",
        useCase: "Tracking project dependencies and preventing circular references."
    },
    "/docs": {
        usage: "/docs [topic] --generate",
        desc: "Manages project documentation generation and maintenance.",
        useCase: "Updating the README or creating new architecture guides."
    },
    "/triage": {
        usage: "/triage [issue_id]",
        desc: "Analyzes incoming tasks or bugs to assign priority and agent routing.",
        useCase: "Processing a list of user-reported bugs."
    },
    "/specify": {
        usage: "/specify [requirement]",
        desc: "Generates detailed technical specifications from high-level requirements.",
        useCase: "Converting a user story into a technical spec."
    },
    "/evolve": {
        usage: "/evolve --target [metric]",
        desc: "Iteratively improves system health, dependencies, and patterns.",
        useCase: "Upgrading dependencies or refactoring legacy modules.",
        richCard: {
            title: "System Evolution Hub",
            summary: "The engine for continuous improvement. It handles refactoring, dependency updates, and applying new patterns across the codebase.",
            workflowPosition: "Evolution Branch > Evolution Phase",
            howToUse: [
                { label: "Optimize Deps", cmd: "/evolve --deps" },
                { label: "Apply Pattern", cmd: "/evolve --pattern repository" },
                { label: "Cleanup", cmd: "/evolve --cleanup" }
            ]
        }
    },
    "/wo_advisory": {
        usage: "/wo_advisory [topic]",
        desc: "Work Order Advisory: Generates strategic advice for complex tasks.",
        useCase: "Getting a second opinion on a proposed implementation plan."
    },
    // --- CORE TOOLS ---
    "/think": {
        usage: "/think [problem]",
        desc: "Invokes the 'Sequential Thinking' protocol for complex problem solving.",
        useCase: "Breaking down a multi-step logic problem or debugging a race condition."
    },
    "/search": {
        usage: "/search [query]",
        desc: "Unified search engine across codebase, docs, and chat history.",
        useCase: "When you don't know where a definition is located."
    },

    "/task": {
        usage: "/task [status]",
        desc: "Manages the current task status and boundaries.",
        useCase: "Updating the visual task tracker."
    },
    "/workflow": {
        usage: "/workflow [view|edit]",
        desc: "Displays or modifies the active agent workflow state.",
        useCase: "Checking which agents are active.",
        whenToUse: "Use to define or check the high-level process flow.",
        richCard: {
            title: "Workflow Management Hub",
            summary: "Controls the active state of the agentic system. It defines which agents are active, their handoff protocols, and the current phase of the SDLC.",
            workflowPosition: "Control Branch > Steering Phase",
            howToUse: [
                { label: "View State", cmd: "/workflow view" },
                { label: "Change Phase", cmd: "/workflow set-phase execution" },
                { label: "List Agents", cmd: "/workflow agents" }
            ]
        }
    },
    "/checkpoint": {
        usage: "/checkpoint [name]",
        desc: "Creates a lightweight local save point (WIP snapshot).",
        useCase: "Saving state before a risky refactor.",
        whenToUse: "Use before starting a risky operation.",
        richCard: {
            title: "Checkpoint & State Hub",
            summary: "Provides instant, lightweight snapshots of the workspace state. Unlike Git commits, Checkpoints are designed for rapid, ephemeral experiments and safe rollbacks.",
            workflowPosition: "Execution Branch > Utilities Phase",
            howToUse: [
                { label: "Save State", cmd: "/checkpoint pre-refactor" },
                { label: "List Saves", cmd: "/checkpoint list" },
                { label: "Rollback", cmd: "/restore <id>" }
            ]
        }
    },
    "/restore": {
        usage: "/restore [id]",
        desc: "Restores the workspace to a previous checkpoint.",
        useCase: "Rolling back a failed experiment."
    },
    "/analyze": {
        usage: "/analyze [file]",
        desc: "Performs deep static and dynamic analysis of a component.",
        useCase: "Understanding the complexity or dependencies of a module."
    },
    // --- FRAMEWORKS ---
    "/acef": {
        usage: "/acef --explain",
        desc: "Agentic Cognitive Execution Framework - The core reasoning loop.",
        useCase: "Understanding how agents make decisions."
    },
    "/csaf": {
        usage: "/csaf --check",
        desc: "Constitutional Safety Alignment Framework - Safety boundaries.",
        useCase: "Verifying compliance with safety rules."
    },
    "/dpef": {
        usage: "/dpef --optimize",
        desc: "Dynamic Prompt Engineering Framework - Context optimization.",
        useCase: "Improving model performance via prompt tuning."
    }
};        


        window.AGENT_METADATA = {
            "@architect": { 
                role: "Architect", 
                desc: "High-level system design and decision-making authority.", 
                icon: "pen-tool",
                capabilities: ["System Design", "Tech Stack Selection", "Cluster Governance", "Pattern Enforcement"]
            },
            "@product-manager": { 
                role: "Product", 
                desc: "Translates requirements into actionable specs.", 
                icon: "briefcase",
                capabilities: ["Requirements Analysis", "User Stories", "Roadmapping", "Prioritization"]
            },
            "@python-core": { 
                role: "Python Dev", 
                desc: "Specialist in Python backend development and standards.", 
                icon: "code",
                capabilities: ["Backend Logic", "API Design", "Performance Tuning", "Type Hinting"]
            },
            "@csf-nip-development": { 
                role: "NIP Dev", 
                desc: "Core Framework (CSF/NIP) integration specialist.", 
                icon: "cpu",
                capabilities: ["Framework Integration", "Pattern Implementation", "Core Systems"]
            },
            "@deepgit": { 
                role: "Version Control", 
                desc: "Advanced Git operations and history analysis.", 
                icon: "git-branch",
                capabilities: ["Complex Merges", "History Rewriting", "Branch Management", "Bisect"]
            },
            "@smart_git_commit": { 
                role: "Committer", 
                desc: "Generates semantic, conventional commit messages.", 
                icon: "git-commit",
                capabilities: ["Semantic Commits", "Change Summarization", "Convention Enforcement"]
            },
            "@qa-engineer": { 
                role: "QA Lead", 
                desc: "End-to-end testing and quality certification.", 
                icon: "shield-check",
                capabilities: ["Test Strategy", "Integration Testing", "Release Certification", "Bug Hunting"]
            },
            "@code-critic": { 
                role: "Reviewer", 
                desc: "Static analysis and code style enforcement.", 
                icon: "eye",
                capabilities: ["Code Review", "Style Enforcement", "Static Analysis", "Best Practices"]
            },
            "@rca-specialist": { 
                role: "RCA Lead", 
                desc: "Root Cause Analysis investigator.", 
                icon: "alert-triangle",
                capabilities: ["Root Cause Analysis", "Failure Pattern Matching", "Incident Investigation"]
            },
            "@rca-learning-specialist": { 
                role: "RCA Learning", 
                desc: "Distills patterns from past failures.", 
                icon: "book-open",
                capabilities: ["Pattern Distillation", "Knowledge Base Updates", "Post-Mortem Analysis"]
            },
            "@rca-verification-specialist": { 
                role: "RCA Verify", 
                desc: "Validates fixes and reproduction steps.", 
                icon: "check-circle",
                capabilities: ["Fix Verification", "Reproduction Steps", "Regression Testing"]
            },
            "@every-style-editor": { 
                role: "Refactorer", 
                desc: "Automated code style and formatting updates.", 
                icon: "align-left",
                capabilities: ["Auto-Formatting", "Style Standardization", "Lint Fixes"]
            },

            "@csf-nip-knowledge": { role: "Knowledge Base", desc: "Maintains the central knowledge repository.", icon: "database", capabilities: ["Knowledge Retrieval", "Context Updates", "Documentation"] },
            "@csf-nip-planning-command": { role: "Planner", desc: "Orchestrates high-level planning commands.", icon: "map", capabilities: ["Strategic Planning", "Command Parsing", "Roadmap Alignment"] },
            "@csf-sr-architecture-solid-principles": { role: "SOLID Architect", desc: "Enforces SOLID principles in architecture.", icon: "box", capabilities: ["SOLID Enforcement", "Coupling Analysis", "Interface Segregation"] },
            "@csf-sr-explainable-reasoning": { role: "Explainability", desc: "Ensures AI reasoning is transparent and logged.", icon: "file-text", capabilities: ["Reasoning Traces", "Decision logging", "Transparency"] },
            "@csf-sr-optimization-strategy": { role: "Optimizer", desc: "Strategizes system-wide optimizations.", icon: "trending-up", capabilities: ["Performance Strategy", "Resource Allocation", "Efficiency"] },
            "@graphql-architect": { role: "GraphQL Arch", desc: "Designs GraphQL schemas and resolvers.", icon: "share-2", capabilities: ["Schema Design", "Resolver Optimization", "Federation"] },
            "@prompt-architect": { role: "Prompt Eng", desc: "Optimizes system prompts and context injection.", icon: "terminal", capabilities: ["Prompt Engineering", "Context Management", "Token Optimization"] },
            "@quant-analyst": { role: "Quant", desc: "Quantitative analysis and metrics.", icon: "bar-chart-2", capabilities: ["Data Analysis", "Statistical Modeling", "Metrics"] },
            "@rag-architect": { role: "RAG Arch", desc: "Designs Retrieval-Augmented Generation pipelines.", icon: "search", capabilities: ["Vector Search", "Embedding Strategy", "Retrieval"] },
            "@researcher": { role: "Researcher", desc: "Deep technical research and discovery.", icon: "microscope", capabilities: ["Information Retrieval", "Tech Evaluation", "Synthesis"] },
            "@vector-db-expert": { role: "Vector DB", desc: "Manages vector embeddings and stores.", icon: "database", capabilities: ["Embedding Management", "Similarity Search", "Index Optimization"] },

            "@api-builder": { role: "API Dev", desc: "Constructs robust API endpoints.", icon: "server", capabilities: ["Endpoint Creation", "REST/GraphQL", "Auth Integration"] },
            "@csf-sr-framework-react-hooks": { role: "React Hooks", desc: "Specializes in custom React hooks.", icon: "code", capabilities: ["Hook Logic", "State Management", "Reusability"] },
            "@python-web": { role: "Python Web", desc: "Python web framework specialist (Django/FastAPI).", icon: "globe", capabilities: ["Framework Config", "Route Handling", "Middleware"] },
            "@react-specialist": { role: "React Dev", desc: "Frontend React UI development.", icon: "layout", capabilities: ["Component Logic", "Virtual DOM", "Lifecycle"] },
            "@tdd-implementer": { role: "TDD Dev", desc: "Implements code satisfying tests.", icon: "check-square", capabilities: ["Red-Green-Refactor", "Test Compliance", "Implementation"] },
            "@tdd-refactorer": { role: "TDD Refactor", desc: "Refactors code while keeping tests passing.", icon: "refresh-cw", capabilities: ["Code Cleanup", "Performance", "Safety"] },
            "@tdd-test-writer": { role: "Test Writer", desc: "Writes comprehensive test cases.", icon: "edit-3", capabilities: ["Unit Tests", "Integration Tests", "Coverage"] },
            "@ui-ux-expert": { role: "UI/UX", desc: "Ensures usability and visual fidelity.", icon: "eye", capabilities: ["User Flow", "Accessibility", "Visual Design"] },

            "@csf-nip-constitution-specialist": { role: "Constitution", desc: "Enforces AI constitution and safety.", icon: "shield", capabilities: ["Safety Checks", "Policy Enforcement", "Compliance"] },
            "@csf-nip-quality": { 
                role: "Quality", 
                desc: "General quality assurance standards.", 
                icon: "award", 
                capabilities: ["Standardization", "Best Practices", "Quality Gates"], 
                badge: "START",
                useCase: "Before creating any new file or module, consult this agent to ensure you aren't violating the 'Single Responsibility' principal, creating a duplicate utility, or missing a required file header." 
            },
            "@csf-nip-security": { 
                role: "Security", 
                desc: "Security auditing and hardening.", 
                icon: "lock", 
                capabilities: ["Vulnerability Scan", "Hardening", "Auth Checks"],
                useCase: "Run this agent early in the design phase to identify potential attack vectors in your API schema, or before deployment to scan for hardcoded secrets and dependency vulnerabilities."
            },
            "@csf-sr-multimodal-analysis": { role: "Multimodal", desc: "Analyzes text, image, and other data types.", icon: "image", capabilities: ["Image Analysis", "Text Processing", "Fusion"] },
            "@csf-sr-risk-assessment": { role: "Risk", desc: "Assesses project and code risks.", icon: "alert-octagon", capabilities: ["Risk Scoring", "Impact Analysis", "Mitigation"] },
            "@csf-sr-temporal-analysis": { role: "Temporal", desc: "Analyzes time-series and event sequences.", icon: "clock", capabilities: ["Timeline Analysis", "Sequence Detection", "Trending"] },
            "@risk-manager": { role: "Risk Mgr", desc: "High-level risk management strategy.", icon: "umbrella", capabilities: ["Strategic Risk", "Contingency Planning", "Governance"] },

            "@chaos-engineer": { role: "Chaos", desc: "Intentionally injects faults to test resilience.", icon: "zap-off", capabilities: ["Fault Injection", "Resilience Testing", "Stress Test"] },
            "@csf-sr-adaptive-learning": { role: "Adaptive", desc: "System that learns and adapts over time.", icon: "activity", capabilities: ["Feedback Loops", "Self-Correction", "Adaptation"] },
            "@ml-engineer": { role: "ML Eng", desc: "Machine Learning model implementation.", icon: "cpu", capabilities: ["Model Training", "Inference", "Data Pipelines"] },
            "@mlops-engineer": { role: "MLOps", desc: "Operations for ML deployment.", icon: "settings", capabilities: ["Model Deployment", "Monitoring", "Scale"] },

            "@context-manager": { role: "Context", desc: "Manages conversation window and memory.", icon: "maximize", capabilities: ["Token Management", "Context Selection", "Pruning"] },
            "@csf-nip-infrastructure": { role: "Infra", desc: "Underlying system infrastructure.", icon: "server", capabilities: ["System Config", "Environment", "Resources"] },
            "@csf-sr-cognitive-integration": { role: "Cognitive", desc: "Integrates reasoning capabilities.", icon: "brain", capabilities: ["Cognition", "reasoning", "integration"] },
            "@csf-sr-monitoring-instrumentation": { role: "Monitor", desc: "Real-time system monitoring.", icon: "activity", capabilities: ["Logging", "Metrics", "Alerting"] },
            "@csf-sr-predictive-analytics": { role: "Predictive", desc: "Predicts future system states.", icon: "trending-up", capabilities: ["Forecasting", "Trend Analysis", "Proactive"] },
            "@n8n-expert": { role: "Automation", desc: "Workflow automation using n8n.", icon: "workflow", capabilities: ["Workflow Design", "Integration", "Automation"] },
            "@csf-nip-orchestration": { 
                role: "Orchestrator", 
                desc: "Manages multi-agent workflows and handoffs.", 
                icon: "layers",
                capabilities: ["Workflow Management", "Agent Handoffs", "Task Coordination"]
            }
        };



        window.EDUCATIONAL_DATA = {
            "/library-first": {
                concept: {
                    title: "The 'Not Invented Here' Trap",
                    summary: "Developers often feel the urge to write their own utilities to avoid dependencies or 'keep it simple'. This leads to unmaintained, buggy code. /library-first defines a culture where we check the ecosystem before writing a single line of implementation logic.",
                    icon: "shield-alert"
                },
                visual: {
                    type: "flow",
                    steps: [
                        { label: "New Task", sub: "e.g., Parse generic CSV" },
                        { label: "Instinct", sub: "Write Regex split(',')", type: "bad" },
                        { label: "Reality", sub: "Fails on quotes, newlines", type: "bad" },
                        { label: "Better Way", sub: "Run /library-first", type: "good" },
                        { label: "Result", sub: "Import standard 'csv' module", type: "good" }
                    ]
                },
                mastery: [
                    { level: "Novice", text: "Run this command before writing any helper function > 5 lines of code." },
                    { level: "Pro", text: "Use it to standardize package choices across the team (e.g., 'Do we use Moment.js or date-fns?')." },
                    { level: "Expert", text: "If no library exists, write one and publish it to the internal registry, then register it here." }
                ],
                pitfalls: [
                    "Don't import a heavy library for a trivial one-line operation (the 'left-pad' problem).",
                    "Always check the license compatibility before proposing a new library."
                ]
            },
            "@product-manager": {
                concept: {
                    title: "The Bridge Between Abstract & Concrete",
                    summary: "The Product Manager isn't just about 'tickets'. They are the translation layer that converts fuzzy human desires into rigorous technical specifications that the Architect can validate and the Team can build.",
                    icon: "git-commit"
                },
                mastery: [
                    { level: "Novice", text: "Use @product-manager to generate user stories from a rough idea." },
                    { level: "Pro", text: "Ask them to prioritize the feature backlog based on technical debt vs. user value." },
                    { level: "Expert", text: "Have them simulate stakeholder pushback to test the robustness of your requirements." }
                ],
                pitfalls: [
                    "Don't treat them as a project manager. They own the 'Why', not just the 'When'.",
                    "Provides specs, not code. Don't ask them for implementation details."
                ]
            }
        };



        window.EXPERT_KNOWLEDGE = {
            "/refactor": {
                tips: [
                    "Best for files < 500 lines. For larger files, split them first or refactor by region.",
                    "Always define the return type before extracting a function to ensure type safety stays intact."
                ],
                examples: [
                    { title: "Extract Helper", prompt: "Extract the validation logic in the 'handleSubmit' function to a new 'validateForm' function." },
                    { title: "Modernize Class", prompt: "Convert this Class Component to a Functional Component with Hooks." },
                    { title: "Simplify Logic", prompt: "Invert this if-statement to reduce nesting depth." }
                ],
                mechanics: "Analysis: AST-based transformations. Safe for syntax, but always verify business logic manually.",
                constraints: ["Does not update references in *other* files automatically.", "May strip non-standard comments in complex JSX blocks."]
            },
            "/verify": {
                tips: [
                    "Run this locally before pushing. It captures 90% of CI failures.",
                    "Use `--watch` mode when actively debugging a test suite to get instant feedback."
                ],
                examples: [
                    { title: "Full Check", prompt: "/verify --all" },
                    { title: "Only Tests", prompt: "/verify --tests-only" },
                    { title: "Lint Fix", prompt: "/verify --fix" }
                ],
                mechanics: "Runs standard linting (ESLint), type checking (TSC), and unit tests (Jest/Vitest).",
                constraints: ["Does not run integration or E2E tests by default (too slow)."]
            },
            "/research": {
        tips: [
            "Be specific. Broad queries like 'how does auth work' yield noise.",
            "Use file path filters if you know the domain (e.g., 'path:src/auth login flow')."
        ],
        examples: [
            { title: "Find Pattern", prompt: "Find all usages of the 'User' class in the 'services' directory." },
            { title: "Explain Logic", prompt: "Explain how the 'retryStrategy' is implemented in 'apiClient.ts'." }
        ],
        mechanics: "Semantic Search (Vector) + Keyword Search (Grep).",
        constraints: ["Cannot see files excluded by .gitignore.", "Knowledge cutoff depends on the last vector index update."]
    },
    "/llm_models": {
        tips: [
            "Use smaller models (Flash/Haiku) for summarization or simple code generation to save costs.",
            "Reserve larger models (Opus/GPT-4) for complex architectural reasoning or refactoring.",
            "Changes persist for the session but reset on restart unless configured in global settings."
        ],
        mechanics: "Updates the session configuration object in memory. Does not restart the underlying LLM client.",
        constraints: ["Available models depend on your API key permissions.", "Switching models mid-stream may lose some context nuances specific to the previous model's tokenizer."]
    },
    "/init": {
        tips: [
            "Always run from the root directory of your workspace to ensure correct path resolution.",
            "Use --dry-run first to see exactly what files will be created before writing to disk."
        ],
        examples: [
            { title: "New Python Service", prompt: "/init python-service --name auth-worker" },
            { title: "React Component", prompt: "/init react-component --name UserProfile" }
        ],
        mechanics: "Uses Jinja2 templates from the system `templates/` directory to scaffold files.",
        constraints: ["Will fail if target directory is not empty (unless --force is used).", "Templates must exist in the system registry."]
    },
    "/cgate": {
        tips: [
            "Run `/cgate optimize` before starting a complex task to free up context window space.",
            "Use `/cgate status` to see exactly which files are currently consuming your token budget."
        ],
        mechanics: "Analyzes the conversation history and actively prunes or summarizes older turns based on relevance scores.",
        constraints: ["Aggressive optimization might remove subtle context definitions.", "Cannot recover cleared context once it is fully pruned (unless you have a checkpoint)."]
    },
    "/think": {
        tips: [
            "Use for problems that require > 3 steps to solve.",
            "Great for 'Rubber Ducking' complex logic before writing code."
        ],
        mechanics: "Injects a structured CoT (Chain of Thought) block into the context.",
        constraints: ["Consumes more tokens than a direct answer.", "May be slower to generate."]
    },
    "/design": {
        tips: [
            "Start with a high-level goal, then iterate on the details.",
            "Use `--interactive` to have the agent ask clarifying questions."
        ],
        mechanics: "Generates markdown artifacts (PRDs) and validates them against the Schema.",
        constraints: ["Requires a clear user intent to start.", "Does not write code directly (use /build for that)."]
    },
    "/build": {
        tips: [
            "Use `--scaffold` for new files to get standard headers and imports.",
            "Always verify the build output with `/test` afterwards."
        ],
        mechanics: "Wraps standard build tools (npm, pip, cargo) with error parsing.",
        constraints: ["Cannot fix build errors automatically (use /fix for that)."]
    }
};



window.SEMANTIC_CATEGORIES = {
    "Governance_Policy": {
        "items": [
                "/comply",
                "/constitutional-patterns",
                "/constraints",
                "/standards",
                "/validate_spec",
                "/validate-safety-patterns",
                "/step_6_5",
                "/slc",
                "/prrp",
                "/sar-inst",
                "/cb",
                "/hooks-edit",
                "/sap",
                "/sap_commit",
                "/quadlet"
        ],
        "desc": "Governance, Compliance, or Safety Policy.",
        "usage": "Reference Only",
        "useCase": "Ensuring system alignment and safety."
    },
    "Learning_Ops": {
        "items": [
                "/learn",
                "/reflect",
                "/retro",
                "/rca",
                "/investigate",
                "/cleanup",
                "/r",
                "/q",
                "/skills_migrate",
                "/testing-skills"
        ],
        "desc": "Learning, Optimization, or Retrospective Operation.",
        "usage": "/<cmd> [topic]",
        "useCase": "Improving system capability and health."
    },
    "Orchestration_Flow": {
        "items": [
                "/orchestrate",
                "/flow",
                "/cwo",
                "/cwo_orchestrator",
                "/execution-clarity",
                "/llm_edit_coordination",
                "/multi-file-refactor",
                "/task",
                "/tm"
        ],
        "desc": "High-level Task Orchestration or Workflow.",
        "usage": "/orchestrate <plan>",
        "useCase": "Managing complex multi-step agent workflows."
    },
    "Agent_Runtime": {
        "items": [
                "/main",
                "/exec",
                "/session",
                "/memory",
                "/obs",
                "/discover",
                "/consult",
                "/apply_safety_patterns",
                "/subagent-first",
                "/search_more",
                "/clear_notifications",
                "/clear_restore"
        ],
        "desc": "Core Agent Runtime or Session Command.",
        "usage": "System Internal",
        "useCase": "Managing agent awareness and lifecycle."
    },
    "AI_Model": {
        items: ["/llm_codex", "/llm_gemini", "/llm_qwen", "/llm_openrouter", "/llm-cli", "/llm-brainstorm", "/llm-review", "/llm_health", "/llm_performance", "/llm_debate", "/llm_doc_review", "/ai_distiller", "/analytics", "/cognitive"],
        desc: "Specialized LLM Model Wrapper or Interface.",
        usage: "/<model_name> [prompt]",
        useCase: "Invoking a specific model capability or wrapper."
    },
    "Git_Action": {
        items: [
                "/clone",
                "/fetch",
                "/log",
                "/status",
                "/diff",
                "/merge",
                "/rebase",
                "/cherry-pick",
                "/blame",
                "/git-conventional-commits",
                "/git-safety",
                "/git-sapling",
                "/git-worktrees",
                "/push",
                "/pull",
                "/remote",
                "/branch",
                "/commit"
        ],
        desc: "Standard Git Version Control Operation.",
        usage: "/git <subcommand>",
        useCase: "Version control and history management."
    },
    "Checkpoint_Op": {
        items: ["/checkpoint_delete", "/checkpoint_diff", "/checkpoint_list", "/checkpoint_restore", "/save", "/load"],
        desc: "Workspace State Management Operation.",
        usage: "/checkpoint <action>",
        useCase: "Managing local save states and snapshots."
    },
    "Testing_State": {
        items: [
                "/test-pass",
                "/test-fail",
                "/test-error",
                "/test-bisect",
                "/coverage",
                "/unit",
                "/integration",
                "/e2e",
                "/tdd-cycle",
                "/qa",
                "/tdd"
        ],
        desc: "Automated Testing Lifecycle State or Metric.",
        usage: "System Output (Read Only)",
        useCase: "Analyzing test execution results."
    },
    "Analysis_Metric": {
        items: [
                "/complexity",
                "/churn",
                "/hotspot",
                "/coupling",
                "/cohesion",
                "/debt",
                "/analysis-audit",
                "/analysis-logs",
                "/analysis-profile",
                "/quota",
                "/telemetry",
                "/perf",
                "/health-monitor"
        ],
        desc: "Codebase Static Analysis Metric.",
        usage: "/analyze --metric <name>",
        useCase: "Understanding code quality and health dimensions."
    },
    "Web_Construct": {
        items: ["/route", "/middleware", "/json", "/headers", "/request", "/response", "/endpoint", "/controller", "/service", "/web-artifacts-builder"],
        desc: "Web Application or API Component.",
        usage: "Import from framework",
        useCase: "Building backend services or APIs."
    },
    "React_Ecosystem": {
        items: ["/hook", "/context", "/provider", "/state", "/effect", "/reducer", "/callback", "/memo", "/ref", "/portal"],
        desc: "React Frontend Framework Primitive.",
        usage: "import { ... } from 'react'",
        useCase: "Building interactive UI components."
    },
    "Doc_Artifact": {
        items: ["/readme", "/changelog", "/wiki", "/adr", "/rfp", "/problem-statement", "/reports", "/review_bundle", "/doc_to_skill", "/hod", "/sar-help", "/csda-concept", "/artifact", "/artifact-add", "/artifact_audit", "/artifact_done", "/prd"],
        desc: "Documentation or Knowledge Artifact.",
        usage: "/docs --view <artifact>",
        useCase: "Reading or generating project knowledge."
    },
    "Framework_Util": {
        items: ["/context_status", "/data_processor", "/deliberate-changes", "/deps", "/disler_start", "/disler_stop", "/rich-library-expert", "/sar-inst", "/session-awareness", "/session-handoff", "/sharing-skills", "/solo-dev-authority", "/subagent-driven-development", "/subagent-first", "/timeline", "/val", "/value", "/writing-skills", "/vta", "/sp", "/update_state", "/value-maximization", "/bgkill", "/pwsh", "/write-file", "/code-python-2025", "/code-typescript-2025", "/command-enhance", "/command_create", "/ddd", "/nse", "/session-transcript-w1t2"],
        desc: "Internal System Utility or Framework Helper.",
        usage: "System Internal",
        useCase: "Supporting the agentic workflow runtime."
    }
};


window.CONSOLIDATION_MAP = {
    // AI Tooling → /llm_models
    "/llm_codex": "/llm_models",
    "/llm_gemini": "/llm_models",
    "/llm_qwen": "/llm_models",
    "/llm_openrouter": "/llm_models",
    "/llm-cli": "/llm_models",
    "/llm-brainstorm": "/llm_models",
    "/llm-review": "/llm_models",
    "/llm_debate": "/llm_models",
    "/llm_doc_review": "/llm_models",
    "/llm_edit_coordination": "/llm_models",
    "/llm_route": "/llm_models",
    
    // Knowledge → /memory (PROPOSED)
    "/cks": "/memory",
    "/chs": "/memory",
    "/memory-system": "/memory",
    "/memory-integration": "/memory",
    "/cks-usage": "/memory",
    
    // Git & VCS → /git
    "/git-conventional-commits": "/git",
    "/git-safety": "/git",
    "/git-sapling": "/git",
    "/git-worktrees": "/git",
    
    // Utilities → /checkpoint (PROPOSED)
    "/checkpoint_delete": "/checkpoint",
    "/checkpoint_diff": "/checkpoint",
    "/checkpoint_list": "/checkpoint",
    "/checkpoint_restore": "/checkpoint",
    
    // Analysis → /analyze
    "/analysis-audit": "/analyze",
    "/analysis-logs": "/analyze",
    "/analysis-profile": "/analyze",
    
    // Testing → /test
    "/test-bisect": "/test",
    "/tdd-cycle": "/test",
    "/qa": "/test",
    
    // Debugging → /debug
    "/bug_hunt": "/debug",
    "/session-transcript-w1t2": "/debug",
    
    // Meta → /cognitive (PROPOSED)
    "/cognitive-frameworks": "/cognitive",
    "/sequential-thinking": "/cognitive",
    "/read-before-write": "/cognitive",
    
    // Meta → /session (PROPOSED)
    "/session-awareness": "/session",
    "/session-handoff": "/session",
    
    // Workflow → /orchestrate (PROPOSED)
    "/cognitive_stack": "/orchestrate",
    "/cognitive_stack_production": "/orchestrate",
    "/cwo": "/orchestrate",
    "/cwo_orchestrator": "/orchestrate",
    "/quadlet": "/orchestrate",
    "/step_6_5": "/orchestrate",
    
    // Artifacts → /artifact (PROPOSED)
    "/artifact-add": "/artifact",
    "/artifact_audit": "/artifact",
    "/artifact_done": "/artifact",
    
    // Evolution → /evolve
    "/skills_migrate": "/evolve",
    "/update_state": "/evolve",
    "/value-maximization": "/evolve",
    
    // Learning → /learn
    "/reflect": "/learn",
    "/retro": "/learn",
    
    // Misc unchanged
    "/query_alias": "/search",
    "/rich-library-expert": "/library-first",
    
    // Orchestration -> /orchestrate
    "/orchestrate": "/orchestrate"
};


window.PROPOSED_HUBS = ["/memory", "/checkpoint", "/cognitive", "/session", "/orchestrate", "/artifact"];


