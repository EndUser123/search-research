# /tp cross-model critique context

**Generated:** 2026-08-05T15:44:05Z
**Packed for:** agy
**Session:** unknown

This file contains everything needed for a cross-model critique.
Read it in full, then produce your critique per the protocol above.

---
## Critique target

**Target:** Retry-with-fallback-model pattern in ship-rhai.rhai and ship-py orchestrator. Failed review/verify agents get retried once with a different model before the both-failed gate blocks.
**Horizon:** all
**Confidence:** medium

---

## Context bundle (verified facts, constraints, prior rejections)

Operator goal: add bounded retry-with-fallback to ship pipelines per P:/docs/handoffs/ship-rhai-retry-fallback-20260805/HANDOFF.md. Rules: cap 1 retry, different model, dont block on single failure, only load-bearing agents. ship-rhai.rhai: deterministic Rhai retry. ship-py: advisory retry + new review subcommand + review-failure gate.

---

## Git diff (a0da067~1..a0da067)

```diff
diff --git a/skills/ship-py/__lib/ship_orchestrator.py b/skills/ship-py/__lib/ship_orchestrator.py
index a51e279..bfa6c8c 100644
--- a/skills/ship-py/__lib/ship_orchestrator.py
+++ b/skills/ship-py/__lib/ship_orchestrator.py
@@ -78,7 +78,15 @@ def cmd_detect(args: argparse.Namespace) -> int:
         rc_branch, branch = _git(repo_path, "branch", "--show-current")
         rc_status, status = _git(repo_path, "status", "--short")
         rc_log, log = _git(repo_path, "log", "--oneline", "-5")
-        rc_diff, diff_stat = _git(repo_path, "diff", "--stat", "HEAD~5")
+
+        # Merge-base detection (aligned with ship_receipt.py + ship-rhai.rhai).
+        # Using HEAD~5 is too broad on multi-agent hosts — it captures other
+        # sessions' commits. merge-base with origin/main scopes correctly.
+        rc_mb, mb = _git(repo_path, "merge-base", "HEAD", "origin/main")
+        if rc_mb != 0 or not mb:
+            rc_mb, mb = _git(repo_path, "merge-base", "HEAD", "main")
+        diff_ref = mb if (mb and mb != head) else "HEAD~5"
+        rc_diff, diff_stat = _git(repo_path, "diff", "--stat", diff_ref)
 
         files_changed = []
         if status:
@@ -111,11 +119,21 @@ def cmd_detect(args: argparse.Namespace) -> int:
     if has_work or not args.health_check:
         instructions.append({
             "action": "spawn_review_agents",
-            "detail": "Spawn 2 read-only subagents in parallel: "
-                      "(1) parent-review: correctness + integrity lens, "
-                      "(2) specialist-review: architecture + test coverage lens. "
-                      "Both should read the diff using read_file/grep, not answer from memory. "
-                      "Collect findings as bugs (with severity), risks, and suggestions.",
+            "detail": (
+                "Spawn 2 read-only subagents in parallel with DIFFERENT models: "
+                "(1) parent-review: correctness + integrity lens, "
+                "(2) specialist-review: architecture + test coverage lens. "
+                "Both should read the diff using read_file/grep, not answer from memory. "
+                "Collect findings as bugs (with severity), risks, and suggestions.\n"
+                "RETRY-WITH-FALLBACK: if any agent fails (empty output, error, timeout), "
+                "retry ONCE with a different model from the pool. Cap: 1 retry per agent. "
+                "Do NOT block the pipeline on a single agent failure — proceed with partial "
+                "results if at least 1 agent succeeded.\n"
+                "RECORD: write findings JSON to P:/tmp/ship-py-review-findings.json, then run: "
+                "python ship_orchestrator.py review --session-id <UUID> "
+                "--findings-file P:/tmp/ship-py-review-findings.json "
+                "--agent-count 2 --failed-count <N>"
+            ),
             "next_phase": "review",
         })
     else:
@@ -144,6 +162,89 @@ def cmd_detect(args: argparse.Namespace) -> int:
     return 0
 
 
+# ---------------------------------------------------------------------------
+# Phase: REVIEW — record findings from spawned agents (deterministic gate)
+# ---------------------------------------------------------------------------
+
+def cmd_review(args: argparse.Namespace) -> int:
+    """Record review findings and apply the review-failure gate.
+
+    The LLM spawns review agents per the detect-phase instructions, collects
+    findings, writes them to a JSON file, then calls this subcommand. This
+    closes the gap where the LLM had to edit the state JSON manually.
+
+    Review-failure gate: if ALL agents failed (failed_count >= agent_count),
+    block the pipeline — same contract as ship-rhai.rhai's both-failed gate.
+    """
+    state = load_state()
+    if not state:
+        print(json.dumps({"error": "No state file. Run detect first."}))
+        return 1
+
+    # Read findings from file (Windows-safe — avoids CLI JSON quoting issues)
+    findings_path = Path(args.findings_file)
+    if not findings_path.exists():
+        print(json.dumps({"error": f"Findings file not found: {findings_path}"}))
+        return 1
+
+    try:
+        findings = json.loads(findings_path.read_text(encoding="utf-8"))
+    except (json.JSONDecodeError, OSError) as e:
+        print(json.dumps({"error": f"Cannot parse findings file: {e}"}))
+        return 1
+
+    agent_count = args.agent_count or 2
+    failed_count = args.failed_count or 0
+    succeeded_count = agent_count - failed_count
+    partial_failure = failed_count > 0 and succeeded_count > 0
+
+    state["review_findings"] = findings
+    state["review_failed_count"] = failed_count
+    state["review_agent_count"] = agent_count
+    state["review_partial_failure"] = partial_failure
+
+    bugs = findings.get("bugs", [])
+    risks = findings.get("risks", [])
+
+    # Review-failure gate: ALL agents failed → block (no unreviewed diff ships)
+    if succeeded_count == 0:
+        state["phase"] = "blocked"
+        save_state(state)
+        print(json.dumps({
+            "phase": "review",
+            "status": "BLOCKED",
+            "reason": f"All {agent_count} review agents failed — "
+                      "cannot proceed with unreviewed diff",
+            "next_action": "report_blocked",
+            "detail": "Retry with fallback models was attempted but all agents failed. "
+                      "Check quota and model availability before retrying.",
+        }, indent=2))
+        return 2
+
+    state["phase"] = "fix" if bugs else "verify"
+    save_state(state)
+
+    detail_parts = [f"{len(bugs)} bugs, {len(risks)} risks found"]
+    if partial_failure:
+        detail_parts.append(
+            f"PARTIAL: {failed_count} of {agent_count} review agents failed "
+            f"— proceeding with results from {succeeded_count} agent(s)"
+        )
+
+    print(json.dumps({
+        "phase": "review",
+        "bugs": len(bugs),
+        "risks": len(risks),
+        "partial_failure": partial_failure,
+        "agents_succeeded": succeeded_count,
+        "agents_failed": failed_count,
+        "next_action": "spawn_fix_agent" if bugs else "run_verify",
+        "next_phase": "fix" if bugs else "verify",
+        "detail": ". ".join(detail_parts),
+    }, indent=2))
+    return 0
+
+
 # ---------------------------------------------------------------------------
 # Phase: VERIFY — run mechanical checks (deterministic)
 # ---------------------------------------------------------------------------
@@ -155,6 +256,22 @@ def cmd_verify(args: argparse.Namespace) -> int:
         print(json.dumps({"error": "No state file. Run detect first."}))
         return 1
 
+    # Review-failure gate: if this is not a health-check, review findings
+    # MUST exist. If the LLM skipped the review phase (or all agents failed
+    # without recording), block — no unreviewed diff ships.
+    is_health_check = state.get("health_check", False)
+    if not is_health_check and "review_findings" not in state:
+        state["phase"] = "blocked"
+        save_state(state)
+        print(json.dumps({
+            "phase": "verify",
+            "status": "BLOCKED",
+            "reason": "Review findings missing on a non-health-check run — "
+                      "run the review phase first (detect → review → verify)",
+            "next_action": "run_review_phase",
+        }, indent=2))
+        return 2
+
     state["phase"] = "verify"
 
     # Write phase log
@@ -271,6 +388,15 @@ def main() -> int:
     p_detect.add_argument("--session-id", required=True, help="Session UUID")
     p_detect.add_argument("--health-check", action="store_true")
 
+    p_review = sub.add_parser("review", help="Phase 1: record review findings")
+    p_review.add_argument("--session-id", required=True, help="Session UUID")
+    p_review.add_argument("--findings-file", required=True,
+                          help="Path to JSON file with {bugs, risks, suggestions}")
+    p_review.add_argument("--agent-count", type=int, default=2,
+                          help="Total review agents spawned (default 2)")
+    p_review.add_argument("--failed-count", type=int, default=0,
+                          help="Number of agents that failed (default 0)")
+
     p_verify = sub.add_parser("verify", help="Phase 3: run mechanical checks")
     p_verify.add_argument("--session-id", required=True, help="Session UUID")
 
@@ -281,6 +407,8 @@ def main() -> int:
 
     if args.cmd == "detect":
         return cmd_detect(args)
+    elif args.cmd == "review":
+        return cmd_review(args)
     elif args.cmd == "verify":
         return cmd_verify(args)
     elif args.cmd == "verdict":
diff --git a/workflows/ship-rhai.rhai b/workflows/ship-rhai.rhai
index 24d6083..4f1dc06 100644
--- a/workflows/ship-rhai.rhai
+++ b/workflows/ship-rhai.rhai
@@ -48,19 +48,79 @@ let verify_schema = #{
 // --- Args ---
 // args may arrive as a map object or as a JSON string depending on the
 // workflow tool's serialization. Handle both cases.
+//
+// String case is parsed minimally with index_of/sub_string — Rhai has no
+// native JSON parser. Expected shape:
+//   {"session_id": "<uuid>", "model_a": "<slug>", "model_b": "<slug>", ...}
+fn extract_json_field(s, field_name) {
+    let needle = "\"" + field_name + "\"";
+    let p = s.index_of(needle);
+    if p < 0 { return ""; }
+    let after_key = s.sub_string(p + needle.len());
+    let colon = after_key.index_of(":");
+    if colon < 0 { return ""; }
+    let after_colon = after_key.sub_string(colon + 1);
+    // Strip leading whitespace
+    let i = 0;
+    while i < after_colon.len() {
+        let ch = after_colon.sub_string(i, i + 1);
+        if ch == " " || ch == "\t" || ch == "\n" || ch == "\r" { i += 1; } else { break; }
+    }
+    if i >= after_colon.len() { return ""; }
+    // Expect a quoted string value
+    let first = after_colon.sub_string(i, i + 1);
+    if first != "\"" { return ""; }
+    let val_start = i + 1;
+    let val_end = after_colon.index_of("\"", val_start);
+    if val_end < 0 { return ""; }
+    return after_colon.sub_string(val_start, val_end);
+}
+
 let session_id = ();
+let model_a = ();
+let model_b = ();
+let model_c = ();
 if args != () {
     let t = type_of(args);
     if t == "map" {
         if args.session_id != () { session_id = args.session_id; }
+        if args.model_a != () { model_a = args.model_a; }
+        if args.model_b != () { model_b = args.model_b; }
+        if args.model_c != () { model_c = args.model_c; }
     } else if t == "string" {
-        log("args arrived as string — cannot parse session_id from JSON in Rhai");
+        // JSON-string args (legacy serialization path)
+        session_id = extract_json_field(args, "session_id");
+        model_a = extract_json_field(args, "model_a");
+        model_b = extract_json_field(args, "model_b");
+        model_c = extract_json_field(args, "model_c");
+        if session_id == "" {
+            // Bare-string fallback (matches close-check.rhai contract):
+            // a session ID may be passed unwrapped.
+            session_id = args;
+            log("WARNING: args arrived as bare string — using entire string as session_id (legacy contract)");
+        }
     }
 }
 if session_id == () || session_id == "" {
     pause("verification", "Pass args.session_id — the UUID from your session context.");
 }
 
+// ── Model routing ──────────────────────────────────────────────────────
+// Dispatchers must NOT hardcode model slugs (per ~/.grok/AGENTS.md model-routing
+// policy). The command wrapper passes resolved models via args (from
+// pick_model.py --count). Fallback to FREE-tier provider-diverse defaults if
+// not provided. NEVER hardcode known-broken slugs (e.g., nim-*).
+//   Defaults: FREE_A=minimax (MiniMax), FREE_B=or-ling (OpenRouter),
+//   FREE_C=minimax (reuse) — max 2 concurrent per provider.
+//   See tool-fallbacks.md § spawn_subagent exclusions.
+let has_args_map = args != () && type_of(args) == "map";
+if !has_args_map {
+    log("WARNING: args not received as object map (type_of(args)=" + type_of(args).to_string() + ") — using default model fallback");
+}
+let FREE_A = if model_a != () && model_a != "" { model_a } else { "minimax-m3" };
+let FREE_B = if model_b != () && model_b != "" { model_b } else { "or-ling-3-flash-free" };
+let FREE_C = if model_c != () && model_c != "" { model_c } else { "minimax-m3" };
+
 // ============================
 // PHASE 0: Detect what to ship
 // ============================
@@ -80,7 +140,7 @@ detect_prompt += "Use run_terminal_command for all git operations. Report findin
 let detect_result = agent(detect_prompt, #{
     label: "detect",
     capability_mode: "read-only",
-    model: "or-ling-3-flash-free",
+    model: FREE_A,
 });
 
 let detect_summary = "";
@@ -122,12 +182,60 @@ specialist_prompt += "An empty bugs array is valid ONLY after you have actually
 specialist_prompt += "Do not answer from memory — use read_file and grep to inspect the actual code.";
 
 let review_jobs = [
-    #{ prompt: review_prompt, label: "parent-review", capability_mode: "read-only", output_schema: findings_schema, model: "or-ling-3-flash-free" },
-    #{ prompt: specialist_prompt, label: "specialist-review", capability_mode: "read-only", output_schema: findings_schema, model: "zen-deepseek-v4-flash-free" },
+    #{ prompt: review_prompt, label: "parent-review", capability_mode: "read-only", output_schema: findings_schema, model: FREE_A },
+    #{ prompt: specialist_prompt, label: "specialist-review", capability_mode: "read-only", output_schema: findings_schema, model: FREE_B },
 ];
 
 let review_results = parallel(review_jobs);
 
+// ── Retry-with-fallback-model (load-bearing agents only) ───────────
+// When a review agent fails (quota exhaustion, serde error, timeout),
+// retry once with a DIFFERENT model. Cap: 1 retry per agent.
+// If ALL agents fail even after retry, the both-failed gate below blocks.
+// Design: ship-rhai-retry-fallback-20260805 handoff.
+let retry_jobs = [];
+let retry_indices = [];
+let ri = 0;
+for r in review_results {
+    if r == () || !r.success {
+        let orig = review_jobs[ri];
+        // Retry model MUST differ from the failed agent's model.
+        // Swap to the other review lane's model; if that also collides,
+        // fall back to a known-diverse provider.
+        let retry_model = if orig.model == FREE_A { FREE_B } else { FREE_A };
+        if retry_model == orig.model {
+            retry_model = "cohere-north-mini-code";
+        }
+        retry_jobs.push(#{
+            prompt: orig.prompt,
+            label: orig.label + "-retry",
+            capability_mode: orig.capability_mode,
+            output_schema: orig.output_schema,
+            model: retry_model,
+        });
+        retry_indices.push(ri);
+    }
+    ri += 1;
+}
+if retry_jobs.len() > 0 {
+    log(retry_jobs.len().to_string() + " review agent(s) failed — retrying with fallback model");
+    let retry_results = parallel(retry_jobs);
+    let rj = 0;
+    for idx in retry_indices {
+        if retry_results[rj] != () && retry_results[rj].success {
+            review_results[idx] = retry_results[rj];
+            log("Retry succeeded for review agent " + idx.to_string());
+        } else {
+            log("Retry also failed for review agent " + idx.to_string());
+            write_scratch_file("review-retry-failure-agent-" + idx.to_string() + ".txt",
+                "Review agent " + idx.to_string() + " failed on both original and retry.\n" +
+                "Original model: " + review_jobs[idx].model + "\n" +
+                "This may indicate a systemic issue (quota, network) rather than a model-specific failure.\n");
+        }
+        rj += 1;
+    }
+}
+
 // Collect findings
 let all_bugs = [];
 let all_risks = [];
@@ -190,7 +298,7 @@ if all_bugs.len() > 0 {
         let fix_result = agent(fix_prompt, #{
             label: "fix-loop-" + iteration.to_string(),
             capability_mode: "read-write",
-            model: "cohere-north-mini-code",
+            model: FREE_C,
         });
 
         if fix_result != () && fix_result.success {
@@ -208,7 +316,7 @@ if all_bugs.len() > 0 {
         let recheck_result = agent(recheck_prompt, #{
             label: "recheck-" + iteration.to_string(),
             capability_mode: "read-only",
-            model: "or-ling-3-flash-free",
+            model: FREE_A,
             output_schema: #{
                 "type": "object",
                 "required": ["remaining_bugs"],
@@ -262,9 +370,34 @@ let verify_result = agent(verify_prompt, #{
     label: "verify",
     capability_mode: "execute",
     output_schema: verify_schema,
-    model: "cohere-north-mini-code",
+    model: FREE_C,
 });
 
+// ── Verify agent retry-with-fallback ───────────────────────────────
+// If the verify agent itself failed (not SHIP BLOCKED — that's a valid
+// result), retry once with a different model. The verify agent runs
+// ship_receipt.py; if the agent call fails (not the script), a different
+// model may succeed at reading the output correctly.
+if verify_result == () || !verify_result.success {
+    let verify_retry_model = FREE_A;
+    if verify_retry_model == FREE_C { verify_retry_model = FREE_B; }
+    log("Verify agent failed — retrying with fallback model " + verify_retry_model);
+    verify_result = agent(verify_prompt, #{
+        label: "verify-retry",
+        capability_mode: "execute",
+        output_schema: verify_schema,
+        model: verify_retry_model,
+    });
+    if verify_result == () || !verify_result.success {
+        log("Verify retry also failed — writing failure details to scratch");
+        write_scratch_file("verify-retry-failure.txt",
+            "Verify agent failed on both original and retry.\n" +
+            "Original model: " + FREE_C + "\n" +
+            "Retry model: " + verify_retry_model + "\n" +
+            "The ship_receipt.py script may need to be run manually.\n");
+    }
+}
+
 let verdict = "SHIP BLOCKED";
 let receipt_text = "Verification failed";
 
@@ -318,7 +451,7 @@ if is_done {
     let merge_result = agent(merge_prompt, #{
         label: "merge",
         capability_mode: "read-write",
-        model: "cohere-north-mini-code",
+        model: FREE_C,
     });
 
     if merge_result != () && merge_result.success {

```

---

## Transcript slices (filtered by relevance)

**Source:** chat_history.jsonl
**Provenance:** FALLBACK: most-recently-modified (GROK_SESSION_ID not set or not found)
**Filter:** 6 terms, 40/168 turns kept
**Terms:** retry, fallback, ship-rhai, ship-py, review-failure-gate, merge-base

---
**[user]:**

---
**[user] *:**

---
**[reasoning]:**

---
**[assistant [read_file, read_file, list_dir]] *:**

---
**[tool_result]:**

---
**[tool_result] *:**

---
**[tool_result] *:**

---
**[reasoning]:**

---
**[assistant [grep, read_file, read_file]] *:**

---
**[tool_result] *:**

---
**[tool_result] *:**

---
**[tool_result]:**

---
**[reasoning]:**

---
**[assistant [run_terminal_command, run_terminal_command]] *:**

---
**[tool_result] *:**

---
**[tool_result] *:**

---
**[reasoning]:**

---
**[assistant [read_file, run_terminal_command]] *:**

---
**[tool_result] *:**

---
**[tool_result] *:**

---
**[reasoning]:**

---
**[assistant [todo_write]] *:**

---
**[tool_result] *:**

---
**[reasoning]:**

---
**[assistant [search_replace, search_replace]] *:**

---
**[tool_result] *:**

---
**[tool_result] *:**

---
**[reasoning]:**

---
**[assistant [search_replace]] *:**

---
**[tool_result] *:**

---
**[reasoning]:**

---
**[assistant [read_file, read_file, read_file]] *:**

---
**[tool_result]:**

---
**[tool_result]:**

---
**[tool_result]:**

---
**[assistant [todo_write]]:**

---
**[tool_result] *:**

---
**[reasoning]:**

---
**[assistant [todo_write]]:**

---
**[tool_result] *:**


---
