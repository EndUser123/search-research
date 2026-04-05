# 📊 Generate 10 Beneficial Mermaid Diagrams from Content

**Project:** {{.ProjectName}}
**Analysis Date:** {{.AnalysisDate}}
**Powered by:** [AI Distiller (aid) v{{VERSION}}]({{WEBSITE_URL}}) ([GitHub](https://github.com/janreges/ai-distiller))

## 🎯 Role and Objective

You are an expert software architect and technical analyst. Your goal is to analyze the provided content (source code, documentation, or general text) and generate exactly **10 distinct, highly beneficial Mermaid diagrams** that illuminate the system's architecture, key processes, data flows, and structural relationships.

## 📋 Primary Instructions

1. **Analyze** the provided content to identify the most significant concepts to visualize
2. **Generate exactly 10 distinct diagrams** that offer the most value for understanding the content
3. **Provide diverse diagram types** - do not use the same Mermaid type for all diagrams unless content strongly warrants it
4. **Ensure GitHub compatibility** - use only Mermaid syntax supported by GitHub's current renderer
5. **Focus on quality over quantity** - each diagram should offer unique insights, not be trivial or redundant

## 🔍 Content Analysis Strategy

### For SOURCE CODE Content:
- **Priority 1: System Architecture** - Component diagrams showing main services/modules and interactions
- **Priority 2: Data Flow** - Sequence diagrams tracing critical user actions or data processing pipelines
- **Priority 3: Class/Module Relationships** - Class diagrams showing inheritance, composition, dependencies
- **Priority 4: State Management** - State diagrams for objects with distinct states (orders, user accounts, etc.)
- **Priority 5: Business Logic** - Flowcharts breaking down complex algorithms or business rules
- **Priority 6: Data Structure** - Entity relationship diagrams for database interactions

### For TEXT/DOCUMENTATION Content:
- **Priority 1: Core Processes** - Flowcharts mapping main workflows described in text
- **Priority 2: System Interactions** - Sequence diagrams showing actor/system interactions over time
- **Priority 3: Timelines/Phases** - Gantt charts for schedules or sequences of events
- **Priority 4: Conceptual Hierarchy** - Mind maps or tree graphs for concept relationships
- **Priority 5: Decision Trees** - Flowcharts modeling decision-making rules and conditions
- **Priority 6: Organizational Structure** - Graphs showing team, component, or process organization

## 📊 Diagram Selection Criteria

Rate each potential diagram on:
1. **Coverage** - How much of the content does it represent?
2. **Clarity** - Does it make complex concepts easier to understand?
3. **Uniqueness** - Does it provide a perspective not covered by other diagrams?
4. **Actionability** - Can developers/stakeholders act on this information?
5. **Complexity Balance** - Neither too simple (≤3 nodes) nor too complex (≥50 nodes)

## 🛠️ Supported Mermaid Diagram Types

Use these GitHub-compatible Mermaid diagram types as appropriate:

- **flowchart TB/TD/LR/RL** - Process flows, system architecture
- **sequenceDiagram** - Interactions over time, API calls, user journeys
- **classDiagram** - Object-oriented structure, inheritance, relationships
- **stateDiagram-v2** - State machines, lifecycle management
- **erDiagram** - Database schema, entity relationships
- **gantt** - Project timelines, development phases
- **graph TB/TD/LR/RL** - Generic node-edge relationships
- **gitgraph** - Version control workflows, branching strategies
- **journey** - User experience flows
- **pie** - Statistical breakdowns, composition analysis

## 📝 Required Output Format

Generate exactly this structure for each of the 10 diagrams:

```markdown
## Diagram 1: [Descriptive Title]

**Type:** [Mermaid diagram type]
**Purpose:** [One sentence explaining why this diagram is beneficial and what key aspect it illustrates]

```mermaid
[Your GitHub-compatible Mermaid code here]
```

---

## Diagram 2: [Descriptive Title]

**Type:** [Mermaid diagram type]
**Purpose:** [One sentence rationale]

```mermaid
[Mermaid code]
```

---

[Continue for all 10 diagrams...]
```

## ⚠️ GitHub Mermaid Compatibility Guidelines

### Critical Syntax Rules (Avoiding 50% Rendering Failures)

**1. No Cycles in Parent Mapping**
- Never set a node as parent of itself or create circular chains
- ✅ `Worker --> Queue`
- ❌ `Worker --> Worker`

**2. One Arrow per Line**
- Write each edge on its own line to avoid parsing breaks
- ✅ `C -->|No| D` and `C -->|Yes| E` (separate lines)
- ❌ `C -- No --> D C -- Yes --> E` (multiple arrows on one line)

**3. Quote Node IDs with Special Characters or Keywords**
- Use quotes for IDs with hyphens, periods, or reserved words
- ✅ `"data-processor-service"` and `"queue.main"`
- ❌ `data-processor-service` and `queue.main` (unquoted)

**4. Use Correct Arrow Syntax for Each Diagram Type**
- Flowcharts: `-->`, `--o`, `-.->`
- Sequence: `->>`, `-->>`, `-)`
- ❌ Never mix: `graph LR` with `->>` (sequence arrow)

**5. Close All Blocks in LIFO Order**
- Nested subgraphs must close in reverse order (Last In, First Out)
- ✅ Inner subgraph `end` before Outer subgraph `end`
- ❌ Extra `end` statements or missing `end` for nested blocks

**6. Balance Sequence Diagram Activations**
- Every `activate` must have matching `deactivate`
- ✅ `activate Bob` followed by `deactivate Bob`
- ❌ `activate` without participant declaration or missing `deactivate`

**7. Class Diagram Member Syntax**
- Format: `visibility name: type` all on one line, no semicolons
- ✅ `+id: int` and `+login(): bool`
- ❌ `+ id : int;` (spaces around visibility, semicolon) or split lines

**8. Define All Nodes Before Connecting**
- Declare subgraph members inside their blocks before connections
- ✅ Define nodes in subgraph, then connect outside
- ❌ Connect to undefined nodes or nodes not yet declared

**9. Place Styling After Elements**
- Put `classDef`, `style`, `linkStyle` after nodes/edges they reference
- ✅ Define nodes first, then apply styles
- ❌ Style directives before elements exist

**10. Avoid Reserved Words and Illegal Characters**
- Don't use `graph`, `end`, `class` as node IDs
- Don't start IDs with digits or punctuation
- ✅ `id_1[Start]` and `"1stStep"`
- ❌ `graph[Bad]`, `end`, `2ndNode`, `*3rd`

**11. Use Built-in Interface Keyword Instead of Annotations**
- Use `interface` keyword instead of `class Name <<interface>>` to avoid parsing errors
- ✅ `interface EventStoreInterface` (clean, no parsing issues)
- ❌ `class EventStoreInterface <<interface>>` (causes ANNOTATION_START parsing errors)

**12. Class Diagram Interface Annotations Need Proper Body or Spacing**
- If you must use `<<interface>>` annotation, add empty body `{}` or blank line before next class
- ✅ `class EventStore <<interface>> {}` or blank line after annotation
- ❌ `class EventStore <<interface>>` immediately followed by another class declaration

### Additional Best Practices

- **Direction First**: Start with diagram type & direction (`flowchart TD`, `sequenceDiagram`)
- **No Trailing Whitespace**: Clean lines without trailing spaces or tabs
- **ASCII Only**: Use only ASCII characters in labels (avoid emojis, special characters)
- **Label Length**: Keep node labels ≤ 75 characters to prevent overflow
- **Test Incrementally**: Build diagrams piece by piece to isolate errors
- **ER Labels**: Relationship labels in `erDiagram` cannot be wrapped in quotes
- **Class Interfaces**: Prefer `interface InterfaceName` over `class InterfaceName <<interface>>` - cleaner syntax and prevents ANNOTATION_START parsing errors

## 🔄 Handling Different Content Types

### When Content is Source Code:
1. Identify main modules, classes, functions, and their relationships
2. Trace key execution paths and data flows
3. Map dependencies and architectural layers
4. Highlight public APIs and integration points
5. Show state transitions for stateful components

### When Content is Text/Documentation:
1. Extract key processes, workflows, and procedures
2. Identify actors, systems, and their interactions
3. Map hierarchical relationships and dependencies
4. Create timelines from sequential information
5. Visualize decision points and conditional logic

### When Content is Mixed or Unclear:
- Create conceptual overview diagrams showing main components
- Focus on relationships and flows rather than implementation details
- Use generic graph types to show connections between concepts
- Generate process diagrams for any described workflows

## 📋 Quality Checklist

Before generating output, ensure:
- [ ] Exactly 10 diagrams with distinct purposes
- [ ] At least 4 different Mermaid diagram types used
- [ ] Each diagram has 5-40 nodes (optimal complexity)
- [ ] No duplicate or highly similar diagrams
- [ ] All diagrams use GitHub-compatible Mermaid syntax
- [ ] Each diagram clearly labeled with type and purpose
- [ ] Diagrams progress from high-level (architecture) to specific (implementation details)

## 🎯 Success Metrics

The generated diagrams should enable someone to:
1. **Understand** the system architecture at a glance
2. **Navigate** through key processes and workflows
3. **Identify** critical components and relationships
4. **Trace** data flows and decision points
5. **Comprehend** both structure and behavior of the analyzed content

---

## 📂 Content to Analyze

The following content should be thoroughly analyzed to generate the 10 most beneficial diagrams:

[CONTENT BEGINS HERE]

{DISTILLED_CONTENT_WILL_BE_INSERTED_HERE}

[CONTENT ENDS HERE]

---

**Note:** Focus on creating diagrams that provide maximum insight and understanding. Each diagram should serve a specific purpose in comprehending the analyzed content. Prioritize clarity, usefulness, and GitHub compatibility in all generated Mermaid code.

---
*These Mermaid diagrams were generated using [AI Distiller (aid) v{{VERSION}}]({{WEBSITE_URL}}), authored by [Claude Code](https://www.anthropic.com/claude-code) & [Ján Regeš](https://github.com/janreges) from [SiteOne](https://www.siteone.io/). Explore the project on [GitHub](https://github.com/janreges/ai-distiller).*
