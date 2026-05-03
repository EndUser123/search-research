{
  "findings": [
    {
      "id": "SEC-001",
      "severity": "LOW",
      "title": "Hardcoded absolute path in stage_e2_binder.py",
      "description": "stage_e2_binder.py fill_artifacts() constructs artifact paths using a hardcoded Windows path prefix P:/.claude/skills/{name}/index.html. This creates platform lock-in.",
      "evidence": {
        "code_excerpt": "index_path: f\"P:/.claude/skills/{name}/index.html\"",
        "file_path": "P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler/stage_e2_binder.py",
        "line_number": 139,
        "function_name": "fill_artifacts",
        "proof": "The index_path construction embeds a literal Windows drive letter P:."
      },
      "impact": {
        "business_consequence": "Documentation output paths incorrect on non-Windows",
        "customer_visible": false,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "Use Path.resolve() for platform-independent paths",
        "code_fix": "Use relative paths or base dir resolved at runtime"
      },
      "confidence": "high"
    },
    {
      "id": "SEC-002",
      "severity": "LOW",
      "title": "subprocess.run with user-controlled prompt data",
      "description": "stage_d_mermaid_critic_review.py invokes claude --print with AGENT_PROMPT containing f-string interpolated file paths from pipeline artifacts.",
      "evidence": {
        "code_excerpt": "AGENT_PROMPT = f\"\"\"...Diagram file: {DIAGRAM}...\"\"\"",
        "file_path": "P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler/stage_d_mermaid_critic_review.py",
        "line_number": 20,
        "function_name": "main",
        "proof": "File paths from pipeline artifacts interpolated into prompt."
      },
      "impact": {
        "business_consequence": "Prompt injection if pipeline artifacts compromised",
        "customer_visible": false,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "Validate paths contain only expected characters",
        "code_fix": "Add path validation before interpolation"
      },
      "confidence": "medium"
    },
    {
      "id": "SEC-003",
      "severity": "LOW",
      "title": "Mermaid palette injection via configparser",
      "description": "stage_b_artifact_plan_builder.py uses configparser to load presets. _pv() strips quotes but does not sanitize for injection.",
      "evidence": {
        "code_excerpt": "val = preset.get(key, default).strip().strip(chr(39)).strip(chr(34))",
        "file_path": "P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler/stage_b_artifact_plan_builder.py",
        "line_number": 93,
        "function_name": "_pv",
        "proof": "Values from presets.ini embedded into CSS without sanitization."
      },
      "impact": {
        "business_consequence": "Malformed CSS output",
        "customer_visible": false,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "Validate preset values for CSS-safe characters",
        "code_fix": "Add regex validation"
      },
      "confidence": "low"
    },
    {
      "id": "SEC-004",
      "severity": "MEDIUM",
      "title": "HTML injection in fill_route_outs",
      "description": "stage_e2_binder.py fill_route_outs() inserts unsanitized text into HTML. fill_steps() escapes &, <, > but fill_route_outs() does NOT escape target and description.",
      "evidence": {
        "code_excerpt": "items_html += f\"<h4>{target}</h4>\"",
        "file_path": "P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler/stage_e2_binder.py",
        "line_number": 105,
        "function_name": "fill_route_outs",
        "proof": "target and description inserted directly without HTML encoding."
      },
      "impact": {
        "business_consequence": "XSS if source model contains malicious HTML",
        "customer_visible": true,
        "regulatory_impact": "Potential stored XSS"
      },
      "recommendation": {
        "action": "Use html.escape() for all text inserted into HTML",
        "code_fix": "Import html and use html.escape()"
      },
      "confidence": "high"
    },
    {
      "id": "SEC-005",
      "severity": "MEDIUM",
      "title": "Template scripts lack path traversal validation",
      "description": "extract_templates.py and rebuild_index.py use hardcoded string paths without path traversal validation.",
      "evidence": {
        "code_excerpt": "BASE = \"P:/packages/cc-skills-meta/skills/doc-compiler\"",
        "file_path": "P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler/templates/extract_templates.py",
        "line_number": 5,
        "function_name": "read",
        "proof": "String concatenation for paths, no traversal validation."
      },
      "impact": {
        "business_consequence": "Could overwrite arbitrary files",
        "customer_visible": false,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "Use pathlib and validate paths stay within base",
        "code_fix": "Use Path.resolve().relative_to(base_dir.resolve())"
      },
      "confidence": "medium"
    }
  ]
}