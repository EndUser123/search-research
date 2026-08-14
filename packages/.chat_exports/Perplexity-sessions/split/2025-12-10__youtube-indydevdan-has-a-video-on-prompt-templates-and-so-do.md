---
title: "youtube indydevdan has a video on prompt templates.  And so do some other people.  Please show me what the current best "
date: "2025-12-10"
mode: "COPILOT"
uuid: "da8d6277-81ab-4074-9630-40a61172982d"
entry_count: 1
---

## Human

youtube indydevdan has a video on prompt templates.  And so do some other people.  Please show me what the current best practices are for LLM prompt templates.

## Assistant

# Best Practices for LLM Prompt Templates (2025)

The main takeaway: **treat prompts as modular, typed “APIs”** rather than ad‑hoc strings. Define clear structure (roles, inputs, constraints, outputs), reuse it as templates, and iterate with the model itself as your prompt reviewer.

Below is a concise synthesis of current best practices from recent guides, API docs, and practitioner content.[1][2][3][4][5]

***

## 1. Treat Prompts as Structured Contracts, Not Free‑Form Text

Modern guidance (including Google Gemini’s docs and multiple 2025 prompt-engineering tutorials) emphasizes **precision and structure** over clever wording.[2][3][5][1]

Core ideas:

- **Be precise and direct.** Avoid fluffy language; state the goal in 1–2 sentences at the top.[5][1]
- **Use a consistent internal structure** within each template, e.g. headings or tags:
  ```text
  <role>...</role>
  <context>...</context>
  <task>...</task>
  <constraints>...</constraints>
  <output_format>...</output_format>
  ```
  XML‑style tags or Markdown headings work well; just be consistent per template.[2][5]
- **Prioritize critical instructions early.** Role, safety constraints, and output format should appear at the very start or in the system block.[1][5]

This “contract” framing is especially important when you start to compose prompts programmatically and pass them between tools or agents.

***

## 2. Use a Standard Template Skeleton

Across sources, good prompts tend to share the same components.[3][4][5][1][2]

A practical skeleton for a *single-turn* template:

1. **Role / Persona**  
   “You are an experienced \<X\> helping \<Y\>.” This narrows behavior and tone.[3][5][1]

2. **High-Level Task**  
   A single sentence: “Your task is to …”. Avoid bundling multiple unrelated tasks; instead, chain calls when possible.[4][1][2]

3. **Context**  
   Only what is necessary: data, user profile, constraints, environment. Use clear delimiters:
   ```text
   <context>
   ...
   </context>
   ```

4. **Explicit Constraints & Policies**  
   Style, depth, length, safety rules, what to avoid.  
   Example: “Be concise, use markdown headings, no external URLs, no emojis.”

5. **Output Format**  
   This is one of the biggest improvements in 2024–2025 guidance:
   - Specify **structure** (JSON / markdown / sections).
   - Include an explicit schema if machine‑consumed.
   - For code, specify language and where to focus.[5][2][3]

6. **Examples (Few‑Shot) – Optional but Powerful**  
   For nontrivial tasks, add 1–3 input/output examples that match your desired behavior.[4][2][5]

7. **Final User Input / Variables**  
   Keep your variable slots clearly marked, e.g. `{{user_query}}`, `{{code_snippet}}`.

That skeleton generalizes across ChatGPT, Gemini, Claude, etc., and maps nicely to “prompt objects” in code.

***

## 3. Design Templates as Modular, Typed “APIs”

Rather than one monolithic super‑prompt, best practice is **modularity**.[4][5]

Patterns:

- **Template types**: e.g. `analysis_prompt`, `refinement_prompt`, `critic_prompt`, `planner_prompt`, `tool_router_prompt`. Each has its own schema.
- **Composable sub‑blocks**:
  - Shared safety block.
  - Shared formatting block (markdown rules, citations, JSON schema).
  - Task‑specific instructions.
- **Variables with types**:
  - `{{language}}` (enum), `{{max_words}}` (int), `{{audience_level}}` (enum), etc.
- Keep templates in **text files or config** rather than hard‑coded strings; this is exactly what systems like IndyDevTools’ Simple Prompt System encourage.[6]

This makes it far easier to:
- Swap models without changing business logic.
- Version, diff, and test prompts.
- Dynamically compose different behaviors in an agentic system.

***

## 4. Leverage Structured Delimiters and Output Schemas

A recurring recommendation in 2025 talks and docs is to **lean into structure** wherever possible.[2][3][5]

For input:

- Use delimiters to separate blocks:
  ```text
  ### CONTEXT
  ...
  ### TASK
  ...
  ### OUTPUT FORMAT
  ...
  ```
  or XML‑like tags (`<context>`).[5][2]

For output:

- Define explicit schemas for machine‑readable responses:
  ```text
  Return a JSON object with this exact shape:

  {
    "summary": string,
    "risk_level": "low" | "medium" | "high",
    "action_items": [
      {
        "owner": string,
        "description": string,
        "due_date": string | null
      }
    ]
  }
  ```
- If you need markdown, specify the **headings and sections** required, and constraints like “no introduction section”, “no links”, etc.[3][5]

This improves reliability, simplifies parsing, and reduces hallucinated fields.

***

## 5. Separate System‑Level Behavior from User‑Level Tasks

Most modern APIs distinguish **system** vs **user** messages. Current best practices:

- Put **global behavior, safety rules, persona defaults, formatting policies** in the system prompt.
- Keep the **user prompt focused on the specific task and context**.
- Avoid re‑stating the same long safety block in every user-level template; reuse via system or shared header.

Google’s Gemini docs explicitly recommend putting critical instructions (role, behavior, important constraints) in the system instruction or at the beginning of the prompt.[5]

For multi‑agent or chain setups, have **different system prompts per agent type**: “planner”, “researcher”, “coder”, “critic”, etc.

***

## 6. Design for Iteration, Self‑Critique, and Chains

Instead of trying to get everything in one shot, current practice is to **chain prompts** and use the model’s own self‑reflection.[7][1][2][4]

Patterns:

- **Self‑critique and refinement**:  
  First call: generate answer.  
  Second call (or second message): “Review the answer above. Find issues, edge cases, and improve it.”[1][2]
- **Planning + Execution**:  
  1st template: “Plan steps to solve X.”  
  2nd template: “Execute step 1 given this context,” etc.[7]
- **Summarize → Analyze**:  
  First template performs extraction/summarization, second performs higher‑order reasoning.

Prompt templates should explicitly anticipate where they fit:
- “This template expects prior context: `{{raw_answer}}`.”
- “This is a critic template; do not restate the original user query.”

***

## 7. Specify Level of Detail, Audience, and Style

Several 2025 guides emphasize **audience specification and depth control** as key levers.[1][2][3][5]

Include fields for:

- **Audience**: “nontechnical manager”, “senior backend engineer”, “law student”, etc.
- **Depth**: “high‑level overview”, “step-by-step tutorial”, “code‑heavy, minimal prose”.
- **Tone**: “neutral and professional”, “friendly and concise”, etc.
- **Verbosity controls**: max word count, number of bullets, whether to include examples.

This makes the template reusable across use cases by just swapping variables.

***

## 8. Keep Context Minimal but Sufficient

Especially with long-context models, it is tempting to dump everything. Current recommendations:[3][4][5]

- **Include only what the model needs** for the current subtask.
- For long documents or codebases:
  - Summarize or extract relevant sections first.
  - Then feed those into a more specialized template.
- Place **context first, question last**, with an explicit bridge like “Based on the context above, …” as recommended in Gemini docs.[5]

This reduces distraction and lowers the risk of the model latching onto irrelevant details.

***

## 9. Build Feedback Loops into Your Template Design Process

A powerful 2025 pattern is using the **LLM itself to critique and improve your templates**.[2][4]

Common techniques:

- **Prompt critique**: Feed the template to the model with meta‑instructions:
  > “Here is a prompt template. Point out any ambiguity, missing constraints, or conflicting instructions. Suggest revisions.”
- **Multiple rewordings**: Ask the same model or different models to rewrite your template and compare outcomes.[2]
- **AB testing**: In code, log:
  - Which template version was used.
  - Model responses + downstream success metrics.
  Then iterate and keep the variants that perform better.

Over time, templates become more like **versioned, tested configuration artifacts**.

***

## 10. Operational & Security Best Practices for Templates

Recent guides aimed at professionals and enterprises stress **security and governance**.[3]

Key points:

- **Centralize templates** in a repo or config layer with:
  - Versioning (git, etc.).
  - Code review / approval for changes.
- **Redact or avoid hard‑coding secrets** or identifying data in templates; keep them parameterized.
- Include **safety instructions** in shared blocks:
  - “Do not fabricate legal or medical advice; instead, recommend contacting a professional.”
  - “If insufficient information, ask clarifying questions rather than guessing.”
- For multi‑tenant apps, ensure any **user‑specific context is passed as variables**, never baked into shared templates.

***

## 11. Concrete Example: Modern Prompt Template Pattern

Putting it together, a reusable template might look like:

```text
<role>
You are an expert {{domain}} assistant helping a {{audience}}.
Respond in {{language}}.
</role>

<task>
Your task is to {{primary_task}}.
</task>

<context>
{{context_block}}
</context>

<constraints>
- Be {{tone}}.
- Depth: {{depth_level}}.
- Ask for clarification if critical information is missing.
- If unsure, say so explicitly rather than guessing.
</constraints>

<output_format>
Return markdown with the following sections:

1. Main Recommendation (2–3 sentences)
2. Detailed Steps
3. Risks & Edge Cases
4. (Optional) Code Snippets – only if directly relevant

Do not include external URLs.
</output_format>

<examples>
{{few_shot_examples_optional}}
</examples>

<user_input>
{{user_query}}
</user_input>
```

In code, you’d render this with your templating engine (Jinja2, handlebars, etc.) and store it in a prompt registry or CLI tool like IndyDevTools’ Simple Prompt System.[6]

***

## 12. How This Relates to “Prompt Templates” Videos (incl. IndyDevDan)

Recent YouTube content on prompt templates, including coding‑oriented channels and general prompt‑engineering talks, aligns on these themes:[8][7][1][2]

- Pre‑define **roles, arguments, model parameters, and message layout** in reusable templates rather than ad‑hoc calls.[8][6]
- Treat templates like **CLI commands / functions** with aliases and named arguments (e.g., `idt sps` templates).[6]
- Emphasize:
  - Structure over prose.
  - Explicit output formats.
  - Iterative refinement chains.
  - Using the model to help design and debug prompts.[7][1][2]

***

If you share how you are currently structuring your templates (e.g., system vs user blocks, how you pass variables in your orchestration layer), a set of domain‑specific “canonical templates” could be drafted that align with these best practices but plug directly into your existing stack.
