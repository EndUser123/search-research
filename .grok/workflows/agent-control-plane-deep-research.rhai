let meta = #{
    name: "agent-control-plane-deep-research",
    description: "Deep-dive the 3 most promising agent control-plane enforcement specs, synthesize an integration architecture, and verify via cross-model panel.",
    phases: [
        #{ title: "Deep-dive", detail: "OAP spec, Earned Authority paper, Codex Windows sandbox — one agent each" },
        #{ title: "Synthesize", detail: "Integration architecture proposal from the 3 deep-dives" },
        #{ title: "Verify", detail: "Cross-model verification of the integration proposal" },
    ],
    when_to_use: "After a single-pass /www on agent control-plane enforcement; deepens the 3 highest-signal findings into implementable patterns.",
};

// Phase 1: Deep-dive the 3 most promising specs/patterns
phase("Deep-dive");

let deep_dive_jobs = [];

// Job 1: Open Agent Passport — implementation feasibility for our fleet
let oap_prompt = "You are researching the Open Agent Passport (OAP) specification for a multi-agent fleet.\n\n";
oap_prompt += "Fetch and read: https://arxiv.org/abs/2603.20953v1 (the OAP paper 'Before the Tool Call: Deterministic Pre-Action Authorization').\n";
oap_prompt += "Also search for: 'open agent passport specification implementation github' via python P:/.agents/scripts/ddgs_search.py.\n\n";
oap_prompt += "Evaluate for a fleet running Grok Build + Codex CLI + Antigravity CLI on a shared Windows filesystem:\n";
oap_prompt += "1. What does the before_tool_call hook actually intercept? Can it work across heterogeneous CLIs?\n";
oap_prompt += "2. What is the policy language (Rego? custom?) and how expressive is it?\n";
oap_prompt += "3. The paper reports 53ms median latency — is this acceptable for interactive agents?\n";
oap_prompt += "4. What are the stated limitations (Section 8 of the paper)?\n";
oap_prompt += "5. Is there a reference implementation we can evaluate?\n\n";
oap_prompt += "Return: a structured evaluation with sections for (a) what OAP provides, (b) implementation feasibility for our fleet, (c) gaps/limitations, (d) recommendation (adopt/adapt/wait).\n";
oap_prompt += "Use web_fetch or ddgs_search to get actual content — do not answer from memory.";

deep_dive_jobs.push(#{
    prompt: oap_prompt,
    label: "deep-dive:oap-spec",
    capability_mode: "read-only",
});

// Job 2: Earned Authority paper — map 6 mutation classes to fleet ops
let ea_prompt = "You are analyzing the paper 'Earned Authority under a Fixed Ceiling for Evolving Agents' (arxiv 2607.23586) for practical fleet application.\n\n";
ea_prompt += "Fetch and read: https://arxiv.org/abs/2607.23586v1.\n\n";
ea_prompt += "Map the paper's 6 mutation classes to concrete fleet operations:\n";
ea_prompt += "1. Control state mutation (model/provider switch) → when our fleet swaps models mid-task\n";
ea_prompt += "2. Capability mutation (new tool) → when an agent loads a new skill or MCP server\n";
ea_prompt += "3. Delegation mutation (subagent) → when /go spawns parallel subagents\n";
ea_prompt += "4. Task/phase mutation (edit→commit) → when the workflow transitions from implement to verify\n";
ea_prompt += "5. Trust context mutation (tool output → control input) → when hook output feeds back into agent decisions\n";
ea_prompt += "6. Enforcement mutation (sandbox change) → when config.toml or hooks are edited mid-session\n\n";
ea_prompt += "For each class, answer:\n";
ea_prompt += "- What triggers this mutation in our fleet?\n";
ea_prompt += "- What authorization consequence should it have?\n";
ea_prompt += "- How would we detect it mechanically (not via prose rules)?\n\n";
ea_prompt += "Also evaluate the non-amplification theorem: does 'agent-produced evidence cannot raise the ceiling' hold for our multi-agent fleet? What are the edge cases?\n\n";
ea_prompt += "Use web_fetch to read the actual paper. Return a structured mapping table plus analysis.";

deep_dive_jobs.push(#{
    prompt: ea_prompt,
    label: "deep-dive:earned-authority",
    capability_mode: "read-only",
});

// Job 3: Codex Windows sandbox — can we replicate it?
let codex_prompt = "You are evaluating the OpenAI Codex Windows sandbox architecture for multi-agent fleet use.\n\n";
codex_prompt += "Fetch and read: https://openai.com/index/building-codex-windows-sandbox/\n";
codex_prompt += "Also search for: 'codex windows sandbox synthetic SID write restricted token implementation' via python P:/.agents/scripts/ddgs_search.py.\n\n";
codex_prompt += "Evaluate replication feasibility for our fleet (3+ agents on shared Windows host):\n";
codex_prompt += "1. Exact mechanism: synthetic SIDs, write-restricted tokens, firewall rules, job objects — what are the PowerShell commands to set this up?\n";
codex_prompt += "2. Multi-agent scaling: the Codex sandbox was designed for single-agent. If we create separate SIDs for Grok, Codex, and Antigravity, what ACL management overhead results?\n";
codex_prompt += "3. Elevated vs unelevated: the elevated mode requires admin at setup. Is this acceptable for fleet-managed machines? What are the unelevated gaps?\n";
codex_prompt += "4. Interaction with our existing worktree-based isolation: can the two layers coexist?\n";
codex_prompt += "5. Any known issues or limitations from the community (check GitHub issues for codex)?\n\n";
codex_prompt += "Use web_fetch and ddgs_search to get actual content. Return: implementation recipe + multi-agent evaluation + recommendation.";

deep_dive_jobs.push(#{
    prompt: codex_prompt,
    label: "deep-dive:codex-windows-sandbox",
    capability_mode: "read-only",
});

let deep_results = parallel(deep_dive_jobs);

// Collect the outputs
let oap_eval = "";
let ea_eval = "";
let codex_eval = "";
let oap_ok = false;
let ea_ok = false;
let codex_ok = false;

if deep_results.len() >= 1 && deep_results[0] != () && deep_results[0].success {
    oap_eval = deep_results[0].output;
    oap_ok = true;
}
if deep_results.len() >= 2 && deep_results[1] != () && deep_results[1].success {
    ea_eval = deep_results[1].output;
    ea_ok = true;
}
if deep_results.len() >= 3 && deep_results[2] != () && deep_results[2].success {
    codex_eval = deep_results[2].output;
    codex_ok = true;
}

let ok_count = 0;
if oap_ok { ok_count += 1; }
if ea_ok { ok_count += 1; }
if codex_ok { ok_count += 1; }
log("Deep-dive phase: " + ok_count.to_string() + "/3 agents succeeded");

// Phase 2: Synthesize integration architecture
phase("Synthesize");

let synth_prompt = "You are an integration architect. Synthesize the following deep-dive evaluations into a single coherent enforcement architecture for a multi-agent fleet running Grok Build + Codex CLI + Antigravity CLI on a shared Windows filesystem.\n\n";

synth_prompt += "## Deep-dive 1: Open Agent Passport (OAP) evaluation\n";
synth_prompt += oap_eval;
synth_prompt += "\n\n## Deep-dive 2: Earned Authority paper analysis\n";
synth_prompt += ea_eval;
synth_prompt += "\n\n## Deep-dive 3: Codex Windows sandbox evaluation\n";
synth_prompt += codex_eval;

synth_prompt += "\n\n## Your task\n";
synth_prompt += "Produce an integration architecture that combines all three into a layered enforcement stack for our fleet. Address:\n";
synth_prompt += "1. How does OAP's before_tool_call hook integrate with Grok Build's hook system?\n";
synth_prompt += "2. How does the Earned Authority transition envelope map to workflow phases (discovery → plan → implement → verify → review)?\n";
synth_prompt += "3. How does the Codex sandbox pattern compose with existing worktree isolation?\n";
synth_prompt += "4. What is the MINIMUM viable subset to implement first (the 'balanced' configuration)?\n";
synth_prompt += "5. What are the integration risks and failure modes?\n";
synth_prompt += "6. What is the implementation order (what to build first, second, third)?\n\n";
synth_prompt += "Also produce a 'rejection criteria' section: what evidence would make you recommend NOT building this architecture?\n\n";
synth_prompt += "Be specific about implementation paths. This should be actionable, not theoretical.";

let synth_result = agent(synth_prompt, #{
    label: "synthesize:integration-architecture",
    capability_mode: "read-only",
});

let architecture = "";
let synth_ok = false;
if synth_result.success {
    architecture = synth_result.output;
    synth_ok = true;
    log("Synthesis phase: architecture proposal generated");
} else {
    log("Synthesis phase: FAILED — skipping verification");
}

// Phase 3: Cross-model verification
phase("Verify");

let verify_jobs = [];

if synth_ok {
    let json_arch = json_encode(architecture);

    // Verifier 1: Skeptic (find holes)
    let skeptic_prompt = "You are a skeptical security architect reviewing a proposed agent enforcement architecture.\n\n";
    skeptic_prompt += "Here is the architecture:\n" + json_arch + "\n\n";
    skeptic_prompt += "Your job is to find every hole, bypass, failure mode, and assumption that could be wrong.\n";
    skeptic_prompt += "For each issue found:\n";
    skeptic_prompt += "1. Name the issue\n";
    skeptic_prompt += "2. Explain how an agent could exploit or bypass it\n";
    skeptic_prompt += "3. Rate severity (critical/high/medium/low)\n";
    skeptic_prompt += "4. Propose a mitigation\n\n";
    skeptic_prompt += "Focus especially on:\n";
    skeptic_prompt += "- Can the model forge capability tokens?\n";
    skeptic_prompt += "- Can hook fail-open undermine the whole stack?\n";
    skeptic_prompt += "- Does the multi-agent fleet create coordination attacks?\n";
    skeptic_prompt += "- Are there TOCTOU races in the sandbox setup?\n";
    skeptic_prompt += "Be thorough. This architecture is for a production fleet with real consequences.";

    verify_jobs.push(#{
        prompt: skeptic_prompt,
        label: "verify:skeptic",
        capability_mode: "read-only",
    });

    // Verifier 2: Implementer (can we actually build this?)
    let impl_prompt = "You are a senior implementation engineer evaluating whether a proposed agent enforcement architecture can actually be built.\n\n";
    impl_prompt += "Here is the architecture:\n" + json_arch + "\n\n";
    impl_prompt += "Evaluate buildability:\n";
    impl_prompt += "1. What components already exist in our workspace (hooks, skills, scripts) that we can leverage?\n";
    impl_prompt += "2. What new code needs to be written? Estimate complexity (S/M/L) for each component.\n";
    impl_prompt += "3. What external dependencies are required?\n";
    impl_prompt += "4. What is the riskiest component to build and why?\n";
    impl_prompt += "5. Is there a simpler architecture that achieves 80% of the enforcement value with 20% of the effort?\n";
    impl_prompt += "6. What is a realistic implementation timeline (in sessions, not hours)?\n\n";
    impl_prompt += "Be honest about what's hard. Over-optimistic timelines waste more time than honest assessments.";

    verify_jobs.push(#{
        prompt: impl_prompt,
        label: "verify:implementer",
        capability_mode: "read-only",
    });
}

let verify_results = [];
let skeptic_output = "";
let impl_output = "";

if verify_jobs.len() > 0 {
    verify_results = parallel(verify_jobs);
    if verify_results.len() >= 1 && verify_results[0] != () && verify_results[0].success {
        skeptic_output = verify_results[0].output;
    }
    if verify_results.len() >= 2 && verify_results[1] != () && verify_results[1].success {
        impl_output = verify_results[1].output;
    }
    log("Verification phase: " + verify_results.len().to_string() + " verifiers completed");
}

// Write the final report
let report = "# Agent Control-Plane Enforcement: Deep Research Report\n\n";
report += "## Phase 1: Deep-Dive Evaluations\n\n";
report += "### Open Agent Passport (OAP)\n" + oap_eval + "\n\n";
report += "### Earned Authority Paper\n" + ea_eval + "\n\n";
report += "### Codex Windows Sandbox\n" + codex_eval + "\n\n";
report += "## Phase 2: Integration Architecture\n\n" + architecture + "\n\n";
report += "## Phase 3: Verification\n\n";
report += "### Skeptic Review\n" + skeptic_output + "\n\n";
report += "### Implementer Assessment\n" + impl_output + "\n\n";
report += "## Run Summary\n";
report += "- Deep-dive agents: " + ok_count.to_string() + "/3 succeeded\n";
report += "- Synthesis: " + if synth_ok { "succeeded" } else { "FAILED" } + "\n";
report += "- Verifiers: " + verify_results.len().to_string() + " completed\n";

let report_path = write_scratch_file("deep-research-report.md", report);

complete(#{
    summary: "Deep research complete: " + ok_count.to_string() + "/3 deep-dives + synthesis + " + verify_results.len().to_string() + " verifiers",
    report_path: report_path,
    deep_dive_success: ok_count,
    synthesis_success: synth_ok,
    verifiers_completed: verify_results.len(),
});
