# doc-compiler_sig.md
## PACK INFO
Target: P:\packages\cc-skills-meta\skills\doc-compiler
Files: 35

## SIGNATURE TOC

### _snapshots\accordion.py
  (no top-level def/class)

### _snapshots\browser_checks.py
  (no top-level def/class)

### _snapshots\browser_checks2.py
  (no top-level def/class)

### _snapshots\desktop_initial.py
  (no top-level def/class)

### _snapshots\run_simple.py
  (no top-level def/class)

### _snapshots\run_test.py
  (no top-level def/class)

### _snapshots\search.py
  (no top-level def/class)

### _snapshots\theme_toggle.py
  (no top-level def/class)

### _snapshots\toc_toggle.py
  (no top-level def/class)

### runtime\__init__.py
  (no top-level def/class)

### runtime\orchestrator.py
  def get_target() -> Path
  def run_stage(stage_name,stage_module,target) -> bool
  def main() -> None

### runtime\stage_a_source_extractor.py
  def extract_frontmatter(text) -> dict[str, Any]
  def normalize_steps(raw_steps) -> list[dict[str, Any]]
  def extract_steps_from_skill(text,fm) -> list[dict[str, Any]]
  def extract_decision_points(text) -> list[dict[str, Any]]
  def extract_route_outs(text) -> list[dict[str, Any]]
  def extract_terminal_states(text) -> list[dict[str, Any]]
  def extract_artifacts(text,fm) -> list[dict[str, Any]]
  def extract_from_skill(path) -> dict[str, Any]
  def extract_from_plugin(path) -> dict[str, Any]
  def extract_from_readme(path) -> dict[str, Any]
  def extract_from_yaml(path) -> dict[str, Any]
  def main() -> None

### runtime\stage_d_guide_loader.py
  def load_json(p) -> dict
  def extract_guide_sections(content) -> list[dict[str, str]]
  def parse_diagram_hints(content,diagram_type) -> dict[str, Any]
  def load_guides(plan) -> list[dict]
  def main() -> None

### runtime\stage_e_diagram_generator.py
  def load_json(p) -> dict
  def sanitize_id(text) -> str
  def sanitize_label(text) -> str
  def generate_flowchart(plan,guide) -> str
  def generate_sequence(plan,guide) -> str
  def generate_state(plan,guide) -> str
  def generate_class(plan,guide) -> str
  def generate_error_path(plan,guide) -> str
  def generate_diagram(diagram_type,plan,guide) -> str
  def main() -> None

### runtime\stage_f_diagram_critic_gate.py
  def load_json(p) -> dict
  def critique_flowchart(mmd,diagram_id) -> list[str]
  def critique_sequence(mmd,diagram_id) -> list[str]
  def critique_state(mmd,diagram_id) -> list[str]
  def critique_class(mmd,diagram_id) -> list[str]
  def critique_error_path(mmd,diagram_id) -> list[str]
  def gate_diagram(diagram) -> dict
  def main() -> None

### runtime\stage_h_template_html_emitter.py
  def load_json(p) -> dict
  def read_template(name) -> str
  def fill(template,bindings) -> str
  def fill_steps_section(steps) -> str
  def fill_diagram_panel() -> str
  def assemble_css() -> str
  def assemble_js() -> str
  def build_html(plan) -> str
  def main() -> None

### runtime\stage_i_static_validator.py
  def check(name,pred,details) -> str
  def main() -> None
  def s(name,pred,details) -> None

### runtime\stage_j_runtime_validator.py
  def load_json(p) -> dict
  def run_browser_checks() -> dict
  def main() -> None

### runtime\stage_k_external_critic.py
  def load_json(p) -> dict
  def summarize_source(model) -> str
  def main() -> None

### runtime\stage_l_emit_proof_bundle.py
  def load_json(p) -> dict
  def check_artifact(name,path) -> dict
  def main() -> None

### stage_a_source_extractor.py
  def extract_frontmatter(text) -> dict[str, Any]
  def normalize_steps(raw_steps) -> list[dict[str, Any]]
  def extract_steps_from_skill(text,fm) -> list[dict[str, Any]]
  def extract_from_skill(path) -> dict[str, Any]
  def extract_from_plugin(path) -> dict[str, Any]
  def extract_from_readme(path) -> dict[str, Any]
  def extract_from_yaml(path) -> dict[str, Any]
  def main() -> None

### stage_c_mermaid_design.py
  (no top-level def/class)

### stage_d_mermaid_critic_review.py
  (no top-level def/class)

### stage_e1_loader.py
  def read_template(name) -> str | None
  def main() -> None

### stage_e2_binder.py
  def load_json(p) -> dict
  def slot_fill(template,bindings) -> str
  def fill_hero(template,plan) -> str
  def fill_facts(template,plan) -> str
  def fill_mermaid_panel(template,plan) -> str
  def fill_steps(template,plan) -> str
  def fill_route_outs(template,plan) -> str
  def fill_terminals(template,plan) -> str
  def fill_proof_summary(template,plan) -> str
  def fill_artifacts(template,plan) -> str
  def fill_proof_summary(template,plan) -> str
  def main() -> None

### stage_e3_assembler.py
  def load_json(p) -> dict
  def read(name) -> str
  def main() -> None

### stage_e4_writer.py
  def read(name) -> str
  def fill_base_shell(base,plan) -> str
  def main() -> None

### stage_f_static_validator.py
  def main() -> None

### stage_f_validator.py
  def read_file(fname) -> 
  def fail(msg) -> 
  def pass_(msg) -> 
  def check(name,pred,details) -> 
  def s(name,pred,details) -> 

### stage_g_artifact_proof.py
  def load_json(p) -> dict
  def run_browser_checks() -> dict
  def main() -> None

### stage_g_validator.py
  (no top-level def/class)

### stage_h_external_critic.py
  def load_json(p) -> dict
  def main() -> None

### stage_h_validator.py
  (no top-level def/class)

### stage_i_emit_proof_metadata.py
  def load_json(p) -> dict
  def main() -> None

### templates\extract_templates.py
  def split_css(css_text) -> 
  def css_join() -> 
  def split_body(body_text) -> 
  def split_js(js_text) -> 


## DIRECTORY INDEX

| Path | Type |
|------|------|
| _snapshots\accordion.py | .py (727b) |
| _snapshots\browser_checks.py | .py (4522b) |
| _snapshots\browser_checks2.py | .py (1047b) |
| _snapshots\desktop_initial.py | .py (754b) |
| _snapshots\run_simple.py | .py (2397b) |
| _snapshots\run_test.py | .py (2398b) |
| _snapshots\search.py | .py (706b) |
| _snapshots\theme_toggle.py | .py (656b) |
| _snapshots\toc_toggle.py | .py (1120b) |
| runtime\__init__.py | .py (35b) |
| runtime\orchestrator.py | .py (4238b) |
| runtime\stage_a_source_extractor.py | .py (14908b) |
| runtime\stage_d_guide_loader.py | .py (4105b) |
| runtime\stage_e_diagram_generator.py | .py (10277b) |
| runtime\stage_f_diagram_critic_gate.py | .py (5880b) |
| runtime\stage_h_template_html_emitter.py | .py (12709b) |
| runtime\stage_i_static_validator.py | .py (5356b) |
| runtime\stage_j_runtime_validator.py | .py (10669b) |
| runtime\stage_k_external_critic.py | .py (7597b) |
| runtime\stage_l_emit_proof_bundle.py | .py (5548b) |
| stage_a_source_extractor.py | .py (10694b) |
| stage_c_mermaid_design.py | .py (3312b) |
| stage_d_mermaid_critic_review.py | .py (4628b) |
| stage_e1_loader.py | .py (2986b) |
| stage_e2_binder.py | .py (7699b) |
| stage_e3_assembler.py | .py (2988b) |
| stage_e4_writer.py | .py (5505b) |
| stage_f_static_validator.py | .py (3023b) |
| stage_f_validator.py | .py (4847b) |
| stage_g_artifact_proof.py | .py (8957b) |
| stage_g_validator.py | .py (4330b) |
| stage_h_external_critic.py | .py (4725b) |
| stage_h_validator.py | .py (3692b) |
| stage_i_emit_proof_metadata.py | .py (5213b) |
| templates\extract_templates.py | .py (15279b) |
| SKILL.md | .md (72659b) |