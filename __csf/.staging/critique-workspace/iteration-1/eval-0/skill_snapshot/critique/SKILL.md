---
name: critique
description: Use /critique whenever the user wants adversarial review of a plan, design, document, policy, prompt, or skill. Triggers on: "critique this", "review my X", "what's wrong with Y", "analyze this plan/design/skill". Produces a three-phase refined critique with severity-ranked findings and executable next steps. Not for casual feedback — for structured adversarial analysis.
category: analysis
triggers:
  - /critique
suggest:
  - /adversarial-review
  - /adversarial-critic
version: "1.1.0"
enforcement: advisory
parallel_agents: true
---

# Critique — Three-Phase Adversarial Review

Execute a three-phase adversarial critique of any work product (plan, design, document, policy, prompt, or skill).

## Subagent Architecture

| Phase | Agent | Timing | Purpose |
|-------|-------|--------|---------|
| 1 | general-purpose | Background | Initial critical review |
| 2 | general-purpose | Background (parallel with Phase 1) | Meta-critique of Phase 1 output |
| 3 | general-purpose | After Phases 1 & 2 complete | Synthesized refined critique |

**All three phases use the same agent type** (general-purpose) because all exercise critical analysis capability. The distinction is workflow position, not capability.

## Phase Prompts

| Phase | File | Key Function |
|-------|------|--------------|
| 1 | `phases/p1_initial_review.md` | Expert critical review of the work |
| 2 | `phases/p2_meta_critique.md` | Critique of the critique |
| 3 | `phases/p3_synthesis.md` | Synthesized refined critique |

## Your Workflow

### Step 1: Capture Work Input

Use conversation context to determine what to critique:

**Context-Aware Resolution (in priority order):**

1. **Args specifies target** — If args contains a skill name (e.g., `on /critique`) or is a path/description of work, use that.
2. **Recent session focus** — If args is empty, check what was just worked on. Recent file edits, skill modifications, or conversation focus indicate the target.
3. **Only ask if genuinely ambiguous** — If multiple possible targets exist in recent context, ask the user to clarify. Never ask when context is obvious.

**Examples:**
- `/critique on /critique` → Critique the /critique skill
- `/critique` (after editing a skill) → Critique that skill
- `/critique` (after no recent work) → Ask for input

### Step 2: Initialize File-Based Session

Create a critique session for token-efficient file passing:

```
python -c "
from pathlib import Path
import sys
sys.path.insert(0, 'P:/.claude/skills/critique/lib')
from critique_io import CritiqueSession
session = CritiqueSession()
session.setup()
session.write_work(sys.argv[1] if len(sys.argv) > 1 else '')
print(session.get_session_dir())
" \"{WORK_INPUT}\"
```

This creates: `{session_dir}/work.md`

### Step 3: Launch Phase 1 and Phase 2 in Parallel

Spawn two background agents simultaneously. Each receives **file paths only** (not content):

**Phase 1 Agent:**
```
Read P:/.claude/skills/critique/phases/p1_initial_review.md

Then execute:
1. cat "P:/{session_dir}/work.md"  # Read the work
2. Perform the critique based on the work content
3. Write your critique to: P:/{session_dir}/p1.md
   (Use: python -c "import sys; open('P:/{session_dir}/p1.md','w').write(sys.stdin.read())" < your_critique)
4. Output ONLY the path P:/{session_dir}/p1.md
```

**Phase 2 Agent:**
```
Read P:/.claude/skills/critique/phases/p2_meta_critique.md

Then execute:
1. cat "P:/{session_dir}/work.md"  # Read original work
2. cat "P:/{session_dir}/p1.md"   # Read Phase 1 critique
3. Perform meta-critique of Phase 1 (NOT the original work)
4. Write your meta-critique to: P:/{session_dir}/p2.md
   (Use: python -c "import sys; open('P:/{session_dir}/p2.md','w').write(sys.stdin.read())" < your_metacritique)
5. Output ONLY the path P:/{session_dir}/p2.md
```

Wait for both agents to complete.

### Step 4: Launch Phase 3 Synthesis

After Phase 1 and Phase 2 complete:

```
Read P:/.claude/skills/critique/phases/p3_synthesis.md

Then execute:
1. cat "P:/{session_dir}/work.md"   # Original work
2. cat "P:/{session_dir}/p1.md"    # Phase 1 critique
3. cat "P:/{session_dir}/p2.md"    # Phase 2 meta-critique
4. Produce synthesized refined critique incorporating all three
5. Write final critique to: P:/{session_dir}/p3.md
   (Use: python -c "import sys; open('P:/{session_dir}/p3.md','w').write(sys.stdin.read())" < your_synthesis)
```

### Step 5: Deliver Final Output

Read `P:/{session_dir}/p3.md` and present it as the final output.

### Step 6: Validate Work Input

Assert the work file is non-empty before launching phases:
```
python -c "
from pathlib import Path
work = Path('{session_dir}/work.md')
if not work.exists() or not work.read_text().strip():
    print('ERROR: No work input provided. Usage: /critique <work or skill name>')
    exit(1)
print('Work input validated.')
"
```

### Step 7: Cleanup

Session directories persist at `P:/.claude/.evidence/critique/` until manually removed. Cleanup is optional — the session_dir path was printed in Step 2.

## Output Structure

The final critique uses the original 7-section structure with severity tags. Render markdown properly — use headings, bold, etc. Do NOT show raw syntax like `**bold**`.

```
## Intent Summary
[2-3 sentences]

## Health Score: XX%

## Logical Gaps & Inconsistencies
1.1. [HIGH] issue (file:line)
...

## Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] issue
...

## Missing Obvious Actions / Best Practices
3.1. [HIGH] issue
...

## Risks and Edge Cases
4.1. [MEDIUM] issue
...

## Concrete Recommendations
5.1. [MEDIUM] specific change
...

## Open Questions / Unknowns
6.1. [LOW] uncertainty
...

## Recommended Next Steps
[Sorted by severity across all sections]

1. [HIGH] Fix specific thing
2. [MEDIUM] Address specific thing
...

**When you respond "0", the skill will begin implementing these fixes — starting with HIGH items and working through each cluster. This is an execution directive, not a display request.**

0 — Begin Implementing ALL Recommended Next Steps
```

## Handling "0 — Do ALL" (Phase 7)

When the user responds with "0" (or "Do ALL"), treat it as an **execution directive**, not an output request.

### What This Means
"0" means: stop reporting, start fixing. Proceed to implement the Recommended Next Steps beginning with HIGH severity items, working through clusters in order.

### Phase 7 Execution Protocol

**Phase 7a: Parse the recommendations**

Read `P:/{session_dir}/p3.md` and extract:
- The target (from work.md: what files/projects were critiqued)
- The Recommended Next Steps section
- Each step's severity from the `<!-- [SEVERITY] -->` HTML comments

**Phase 7b: Identify the target**

From work.md, determine what was critiqued:
- If a skill was critiqued (e.g., `/arch`), the target is `P:/.claude/skills/{skill_name}/`
- If a plan was critiqued, the target is the plan file referenced
- If a module was critiqued, the target is that module's path

**Phase 7c: Execute HIGH severity items first**

Start with all `<!-- [HIGH] -->` and `<!-- [CRITICAL] -->` items across clusters. For each:
1. Read the relevant source file
2. Make the minimal fix
3. If tests exist, run them
4. Verify the fix

**Phase 7d: Continue through MEDIUM items**

After all HIGH items complete, proceed through `<!-- [MEDIUM] -->` items in cluster order.

**Phase 7e: Report per-item status**

For each item, report:
- `DONE` if implemented and verified
- `DEFERRED` if blocked by dependency or need for more context
- `N/A` if the item is actually a documentation/process gap (not a code fix)

**Stop condition**: Continue until all items are marked DONE, DEFERRED, or N/A.

### Important Constraints

- **Minimal changes**: Only fix what the critique identified. Do not refactor, improve, or generalize beyond the specific finding.
- **Verify before claiming**: After each fix, run relevant tests. Unverified fixes are not DONE.
- **Do not re-critique**: If a fix reveals new issues, mark the original item DEFERRED and note the blocker. Do not expand scope.
- **Authorship**: All fixes are your own commits. Use feature branches if the repo supports it.

## Usage

```bash
/critique
# Critique whatever was just worked on (auto-detected from session context)

/critique on /critique
# Critique the /critique skill specifically
```
