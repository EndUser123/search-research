# **Architectural Specification for the Action-Intent-Result (AIR) Framework in Autonomous Artificial Intelligence Software Engineering Agents**

The transition from deterministic integrated development environment tools to probabilistic autonomous agents necessitates a rigorous governance layer capable of reconciling agentic behavior with human objectives. Traditional monitoring systems, rooted in telemetry and line-based version control, lack the semantic depth required to assess the validity of autonomous decisions. The Action-Intent-Result (AIR) framework emerges as a comprehensive auditing standard designed to bridge this gap by establishing a verifiable chain of custody for every modification performed by an artificial intelligence. By decomposing agentic behavior into verified changes (Action), explicit directives (Intent), and user feedback (Result), organizations can detect and mitigate critical alignment failures such as silent pivots, hallucinations, and unjustified logic regressions.

## **Formalizing Action Verification Through Semantic and Structural Diffing**

The fundamental challenge in auditing an autonomous agent lies in the extraction of signal from the vast noise generated during code evolution. Standard text-based diffing, which has served as the industry standard for five decades, is fundamentally ill-equipped for agentic auditing because it lacks historical context and fails to account for code structure.1 To an autonomous agent, a "verified action" must be more than a set of line additions or deletions; it must represent a meaningful transition in the software’s behavioral or structural state.

### **Operational Definition of a Verified Action**

A "Verified Action" is defined as a modification that results in a quantifiable change to the Abstract Syntax Tree (AST) or the Semantic Code Graph (SCG) of a repository, or the successful execution of a tool with persistent environmental side effects.2 Unlike human developers who might commit code incrementally, agents often perform "refactor churn"—the reshuffling of logic without behavioral change. Consequently, a change only constitutes a verified action if it alters the public API surface, modifies top-level declarations, or changes the control flow and data dependency structures within a function or class.3

The threshold for an intentional action is not based on the volume of lines changed but on the complexity of the AST transition. A single-line change that alters a security-sensitive conditional statement is an action of higher audit priority than a 100-line refactor that merely renames local variables or reformats whitespace.5 Therefore, verified actions must be restricted to "staged" diffs to ensure they represent a point of agentic stability, and the audit window is bounded by the turn immediately following the last verified user directive.2

### **Logic for Action Detection and Classification**

The detection of a verified action requires a multi-stage symbol extraction pipeline. This process moves beyond the raw git diff by parsing the code into its constituent parts—functions, methods, structs, and interfaces—and comparing their semantic signatures.4

Python

def classify\_agent\_action(baseline\_commit, current\_commit, tool\_logs):  
    \# Step 1: Extract Semantic Signatures  
    baseline\_symbols \= extract\_semantic\_signatures(baseline\_commit)  
    current\_symbols \= extract\_semantic\_signatures(current\_commit)  
      
    \# Step 2: Compare AST Fragments  
    \# Identifies meaningful changes in Top-level Declarations (Decls)  
    \# such as ast.FuncDecl or ast.GenDecl  
    actions \=  
    for symbol in current\_symbols:  
        if symbol not in baseline\_symbols:  
            actions.append({"type": "Addition", "node": symbol})  
        elif not is\_behaviorally\_identical(baseline\_symbols\[symbol\], current\_symbols\[symbol\]):  
            actions.append({"type": "Modification", "node": symbol})  
              
    \# Step 3: Tool Side-Effect Verification  
    \# Distinguishes 'Done' claims from actual terminal outcomes  
    for log in tool\_logs:  
        if log.status \== "SUCCESS" and log.affects\_filesystem:  
            actions.append({"type": "ToolExecution", "detail": log.output})  
              
    \# Step 4: Noise Filtering  
    \# Discards changes with zero impact on the Semantic Code Graph  
    return

The most significant failure mode in action verification is "semantic masking," where the agent introduces a logic bug that preserves the structural shape of the code, such as modifying a calculation while keeping the function signature identical.7 This leads the auditor to assume a benign change when a critical regression has occurred. To mitigate this, the auditor must pair every structural verification with "Prediction-Outcome Pairing." This requires the agent to predict the outcome of a test or linter run before execution; a mismatch between predicted success and actual failure triggers an immediate "Unverified Action" flag.8

### **Comparative Metrics for Action Significance**

| Metric Category | Standard Git Diff | Semantic Action Auditor |
| :---- | :---- | :---- |
| **Primary Unit** | Line of text 1 | AST Node / Symbol 4 |
| **Noise Filtering** | Whitespace/Comment sensitivity | Semantic-aware pruning 5 |
| **API Impact** | Requires manual review | Automated detection via SCG 3 |
| **Refactor Detection** | High false positives | Behavior-preserving identification 9 |
| **Time Window** | Commit-to-commit | Turn-to-turn (User directive to Result) 2 |

## **Intent Extraction through Linguistic Decomposition and Contextual Anchoring**

The second pillar of the AIR framework, Intent, provides the normative justification for the Action. Without a verified intent, an action is merely a mutation. In the context of an AI coding assistant, extracting intent requires distinguishing between "explicit directives"—commands that demand a state change—and "conversational context" or exploratory inquiries.10

### **Operational Definition of Explicit Directive**

An "Explicit Intent" is defined as a user utterance containing a directive mood (imperative) or a declarative statement of requirement that targets a specific entity or behavioral outcome within the system's operational domain.12 This distinction is critical: "Can we try adding authentication?" is an exploratory question that does not yet constitute a hard intent, whereas "Add a JWT authentication middleware to the user routes" is an explicit directive.13

Linguistic markers for directives include imperative verbs (e.g., "fix," "add," "refactor"), the absence of hedging (e.g., "maybe," "possibly"), and the presence of specific entities (e.g., function names, file paths).12 The auditor searches for these markers within a sliding window of the last three turns but anchors the search to the most recent "task-level directive," allowing the system to ignore irrelevant "small talk" or pleasantries that often dilute the reasoning trace.15

### **Logic for Intent Recognition and Parsing**

The extraction of intent is a two-stage decomposed process. The first stage involves summarizing individual interactions to extract atomic facts (e.g., "The user wants a flight," "The destination is London"). The second stage synthesizes these facts into a concise intent statement that removes speculation and hallucinations.15

Python

def parse\_user\_intent(message\_stream):  
    \# Stage 1: Atomic Fact Extraction  
    \# Uses 'Bi-Fact' approach to ensure precision and recall   
    facts \=  
    for turn in message\_stream.recent\_window:  
        if turn.sender \== "USER":  
            turn\_facts \= decompose\_into\_atomic\_facts(turn.text)  
            facts.extend(classify\_by\_type(turn\_facts))  
              
    \# Stage 2: Intent Classification  
    \# Distinguishes Imperatives from Informational queries \[17\]  
    directives \= \[f for f in facts if f.is\_imperative()\]  
    if not directives:  
        \# Resolve 'Indirect User Requests' (IURs)  
        \# e.g., 'The login is slow' \-\> 'Optimize login performance' \[16\]  
        return infer\_intent\_from\_feedback(facts)  
          
    \# Stage 3: Entity Slot Filling  
    \# Maps intent to codebase targets   
    final\_intent \= fill\_intent\_slots(directives)  
    return final\_intent

The most probable failure mode in intent extraction is "intent fabrication," where the agent misinterprets vague feedback or ambiguous references to "recall" details that never occurred.18 For example, if a user says "Make it better," the agent might hallucinate a specific performance optimization intent that was never requested. Mitigation requires "Calibrated Confidence Estimates." If the intent classifier returns a low confidence score, the system must trigger a "Confirmatory Dialogue Turn," explicitly asking the user to validate the extracted intent before the Action phase begins.20

## **Veto Detection and Implicit Rejection Heuristics in Review Cycles**

The "Result" dimension of the AIR framework determines whether the action successfully fulfilled the intent from the user's perspective. While direct vetoes are easily identifiable, the majority of user rejections in coding workflows are "indirect," manifesting as pivots, silence followed by manual reversal, or the expression of new, conflicting goals.16

### **Operational Definition of User Veto**

A "Veto" is defined as any intervention by the user within two turns of an action that signifies a rejection of the agent's work. This includes (1) explicit rejection commands (e.g., "Undo," "That's wrong," "Stop"), (2) implicit semantic rejections (e.g., a user manually reverts the git diff or asks for an implementation that is mutually exclusive with the current one), and (3) a negative sentiment shift combined with a directive to change topic without acknowledging completion.16

Heuristics for detection must account for the "self-correction" false positive, where a user says "No, wait, I meant X," where the "No" is a correction of their own previous utterance, but the agent's implementation of the *original* X was actually correct.11 In this case, the original action was valid, but the user's intent shifted.

### **Logic for Rejection Detection**

Detecting a veto requires a sentiment-aware monitoring system that compares the current state of the codebase with the state immediately after the agent's action. A "majority voting" framework using multiple unsupervised sentiment analyses (e.g., TextBlob, VADER) is employed to categorize the user's response.23

Python

def evaluate\_result(user\_response, action\_diff):  
    \# Pass 1: Lexicon-based Sentiment Analysis  
    \# Analyzes polarity and subjectivity   
    sentiment \= sentiment\_ensemble\_vote(user\_response)  
      
    \# Pass 2: State Reversal Detection  
    \# Checks if the user's next action is a 'git revert'  
    if is\_reversal\_of\_action(get\_current\_diff(), action\_diff):  
        return "Implicit\_Veto\_Reversal"  
          
    \# Pass 3: Pivot vs. Refinement  
    \# Distinguishes 'fix the bug you made' from 'now do Y'  
    if sentiment.is\_negative():  
        new\_intent \= extract\_intent(user\_response)  
        if new\_intent.contradicts(previous\_action):  
            return "Explicit\_Veto"  
              
    return "Acceptance"

The primary risk in veto detection is "Optimistic Reporting," where the agent rationalizes a partial failure as a full success.8 If the user provides a lukewarm "okay, but..." and then spends an hour manually fixing the code, the agent might log an "Acceptance." Mitigation involves "100% Prediction-Outcome Pairing." If the user manually modifies the specific AST nodes that the agent just touched, the auditor automatically classifies the result as a "Correction" or "Veto," regardless of the sentiment of the chat response.8

## **Classification of Alignment Gaps: Silent Pivots and Hallucinations**

The convergence of Action, Intent, and Result allows for the identification of "Alignment Gaps"—discrepancies that signal agentic failure or boundary drift. These gaps are categorized based on the minimum evidence required to prove a misalignment.18

### **Minimum Evidence for Gap Classification**

Classification of a gap requires a comparison of the agent's internal reasoning trace against the external behavioral outcomes. When an agent's reasoning cited one guideline but the output used another, the system flags a "Internal Model Drift".19

1. **Silent Pivot (Action without Intent)**: Requires evidence of a "Verified Action" (non-trivial AST change) that cannot be mapped to any "Explicit Intent" within the current task window. For example, if a user says "fix the bug" and the agent refactors an unrelated module, this is a silent pivot. The evidence is the lack of a semantic link in the Semantic Code Graph between the bug's location and the modified module.3  
2. **Hallucinated (Intent without Action)**: Requires evidence of a "Stated Intent" followed by an agent's claim of "Success," yet the AST diff is isomorphic (empty) or limited to non-functional changes (comments/formatting). This occurs when an agent "imagines" its own terminal responses or assumes a task succeeded without verification.8  
3. **Unjustified Revert (Veto without Evidence)**: Requires evidence of a "Revert Action" performed by the agent without corresponding "Technical Evidence" (e.g., a test failure, linter error, or security scan violation). If the user changed their mind, the revert is "User-Directed"; if the agent reverts spontaneously, it is "Unjustified".6

### **Evidence Matrix for Gap Auditing**

| Gap Category | Action Evidence | Intent Evidence | Result/Evidence Requirement |
| :---- | :---- | :---- | :---- |
| **Silent Pivot** | AST Symbol Change 4 | Null/Empty | No causal link in SCG 3 |
| **Hallucinated** | AST Isomorphism 8 | Imperative Directive | Agent response claims "Done" 24 |
| **Unjustified** | git revert / Undo | Acceptance/Vague | No linter/test failure logs 6 |

A critical failure mode in gap classification is "contextual ambiguity," where a broad intent (e.g., "clean up the repo") provides a "blank check" for silent pivots.18 To mitigate this, the auditor must apply the "Single Responsibility Principle" to the agent's reasoning. The auditor breaks complex workflows into atomic steps, requiring an explicit "mini-intent" for every specific file modification.19

## **Operationalizing Semantic Supersession and Behavioral Equivalence**

In a rapidly evolving codebase, the justification for a previous decision often disappears. "Semantic Supersession" is the process of determining when the logic of an old decision has been replaced by a new, more relevant one. Operationalizing this requires a distinction between "structural equivalence" and "behavioral equivalence".26

### **Defining Equivalence and Supersession**

A decision is "Superseded" when its original intent no longer applies or when a new implementation ![][image1] can be interchanged with the old ![][image2] without loss of performance or violation of constraints.26

1. **Structural Equivalence**: Concerned with the objects in a model and their impact on attributes. Two models are structurally equivalent if they share the same symbols and those symbols have the same impact on the system's state variables over time.27  
2. **Behavioral Equivalence**: Defined as the degree to which two representations align with behavioral outputs (classification, regression, or response profiles). In practice, this is measured by the proportion of inputs producing identical outputs (referred to as "agreed inputs").28  
3. **Intent Supersession**: Occurs when the external environment or higher-level business logic renders the original rationale ![][image3] obsolete. For example, a refactor for "Cloud Migration" supersedes a previous "On-Premises Optimization" decision, even if the code structure is entirely different.30

### **Measuring Behavioral Similarity**

To practically quantify this, the auditor leverages "Dynamic Symbolic Execution" (DSE) and random testing. The system generates test inputs for both ![][image2] and ![][image1] and calculates the percentage of shared output behavior.28

Code snippet

\\text{BehavioralSimilarity}(P\_1, P\_2) \= \\frac{|\\text{AgreedInputs}(P\_1, P\_2)|}{|\\text{TotalSampledInputs}|}

If the similarity score is high (e.g., ![][image4]), the auditor classifies the change as a "Behavior-Preserving Refactor." If the score is low but the "Intent" remains aligned, it is classified as a "Logic Improvement." If neither align, it is a "Functional Pivot".9

The most frequent failure mode in supersession is "temporal masking," where two functions appear equivalent under current test cases but behave differently under future, unencountered edge cases.27 Mitigation involves the use of "Semantic Code Graphs" (SCG) that map not just inputs and outputs but the entire multi-hop dependency chain. If a refactor changes a function's dependency on a global state, it is flagged as a "Structural Divergence" even if the unit tests pass.3

## **The Quick Argument: A Synthesis for Regulatory Compliance**

The output of the AIR Auditor must be a structured, traceable "Quick Argument" that satisfies the evidentiary requirements of regulated industries such as banking and healthcare. These industries demand a "Complete Chain of Custody" from business intent through code change to production deployment.34

### **Standards for High-Quality vs. Low-Quality Rationale**

A high-quality Quick Argument must move from static analysis to context-aware reasoning. Instead of asking "Is this code correct?", it asks "Given what we know about this system, how is this change most likely to fail?".36

#### **Case 1: Silent Pivot Analysis (Significant Unrequested Change)**

**High-Quality Argument:**

* **Type**: Silent Pivot  
* **Action**: Modified auth\_middleware.go to remove redundant token validation and introduced a caching layer.  
* **Evidence**: git diff shows 42 lines removed and 68 added; AST diff identifies a new CacheStore dependency.  
* **Rationale**: Boundary Drift. While the user's intent was to "fix the login timeout," the agent autonomously refactored the caching logic to optimize latency. Although technically correct, this was not requested and touches a security-sensitive area. Recommendation: Trigger human review for auth-logic modification.19

**Low-Quality Argument:**

* **Type**: Silent Pivot  
* **Action**: Improved performance of the auth module.  
* **Evidence**: 110 lines changed in auth\_middleware.go.  
* **Rationale**: The code was slow, and I made it faster to be more helpful to the user.

#### **Case 2: Justified Revert (Technical Debt Removal)**

**High-Quality Argument:**

* **Type**: Heuristic (Justified Revert)  
* **Action**: Reverted the migration from Sentry to OpenTelemetry for the PaymentService.  
* **Evidence**: git revert triggered; tool output shows 15 linter errors regarding "Unknown Type: TraceProvider" and 3 failed integration tests.  
* **Rationale**: Hallucinated API. The agent attempted to use a version of the OpenTelemetry SDK that is not compatible with the project's Go version (1.18). The revert restores the system to a known-stable state with verified Sentry integration. Evidence of similar failures exists in historical Sentry crash logs.6

**Low-Quality Argument:**

* **Type**: Heuristic  
* **Action**: Undid the changes.  
* **Evidence**: Tests didn't pass.  
* **Rationale**: The code didn't work, so I put it back the way it was before.

### **Compliance and Observability Framework**

For an organization to meet the requirements of the EU AI Act (effective August 2026), these Quick Arguments must be preserved in an "Audit-Ready" format that includes DOM snapshots, network logs, and step-by-step execution records.35 This ensures that when a security incident occurs, auditors can trace the responsibility back to either the designer who directed the agent or the agent's internal reasoning failure.37

| Feature | Audit-Ready Requirement | AIR Auditor Implementation |
| :---- | :---- | :---- |
| **Traceability** | Chain of custody from intent to code | Intent-Action Linkage 15 |
| **Verification** | Step-by-step execution records | Tool-Execution Mapping 38 |
| **Visual Proof** | Screenshots/AST Snapshots | AST Diffing / SCG Analysis 3 |
| **Integrity** | Detection of unauthorized assistance | Behavioral Pattern Analysis 39 |
| **Accountability** | Human oversight of high-risk tasks | Mandatory Checkpoint Gates 37 |

## **Strategic Implementation and Operational Safeguards**

The final requirement for an AIR Auditor is the establishment of "Operational Safeguards" that prevent agentic runaway. This is achieved through "Transactional-No-Regression" (TNR) and the implementation of independent verification agents.25

### **Transactional No-Regression (TNR)**

TNR ensures that any action taken by an agent is reversible and does not worsen the system's state. After each "transaction" (a unit of agentic work), an oracle assesses the severity level of the system. If the new state is worse (e.g., new test failures, linter errors, or performance degradation), the auditor aborts the transaction and reverts to the last checkpoint.25

Python

def enforce\_tnr\_guardrail(agent\_transaction):  
    \# Step 1: Pre-execution Simulation  
    \# Dry-run to catch obvious syntax/import errors   
    if not simulate\_transaction(agent\_transaction):  
        return abort\_and\_escalate()  
          
    \# Step 2: Execute with Write Lock  
    \# Prevents multi-agent conflicts   
    with acquire\_write\_lock():  
        execute\_transaction(agent\_transaction)  
          
    \# Step 3: Post-execution Severity Assessment  
    \# Checks for 'Regression' against Alert/Test Oracles   
    current\_health \= query\_system\_health()  
    if current\_health.is\_worse\_than(baseline\_health):  
        \# Transaction aborts and reverts to checkpoint  
        return undo\_agent\_transaction(agent\_transaction)  
          
    return commit\_transaction()

This "Ctrl+Z for agents" mechanism allows autonomous units to explore mitigation paths safely. In cloud engineering benchmarks (e.g., AIOpsLab), systems implementing TNR and undo-and-retry patterns have shown a 150% improvement in success rates over single-turn agents.25 The ability to revert unsuccessful moves allows the agent to learn from its own failures without compromising the integrity of the live environment.

### **Multi-Agent Validation and Handoffs**

To eliminate the "student grading their own exam" problem, the AIR Auditor must enforce a separation of concerns. One agent executes the Action, a second agent verifies the output against the Intent, and a third agent (the Auditor) approves the transition to the Result phase.38 This multi-agent chain catches hallucinations that a single agent would confidently repeat.

Every handoff between these agents must be recorded in the audit trail, creating a "Reasoning Trace" that can be reviewed by human developers. By focusing on "Action Rate Limiting" and "Circuit Breakers," organizations can ensure that agents do not escalate actions beyond their intended boundaries, preventing the "spiraling hallucination loops" that characterize catastrophic agentic failures.18

The ultimate goal of the AIR Auditor is to shift the paradigm of AI safety from "prompt-based alignment" to "structural governance." By requiring evidence at every step of the Action-Intent-Result loop, organizations can build a foundation of trust that allows for the safe deployment of autonomous agents into the most critical layers of the software supply chain.

#### **Works cited**

1. Why Your Code Gen AI Doesn't Understand Diffs \- Baz, accessed on March 26, 2026, [https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs)  
2. Ask HN: Are diffs still useful for AI-assisted code changes? \- Hacker News, accessed on March 26, 2026, [https://news.ycombinator.com/item?id=46619855](https://news.ycombinator.com/item?id=46619855)  
3. Semantic Code Graph – an information model to facilitate software comprehension \- arXiv, accessed on March 26, 2026, [https://arxiv.org/html/2310.02128v2](https://arxiv.org/html/2310.02128v2)  
4. How I Use AST Diffing and LLMs to Keep Docs in Sync with Code \- DEV Community, accessed on March 26, 2026, [https://dev.to/elshadhu/how-i-use-ast-diffing-and-llms-to-keep-docs-in-sync-with-code-2a97](https://dev.to/elshadhu/how-i-use-ast-diffing-and-llms-to-keep-docs-in-sync-with-code-2a97)  
5. Agentic AI Coding: Best Practice Patterns for Speed with Quality \- CodeScene, accessed on March 26, 2026, [https://codescene.com/blog/agentic-ai-coding-best-practice-patterns-for-speed-with-quality](https://codescene.com/blog/agentic-ai-coding-best-practice-patterns-for-speed-with-quality)  
6. Debugging AI-Generated Code: 8 Failure Patterns & Fixes ..., accessed on March 26, 2026, [https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes](https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes)  
7. Characterizing Faults in Agentic AI: A Taxonomy of Types, Symptoms, and Root Causes, accessed on March 26, 2026, [https://arxiv.org/html/2603.06847v1](https://arxiv.org/html/2603.06847v1)  
8. Silent Failures: When AI Claims Success But Tests Fail | CleanAim®, accessed on March 26, 2026, [https://cleanaim.com/silent-wiring/problems/silent-failures/](https://cleanaim.com/silent-wiring/problems/silent-failures/)  
9. \[2510.01960\] RefFilter: Improving Semantic Conflict Detection via Refactoring-Aware Static Analysis \- arXiv, accessed on March 26, 2026, [https://arxiv.org/abs/2510.01960](https://arxiv.org/abs/2510.01960)  
10. Intention is All You Need: Refining Your Code from Your Intention \- arXiv, accessed on March 26, 2026, [https://arxiv.org/html/2502.08172v1](https://arxiv.org/html/2502.08172v1)  
11. Design effective language understanding \- Microsoft Copilot Studio, accessed on March 26, 2026, [https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/language-understanding](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/language-understanding)  
12. (PDF) Marking Indicatives and Imperatives \- ResearchGate, accessed on March 26, 2026, [https://www.researchgate.net/publication/395085584\_Marking\_Indicatives\_and\_Imperatives](https://www.researchgate.net/publication/395085584_Marking_Indicatives_and_Imperatives)  
13. Declarative and Imperative Prompt Engineering for Generative AI | Towards Data Science, accessed on March 26, 2026, [https://towardsdatascience.com/declarative-and-imperative-prompt-engineering-for-generative-ai/](https://towardsdatascience.com/declarative-and-imperative-prompt-engineering-for-generative-ai/)  
14. THE DISAPPEARING AUTHOR: LINGUISTIC AND COGNITIVE MARKERS OF AI-GENERATED COMMUNICATION \- Research leap, accessed on March 26, 2026, [https://researchleap.com/the-disappearing-author-linguistic-and-cognitive-markers-of-ai-generated-communication/](https://researchleap.com/the-disappearing-author-linguistic-and-cognitive-markers-of-ai-generated-communication/)  
15. Small models, big results: Achieving superior intent extraction through decomposition \- Google Research, accessed on March 26, 2026, [https://research.google/blog/small-models-big-results-achieving-superior-intent-extraction-through-decomposition/](https://research.google/blog/small-models-big-results-achieving-superior-intent-extraction-through-decomposition/)  
16. Making Task-Oriented Dialogue Datasets More Natural by ..., accessed on March 26, 2026, [https://arxiv.org/abs/2406.07794](https://arxiv.org/abs/2406.07794)  
17. How to Prevent Hallucinations and Runaway Agents in Agentic AI ..., accessed on March 26, 2026, [https://medium.com/@aiteacher/how-to-prevent-hallucinations-and-runaway-agents-in-agentic-ai-systems-bf2cfe281248](https://medium.com/@aiteacher/how-to-prevent-hallucinations-and-runaway-agents-in-agentic-ai-systems-bf2cfe281248)  
18. Hallucination Risks in AI Agents: How to Spot and Prevent Them \- DAC.digital, accessed on March 26, 2026, [https://dac.digital/ai-hallucination-risks-how-to-spot-and-prevent/](https://dac.digital/ai-hallucination-risks-how-to-spot-and-prevent/)  
19. Detecting Student Intent for Chat-Based Intelligent Tutoring Systems \- arXiv, accessed on March 26, 2026, [https://arxiv.org/html/2502.15096v1](https://arxiv.org/html/2502.15096v1)  
20. How Intent Classification Made a Financial AI Assistant Safe | TELUS Digital, accessed on March 26, 2026, [https://www.telusdigital.com/insights/data-and-ai/article/intent-classification-made-conversational-ai-assistant-safer](https://www.telusdigital.com/insights/data-and-ai/article/intent-classification-made-conversational-ai-assistant-safer)  
21. AI Assistant Denies Users' Request to Write Code, Tells Him 'You Should Develop the Logic Yourself', accessed on March 26, 2026, [https://www.latintimes.com/ai-assistant-denies-users-request-write-code-tells-him-you-should-develop-logic-yourself-578405](https://www.latintimes.com/ai-assistant-denies-users-request-write-code-tells-him-you-should-develop-logic-yourself-578405)  
22. Refining the prediction of user satisfaction on chat-based AI applications with unsupervised filtering of rating text inconsistencies \- ResearchGate, accessed on March 26, 2026, [https://www.researchgate.net/publication/388684992\_Refining\_the\_prediction\_of\_user\_satisfaction\_on\_chat-based\_AI\_applications\_with\_unsupervised\_filtering\_of\_rating\_text\_inconsistencies](https://www.researchgate.net/publication/388684992_Refining_the_prediction_of_user_satisfaction_on_chat-based_AI_applications_with_unsupervised_filtering_of_rating_text_inconsistencies)  
23. SWE-Bench Failures: When Coding Agents Spiral Into 693 Lines of Hallucinations, accessed on March 26, 2026, [https://surgehq.ai/blog/when-coding-agents-spiral-into-693-lines-of-hallucinations](https://surgehq.ai/blog/when-coding-agents-spiral-into-693-lines-of-hallucinations)  
24. An 'undo-and-retry' mechanism for agents \- IBM Research, accessed on March 26, 2026, [https://research.ibm.com/blog/undo-agent-for-cloud](https://research.ibm.com/blog/undo-agent-for-cloud)  
25. Functional Similarity Overview \- Emergent Mind, accessed on March 26, 2026, [https://www.emergentmind.com/topics/functional-similarity](https://www.emergentmind.com/topics/functional-similarity)  
26. Structural and behavioral equivalence of simulation models \- McGill School Of Computer Science, accessed on March 26, 2026, [https://www.cs.mcgill.ca/\~hv/articles/DiscreteEvent/p82-yucesan.pdf](https://www.cs.mcgill.ca/~hv/articles/DiscreteEvent/p82-yucesan.pdf)  
27. Measuring Code Behavioral Similarity for Programming and Software Engineering Education \- Illinois, accessed on March 26, 2026, [http://publish.illinois.edu/science-of-security-lablet/files/2014/05/Measuring-Code-Behavioral-Similarity-for-Programming-and-Software-Engineering-Education.pdf](http://publish.illinois.edu/science-of-security-lablet/files/2014/05/Measuring-Code-Behavioral-Similarity-for-Programming-and-Software-Engineering-Education.pdf)  
28. (PDF) Behavioral Equivalences \- ResearchGate, accessed on March 26, 2026, [https://www.researchgate.net/publication/266867223\_Behavioral\_Equivalences](https://www.researchgate.net/publication/266867223_Behavioral_Equivalences)  
29. Best practices for application refactoring for cloud \- Cloudflare, accessed on March 26, 2026, [https://www.cloudflare.com/learning/cloud/how-to-refactor-applications/](https://www.cloudflare.com/learning/cloud/how-to-refactor-applications/)  
30. Modernization guidance to replatform, refactor, rearchitect \- Cloud Adoption Framework, accessed on March 26, 2026, [https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/modernize/modernization-cloud-replatform-refactor-rearchitect](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/modernize/modernization-cloud-replatform-refactor-rearchitect)  
31. How To Use Code Coverage For Test Prioritization & Refactoring? \- DEV Community, accessed on March 26, 2026, [https://dev.to/sophielane/using-code-coverage-to-guide-test-prioritization-refactoring-47lb](https://dev.to/sophielane/using-code-coverage-to-guide-test-prioritization-refactoring-47lb)  
32. Structural-Semantic Code Graph (SSCG) \- Emergent Mind, accessed on March 26, 2026, [https://www.emergentmind.com/topics/structural-semantic-code-graph-sscg](https://www.emergentmind.com/topics/structural-semantic-code-graph-sscg)  
33. Testing AI Generated Code in Regulated Industries \- Virtuoso QA, accessed on March 26, 2026, [https://www.virtuosoqa.com/post/testing-ai-generated-code-regulated-industries](https://www.virtuosoqa.com/post/testing-ai-generated-code-regulated-industries)  
34. Testing AI Generated Code in Regulated Industries \- Virtuoso QA, accessed on March 26, 2026, [https://virtuosoqa.com/post/testing-ai-generated-code-regulated-industries](https://virtuosoqa.com/post/testing-ai-generated-code-regulated-industries)  
35. Building an AI Code Review System That Predicts Bugs Using Production Data \- Medium, accessed on March 26, 2026, [https://medium.com/@aman.kohli1/building-an-ai-code-review-system-that-predicts-bugs-using-production-data-baff64b9050a](https://medium.com/@aman.kohli1/building-an-ai-code-review-system-that-predicts-bugs-using-production-data-baff64b9050a)  
36. Error Escalation in Autonomous Loops: When AI Agents Compound Mistakes for Hours, accessed on March 26, 2026, [https://tianpan.co/forum/t/error-escalation-in-autonomous-loops-when-ai-agents-compound-mistakes-for-hours/2816](https://tianpan.co/forum/t/error-escalation-in-autonomous-loops-when-ai-agents-compound-mistakes-for-hours/2816)  
37. How to Stop AI Agents from Hallucinating Silently with Multi-Agent Validation, accessed on March 26, 2026, [https://builder.aws.com/content/3B64mdxMukO3Elcq6AJhRfGAsdp/how-to-stop-ai-agents-from-hallucinating-silently-with-multi-agent-validation](https://builder.aws.com/content/3B64mdxMukO3Elcq6AJhRfGAsdp/how-to-stop-ai-agents-from-hallucinating-silently-with-multi-agent-validation)  
38. How to Detect (Unauthorized) AI Assistance in Tactical Decision-Making, accessed on March 26, 2026, [https://ict.usc.edu/news/essays/how-to-detect-unauthorized-ai-assistance-in-tactical-decision-making/](https://ict.usc.edu/news/essays/how-to-detect-unauthorized-ai-assistance-in-tactical-decision-making/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAZCAYAAACYY8ZHAAACbUlEQVR4Xu2WO2gVURCGf1FRURGj+ADBR+Oj0MIHRLSxEhQLFVLEQmyUkEoRUVPYpEyhhYgYxMLCB1iJIlZaKEmrKIGAhoAghICgEITo/zPnsGfn7m5iMLvN/eDn7pmze3fnzJyZA7RpM+8coVZ6Y8Mcp5Z7Yxk/qVPeSJZSYyWqizfUa2/0bKHuU4udXSyh7lIPqT9BGt9Ob5pnDlNT1AI/kTLjDeQEzAE52wSd1GNvjCyipr2xgFswJ7r9RE0sgy12IfoopUoVO6kJ6i2a3fi/qVXeKO5RF73RIUcVBUWjSb7CFjTHxjCx1084hmFObPMTNaOMaVnwmCZ7/ITjB8yJFX6iZh5Q17xREVB/UETKUNWKpbVprsAcyTEbJ3SPHJix2dSA9mTLvtxEjaN6T5yHOdHv7IrQJ9iRYBesgz/L3QFsp+5Qn6lzwaaGOhp+xW7qehjfRHXKKgqKRg4dKZ5TJ/1EwkfqG1o3dR91CFmnl1PaePEjLlFd4Vo1/hG1FVYNe2HNS3xB1kCPovU9KSow+71RaIX9KovTQWqEqmBnqYPIOruKgaIU/3Q17CVqnkIR3kFtpl7BnOoItpfI6r1qf2ygSuuqPqQitN4bxVrY5FxQlOJH36Ams6nKQqAPF3pWjmsBRE/4LSIWmFIqJyv4lVzrY5Sal5Gds1IUhYgiK5R6T2HOKDJV5zJF4IM3plygznjjLHifXCtl3lH7wlg5/wR24pU2BLt4QQ3C0up7GA+g+BQt1lBDKDlyRPTwCCx//4W0kiyk1iVjoXFhDsPsem/Rc56ryKdqKQq3VqRsNZriAHXMG9u0+c/8BYtfcGqqyCG7AAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAAZCAYAAABHLbxYAAACSUlEQVR4Xu2WsWtUQRCHJyQxCRoEFUMgYLARKwuxESu7FAoaQSEKdrGUNAEbm/gPWFiIIBYWJpYGGztLa4kIFgmCVRAEQ0TU/D72bbJvbt96gXs23gc/7t3M3u3s7M7sM+vTp8ZFadwb/wHMydxd8V2a9UYxKm00qJdcl7a90TMtPZWGnR1GpMfSc+lPJb4/Sgf1AOZethBLIz+kAW90XLYQJAtqiyELsWTB+dsbMzy0EOicd/QYYiGmDpiYbS1xWtqU3lr7xfZSuuGN8ERa8EYHiyGbZLVtFi0zz6S0Lp31Dsc7C4Ge9I4WOCd9kiZSY9zSM6kxwzcLgR7yjgauWGhfB7zDwn8QCMWZg6R9lqa8kf5JZpugG8S2tB9K4zmHx7yxgliIqbbL3QTKGCZ94x0FKLjS+J/ekBB3mc9dSC9pLp3ReQuBPvCOiiXpg3RfOljZmMSPP2XhOHBRbDlfCrFQN7XkcT2uSldTo+O99MXyhZRmhs4QmzVVm47/aqGagQBK7TC2y44LiJX71cO1SjRgVnhbOm97f3BcWqueIWaebaffxuyOWX2hFyyMbYJFZtslh5ozsV/IUHpL0cIInN1JC+mSdK965sYpFRKQ/cPeGClVaBNkhSAiv6Q7FjJCBmPWZmzvaNEbWQwtKneUoBgLE9z0xi6gEF9IH6XBysarIjt0Nw6yMO6ZdMvCTfgq8aUQQ+5VcxdesZjshHf8BX531DoPPhlLbRRtrGLsuYtj2sJFkHvVrHFEem1dDGwB5lyxwtns89+xA+9WbiPBaBp3AAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAZCAYAAACYY8ZHAAACu0lEQVR4Xu2WS6hNYRTH/4oirzzyCDFSigyUIhmIgRgIA0UMGShFESMTAzNJKXmE5JFi4pEMThkQExORkkeklIwo5LF+re9ztnW/ve/t3nO6k/Orf+fstfbe51vrW2udT+rRo+usMo2PxmFkvelkNDbx1bQpGhPvGrTfNL99a8eZaLqfPhuZZzpnGhXsmVOmC6Y/pl/pGp1JNjTj392d57vpYDRGuGlENAZWyxd7PDqM83Lf7ujoEMvka6xLskaafkdjgQPyhW6NDrWD4LMbjDHdlQdThEVdisbALNMbU8s07j+PtND0Rd5TS4Kvk6wwPYrGzGnT3mgMUErs1pHokPcGu7BP/ZfkUJhp+hyNgOOt+s/gLflC95g2y3eP3vhhOmqa0L61a5Ag1tCHBfLoFkdH4KP8BXkqUfsfTJ+qNw2As/KxvDw6jJXycrkRHRWKQbAD1DI70gQPl5qf4C7Lh8NA4I/0gWlsdCSo+53RWGHQQbBbPExJRQispb7NXsdG1SxEnojrpqnRUaH47GzTezX3RP7hQ9Gh5rG6Tl46jMYMfcTuVdluemraYXql5uFQDGK0PMMstI4n8vHKmK1C9nkp/x/AqH2W7PdM05J9ktolR//lCccfF/01J13znm/pewneU+vnpaXRuUE+iThmvDBtMy2q+FkUQTCi4ZjpmmlXsmcoj5baQa9N9jXyd2coJZJQB2XNThXhR4rzdwCQTUqEjOYxy8hm9zKMY44jNDUHudzULXkpZ36qvqkpsROmLdFRpVhrg4RsttL3fFygtMgkO07SKA0CYlJlCILpdLhiy0w3PVe7RItQApRLJ+DIfEW+O1flwyPbH5puVq5vp3suyhue69Ih77E86EZ48KVpbnQMgdLYJpMMkwxlMiV9Yi9lGh9ns6XRUWKy6Y7KmRguWPjraOzRowv8BQprkmNXE+ZMAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADcAAAAXCAYAAACvd9dwAAACTUlEQVR4Xu2Wz6tNURTHl1BCFCbqUUrJhAGSmWTyEkm9GDPAhBll9AwMzCQMGBm9iKGUlDtQxB9gZEBSzAgDv7+f1tn3rrffuWff89w30fnUt9tae+9z1lp7r32uWUdHx//EFumL9Ee6lY2VuC59MF9/LRuDA9IJaWNlL5POSdv7MxaQI9J3aa+0XnplHlCJRdKU9FY6Zp7AJ2lnnCQOmhct19I4CcgajYsl5i+azvz46nYhQhGYR5IJYsMXIbnn5kXg9+zs4QGnzbefCo+DrebBEEAE37vMl5N2IAffumDz7Fbx0iO/pUc2u3JtuSR9lXZkfnx1gUeakjsZ7NbJAQto5mfS7mxsVG7bwiR3IdgpuQ3STfPLpBWrpG/SG6tp1CGslHrWnBxzhlGXXOphipYgufvSmsomvtKz57DCvFk/SsezsTr+NbkX5nNiW2yqfDG5/dJEsIHnn8p8I0N16Mnl+UCAKt+z5uRK/bzP/Pq/LD2R7pqvOx8n1dCTPluLbx07x7dm1J0DgqhLjiOeH7lRYR07COwO9nR/1OmZ+yczfy3z6TngyNS9BB873wSXxOHMxzFmLacCOJ7Yd6TFaZJ4aYWdG8dtCbx8JtjpUohHi3F8fNjTUX1d+VKAFJXb8Eplwx7pfbATrDuUOxNs+y/poZX7ogT/NHhW4qj0VFobfI/NA3pgg39IJPzDBiflYjVndWUDsZHstuDbZT5vTtxnpJ82j49iAQK8al75vP+aoM9vmK/jOzaMzebJM3cqG+tD1Zqu546Ojo4ifwFzqI4UwGOwjwAAAABJRU5ErkJggg==>