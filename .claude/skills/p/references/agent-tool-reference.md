# Agent Tool Parameter Reference

**When using the Agent tool to spawn subagents from /p, use these parameters correctly:**

| Parameter | Purpose | Valid Values | Required |
|-----------|---------|--------------|----------|
| `subagent_type` | Specifies which specialized agent to use | `general-purpose`, `Explore`, `Plan`, `feature-dev:code-architect`, etc. | **Yes** |
| `model` | Override the default model for this subagent | `sonnet`, `opus`, `haiku` | No (defaults to inherited) |
| `prompt` | What the subagent should do | Free text instructions | **Yes** |
| `description` | Short summary for task tracking | 3-5 word summary | **Yes** |

**Common Mistakes:**

WRONG:
```markdown
Launch subagents (haiku model):
```
This gets misinterpreted as `subagent_type="haiku"` -> **ERROR** (haiku is not an agent type)

CORRECT:
```markdown
Launch subagents with model="haiku":
```
This correctly passes `model: "haiku"` -> Works as expected

**When to Specify model Parameter:**
- **Speed optimization**: Use `model="haiku"` for simple tasks (bash commands, file checks, basic reporting)
- **Quality override**: Use `model="opus"` for complex reasoning when default would be sonnet
- **Cost optimization**: Use `model="haiku"` for high-volume, low-complexity operations

**Valid subagent_type values (NOT model names):**
- `general-purpose` - Default, can handle most tasks
- `Explore` - Codebase exploration and discovery
- `Plan` - Architecture and planning tasks
- `feature-dev:code-architect` - Feature architecture design
- `feature-dev:code-explorer` - Deep code analysis
- Many more - see full agent catalog

**Model selection guidance for subagents:**
- **P1 (Build)**: `model="haiku"` OK (test collection is mechanical)
- **P2 (Review)**: `model="sonnet"` required (deep analysis needs quality)
- **P3 (Validate)**: `model="haiku"` OK (linting is mechanical)
- **P4-P5**: `model="sonnet"` required (documentation requires reasoning)
