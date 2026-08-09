let meta = #{
    name: "pecd-loop",
    description: "Iterative proposal-evidence-critique-deepen refinement loop. Generates improvement proposals, grounds them against external evidence, critiques the decisions, deepens uncertain items, and produces a final ship/refine/defer list with evidence.",
    phases: [
        #{ title: "Propose", detail: "generate candidate improvements" },
        #{ title: "Evidence", detail: "ground proposals against external research" },
        #{ title: "Critique", detail: "adversarial review: ship/refine/defer" },
        #{ title: "Operator Gate", detail: "operator reviews and selects items to deepen" },
        #{ title: "Deepen", detail: "targeted research on selected refine items" },
        #{ title: "Re-critique", detail: "re-evaluate deepened items" },
        #{ title: "Decide", detail: "emit final decisions" },
    ],
    when_to_use: "When you want to systematically improve skills, workflows, or architecture through an evidence-grounded iterative refinement cycle. Use /workflow pecd-loop topic='<your topic>'",
};

// Guard args — args may arrive as a map or as a unit value
let topic = "";
if args != () {
    let raw = args;
    if type_of(raw) == "string" {
        topic = raw;
    } else if raw.topic != () {
        topic = raw.topic;
    }
}
if topic == "" || topic == () {
    pause("verification", "Pass args with a topic — the improvement domain to analyze. Example: /workflow pecd-loop '{\"topic\":\"improve our SDLC skills\"}'");
}
let topic_str = json_encode(topic);

let proposal_schema = #{
    "type": "object", "required": ["proposals"],
    "properties": #{
        "proposals": #{ "type": "array", "maxItems": 10, "items": #{
            "type": "object", "required": ["id", "title", "description", "rationale"],
            "properties": #{
                "id": #{ "type": "string" },
                "title": #{ "type": "string" },
                "description": #{ "type": "string" },
                "rationale": #{ "type": "string" },
            },
        }},
    },
};

let evidence_schema = #{
    "type": "object", "required": ["findings"],
    "properties": #{
        "findings": #{ "type": "array", "maxItems": 10, "items": #{
            "type": "object", "required": ["id", "label", "evidence_summary"],
            "properties": #{
                "id": #{ "type": "string" },
                "label": #{ "type": "string", "enum": ["CONFIRMED", "EXTENDED", "NOVEL", "REFUTED"] },
                "evidence_summary": #{ "type": "string" },
                "enhancements": #{ "type": "string" },
            },
        }},
    },
};

let critique_schema = #{
    "type": "object", "required": ["decisions"],
    "properties": #{
        "decisions": #{ "type": "array", "maxItems": 10, "items": #{
            "type": "object", "required": ["id", "verdict", "reasoning"],
            "properties": #{
                "id": #{ "type": "string" },
                "verdict": #{ "type": "string", "enum": ["ship", "refine", "defer"] },
                "reasoning": #{ "type": "string" },
                "decision_question": #{ "type": "string" },
            },
        }},
    },
};

let deepen_schema = #{
    "type": "object", "required": ["verdicts"],
    "properties": #{
        "verdicts": #{ "type": "array", "maxItems": 10, "items": #{
            "type": "object", "required": ["id", "verdict", "evidence"],
            "properties": #{
                "id": #{ "type": "string" },
                "verdict": #{ "type": "string", "enum": ["UPGRADE", "CONFIRM_CURRENT", "CONFIRM_DEFER"] },
                "evidence": #{ "type": "string" },
            },
        }},
    },
};

// ─── Phase 1: Propose ───
phase("Propose");

let propose_prompt = "You are a thought partner analyzing improvement opportunities for: " + topic_str + ".\n\n";
propose_prompt += "Generate 5-10 concrete, actionable improvement proposals. For each:\n";
propose_prompt += "- State the problem it solves (with session evidence if available)\n";
propose_prompt += "- State the proposed improvement\n";
propose_prompt += "- State the rationale (why this matters)\n";
propose_prompt += "- State whether it's a code change, skill change, rule change, or workflow change\n\n";
propose_prompt += "Constraints:\n";
propose_prompt += "- Bias toward optimal long-term solutions, not minimal fixes\n";
propose_prompt += "- Each proposal should be independently actionable\n";
propose_prompt += "- If you see a pattern across multiple proposals, call it out as a meta-observation\n";
propose_prompt += "- Use DDG (python P:/.agents/scripts/ddgs_search.py) for any quick lookups\n\n";
propose_prompt += "Output as structured proposals with id, title, description, rationale.";

let propose_result = agent(propose_prompt, #{
    label: "propose",
    capability_mode: "read-only",
    output_schema: proposal_schema,
});

if !propose_result.success || propose_result.output == () || propose_result.output.proposals == () {
    complete(#{ summary: "PECD failed at Propose phase", error: "proposal agent failed" });
}

let proposals = propose_result.output.proposals;
let prop_count = proposals.len();
log("Generated " + prop_count.to_string() + " proposals");

// ─── Phase 2: Evidence ───
phase("Evidence");

let evidence_prompt = "You are validating improvement proposals against external evidence.\n\n";
evidence_prompt += "Topic: " + topic_str + "\n\n";
evidence_prompt += "Proposals to validate:\n";
for p in proposals {
    evidence_prompt += "- [" + p.id + "] " + p.title + ": " + p.description + "\n";
}
evidence_prompt += "\nFor each proposal:\n";
evidence_prompt += "1. Search the wiki (P:/.data/wiki/concepts/) for existing coverage\n";
evidence_prompt += "2. Search the web via DDG (python P:/.agents/scripts/ddgs_search.py '<query>' --max 5)\n";
evidence_prompt += "3. Label each: CONFIRMED (already known), EXTENDED (known + new insight), NOVEL (not covered), REFUTED (conflicts with evidence)\n";
evidence_prompt += "4. Note any actionable enhancements the external evidence suggests\n\n";
evidence_prompt += "Run searches in parallel where possible. Bias toward thorough research, not depth reduction.\n";
evidence_prompt += "Output structured findings with id, label, evidence_summary, enhancements.";

let evidence_result = agent(evidence_prompt, #{
    label: "evidence",
    capability_mode: "all",
    output_schema: evidence_schema,
});

if !evidence_result.success || evidence_result.output == () {
    complete(#{ summary: "PECD failed at Evidence phase", error: "evidence agent failed" });
}

let evidence_findings = evidence_result.output.findings;
log("Grounded " + evidence_findings.len().to_string() + " findings against external evidence");

// ─── Phase 3: Critique ───
phase("Critique");

let critique_prompt = "You are a critical friend reviewing improvement proposals that have been evidence-grounded.\n\n";
critique_prompt += "Topic: " + topic_str + "\n\n";
critique_prompt += "Proposals:\n";
for p in proposals {
    critique_prompt += "- [" + p.id + "] " + p.title + ": " + p.description + "\n";
    critique_prompt += "  Rationale: " + p.rationale + "\n";
}
critique_prompt += "\nEvidence findings:\n";
for f in evidence_findings {
    critique_prompt += "- [" + f.id + "] " + f.label + ": " + f.evidence_summary + "\n";
    if f.enhancements != () { critique_prompt += "  Enhancements: " + f.enhancements + "\n"; }
}
critique_prompt += "\nFor each proposal, apply TWO critique lenses:\n\n";
critique_prompt += "1. IMPLEMENTMENT CRITIQUE (existing): Is this well-evidenced? Not over-engineered? Correctly prioritized?\n";
critique_prompt += "2. DECISION CRITIQUE (new): What would make this proposal unnecessary? What assumption, if false, reverses it? Is there a simpler alternative?\n\n";
critique_prompt += "Label each: ship (ready to implement), refine (needs more evidence/changes), defer (not worth doing now).\n";
critique_prompt += "For each 'refine' item, state the specific decision question that needs answering.\n\n";
critique_prompt += "Also apply the Decision Integrity Check:\n";
critique_prompt += "- Is the solution frame locked in prematurely? (Are we assuming the solution shape?)\n";
critique_prompt += "- Are any blocking unknowns treated as carryable? (Recommendation depends on unverified assumptions?)\n";
critique_prompt += "- Is NEW being recommended without proof that reuse is worse?\n\n";
critique_prompt += "Output structured decisions with id, verdict, reasoning, decision_question (for refine items).";

let critique_result = agent(critique_prompt, #{
    label: "critique",
    capability_mode: "read-only",
    output_schema: critique_schema,
});

if !critique_result.success || critique_result.output == () {
    complete(#{ summary: "PECD failed at Critique phase", error: "critique agent failed" });
}

let critique_decisions = critique_result.output.decisions;

// Count verdicts
let ship_count = 0;
let refine_items = [];
let defer_count = 0;
for d in critique_decisions {
    if d.verdict == "ship" {
        ship_count += 1;
    } else if d.verdict == "refine" {
        refine_items.push(d);
    } else if d.verdict == "defer" {
        defer_count += 1;
    }
}

log("Critique: " + ship_count.to_string() + " ship, " + refine_items.len().to_string() + " refine, " + defer_count.to_string() + " defer");

// ─── Phase 4: Operator Gate ───
phase("Operator Gate");

let gate_msg = "Critique complete. Results:\n\n";
gate_msg += "SHIP (" + ship_count.to_string() + "): ready to implement\n";
for d in critique_decisions {
    if d.verdict == "ship" {
        gate_msg += "  - " + d.id + ": " + d.reasoning + "\n";
    }
}
gate_msg += "\nREFINE (" + refine_items.len().to_string() + "): need more evidence\n";
for d in refine_items {
    gate_msg += "  - " + d.id + ": " + d.decision_question + "\n";
}
gate_msg += "\nDEFER (" + defer_count.to_string() + "): not worth doing now\n";
for d in critique_decisions {
    if d.verdict == "defer" {
        gate_msg += "  - " + d.id + ": " + d.reasoning + "\n";
    }
}
gate_msg += "\nOptions:\n";
gate_msg += "1. Deepen all refine items (research each decision question)\n";
gate_msg += "2. Deepen specific items (type the IDs)\n";
gate_msg += "3. Ship the " + ship_count.to_string() + " ship items, defer the rest\n";
gate_msg += "4. Done — accept current state as final";

if refine_items.len() == 0 {
    log("No refine items — skipping deepen phase");
    complete(#{ summary: "PECD complete: " + ship_count.to_string() + " ship, " + defer_count.to_string() + " defer, 0 refine", proposals: proposals, evidence: evidence_findings, decisions: critique_decisions });
}

let operator_response = await_user("user", gate_msg);

// Parse operator response — check if they want to deepen
let response_str = json_encode(operator_response).to_lower();
let deepen_all = response_str.contains("1") || response_str.contains("deepen all") || response_str.contains("all");
let done = response_str.contains("3") || response_str.contains("4") || response_str.contains("done") || response_str.contains("ship") || response_str.contains("accept");

if done && !deepen_all {
    log("Operator chose to accept current state");
    complete(#{ summary: "PECD complete (operator-accepted): " + ship_count.to_string() + " ship, " + refine_items.len().to_string() + " refine (unaddressed), " + defer_count.to_string() + " defer", proposals: proposals, evidence: evidence_findings, decisions: critique_decisions });
}

// Determine which items to deepen
let items_to_deepen = [];
if deepen_all {
    items_to_deepen = refine_items;
} else {
    // Check for specific IDs mentioned
    for d in refine_items {
        if response_str.contains(d.id) {
            items_to_deepen.push(d);
        }
    }
    if items_to_deepen.len() == 0 {
        // If no specific IDs matched, deepen all as default
        log("No specific IDs matched — deepening all refine items");
        items_to_deepen = refine_items;
    }
}

log("Deepening " + items_to_deepen.len().to_string() + " items");

// ─── Phase 5: Deepen ───
phase("Deepen");

let deepen_jobs = [];
for item in items_to_deepen {
    let d_prompt = "Research this specific decision question about an SDLC improvement:\n\n";
    d_prompt += "Item: " + item.id + "\n";
    d_prompt += "Decision question: " + item.decision_question + "\n";
    d_prompt += "Context: " + item.reasoning + "\n\n";
    d_prompt += "Research plan:\n";
    d_prompt += "1. Search wiki for existing knowledge on this specific question\n";
    d_prompt += "2. Search DDG (python P:/.agents/scripts/ddgs_search.py) for external evidence\n";
    d_prompt += "3. Produce a verdict: UPGRADE (should ship with this evidence), CONFIRM_CURRENT (current approach is correct), CONFIRM_DEFER (should stay deferred)\n";
    d_prompt += "4. Cite specific sources\n";
    d_prompt += "Run 2-3 focused searches. Be thorough on this specific question.";

    deepen_jobs.push(#{
        prompt: d_prompt,
        label: "deepen:" + item.id,
        capability_mode: "all",
        output_schema: deepen_schema,
    });
}

let deepen_results = parallel(deepen_jobs);

// Collect deepen verdicts
let deepen_verdicts = [];
let i = 0;
for r in deepen_results {
    if r != () && r.success && r.output.verdicts != () {
        for v in r.output.verdicts {
            deepen_verdicts.push(v);
        }
    }
    i += 1;
}
log("Deepened " + deepen_verdicts.len().to_string() + " verdicts");

// ─── Phase 6: Re-critique ───
phase("Re-critique");

let re_critique_prompt = "Re-evaluate the deepened items and produce the final ship/refine/defer list.\n\n";
re_critique_prompt += "Original critique decisions:\n";
for d in critique_decisions {
    re_critique_prompt += "- [" + d.id + "] " + d.verdict + ": " + d.reasoning + "\n";
}
re_critique_prompt += "\nDeepen verdicts:\n";
for v in deepen_verdicts {
    re_critique_prompt += "- [" + v.id + "] " + v.verdict + ": " + v.evidence + "\n";
}
re_critique_prompt += "\nApply upgrades: items marked UPGRADE in deepen should move to 'ship' if the evidence supports it.\n";
re_critique_prompt += "Items marked CONFIRM_DEFER should stay deferred.\n";
re_critique_prompt += "Items marked CONFIRM_CURRENT need no changes.\n\n";
re_critique_prompt += "Produce the FINAL decisions list with updated verdicts.";

let re_critique_result = agent(re_critique_prompt, #{
    label: "re-critique",
    capability_mode: "read-only",
    output_schema: critique_schema,
});

let final_decisions = [];
if re_critique_result.success && re_critique_result.output != () && re_critique_result.output.decisions != () {
    final_decisions = re_critique_result.output.decisions;
} else {
    log("Re-critique agent failed — using original decisions + deepen verdicts");
    final_decisions = critique_decisions;
}

// ─── Phase 7: Decide ───
phase("Decide");

let final_ship = 0;
let final_refine = 0;
let final_defer = 0;
for d in final_decisions {
    if d.verdict == "ship" {
        final_ship += 1;
    } else if d.verdict == "refine" {
        final_refine += 1;
    } else {
        final_defer += 1;
    }
}

let report = "# PECD Loop Results: " + topic_str + "\n\n";
report += "## Summary\n\n";
report += "- **Proposals generated:** " + proposals.len().to_string() + "\n";
report += "- **Evidence-grounded:** " + evidence_findings.len().to_string() + "\n";
report += "- **Deepened:** " + deepen_verdicts.len().to_string() + "\n";
report += "- **Final: " + final_ship.to_string() + " ship, " + final_refine.to_string() + " refine, " + final_defer.to_string() + " defer**\n\n";
report += "## Final decisions\n\n";
for d in final_decisions {
    let icon = "?";
    if d.verdict == "ship" { icon = "SHIP"; }
    else if d.verdict == "refine" { icon = "REFINE"; }
    else { icon = "DEFER"; }
    report += "- **[" + icon + "]** " + d.id + ": " + d.reasoning + "\n";
}
report += "\n## Deepen verdicts\n\n";
for v in deepen_verdicts {
    report += "- **[" + v.verdict + "]** " + v.id + ": " + v.evidence + "\n";
}

let report_path = write_scratch_file("pecd-report.md", report);

complete(#{
    summary: "PECD complete: " + final_ship.to_string() + " ship, " + final_refine.to_string() + " refine, " + final_defer.to_string() + " defer",
    path: report_path,
    proposals: proposals,
    evidence: evidence_findings,
    decisions: final_decisions,
    deepen_verdicts: deepen_verdicts,
});
