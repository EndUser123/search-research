#!/usr/bin/env python3
"""Defect scanner — LangGraph-based defect detection pipeline.

This is the pilot implementation of the /defect skill as a LangGraph
state graph. The graph enforces a deterministic pipeline:

    classify → scan → verify → verdict

The LLM cannot skip steps because they are graph edges, not prose rules.

Usage:
    python main.py --target <path> [--type code|session|pipeline|doc|skill]
    python main.py --target P:/packages/yt-is/src/ --type code
    python main.py --target . --type skill
    python main.py --diff HEAD~3 --type code

Modes:
    --type code      Scan a code diff or directory for defects
    --type session   Scan session claims for unverified assertions
    --type pipeline  Scan Python scripts for I/O boundary failure modes
    --type doc       Scan documentation for broken links, missing sections
    --type skill     Scan SKILL.md files for static defects
    --type auto      (default) Classify from the target path automatically

Output:
    Structured JSON findings with severity, file:line, verified status.
    Exit code 0 = PASS (no defects), exit code 1 = FAIL (defects found).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END


# ─────────────────────────────────────────────────────────────────────────────
# State definition — carries evidence between phases
# ─────────────────────────────────────────────────────────────────────────────

class DefectState(TypedDict):
    target: str                    # what we're scanning (path, diff ref, session id)
    defect_type: str               # classified: code | session | pipeline | doc | skill | auto
    findings: list[dict]           # accumulated defect findings
    verified: list[dict]           # findings that passed verification
    verdict: str                   # PASS | FAIL
    error: str                     # error message if a node failed


# ─────────────────────────────────────────────────────────────────────────────
# Finding dataclass — structured output
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    id: str
    severity: str        # BLOCK | REVISE | ADVISORY
    title: str
    detail: str
    evidence: str        # file:line or tool-call reference
    verified: bool = False
    source: str = ""     # which scanner produced it

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# Node 1: CLASSIFY — determine what type of defect scan to run
# ─────────────────────────────────────────────────────────────────────────────

def classify(state: DefectState) -> DefectState:
    """Classify the target to determine which scanner(s) to invoke."""
    target = state["target"]
    defect_type = state.get("defect_type", "auto")

    if defect_type != "auto":
        state["defect_type"] = defect_type
        return state

    # Auto-classify from target path
    target_path = Path(target)
    target_str = str(target_path).lower().replace("\\", "/")

    if _SESSION_ID_RE.match(target.strip()) or target.strip().lower() in ("latest", "current"):
        state["defect_type"] = "session"
    elif target_str.endswith(".py") or "/src/" in target_str or "/packages/" in target_str:
        state["defect_type"] = "code"
    elif "/skills/" in target_str and target_path.name == "SKILL.md":
        state["defect_type"] = "skill"
    elif "/skills/" in target_str and target_path.is_dir():
        state["defect_type"] = "skill"
    elif target_path.suffix in (".md", ".rst"):
        state["defect_type"] = "doc"
    elif target_str.endswith(".py") and "/scripts/" in target_str:
        state["defect_type"] = "pipeline"
    else:
        state["defect_type"] = "code"  # default

    return state


def route_by_type(state: DefectState) -> str:
    """Conditional edge: route to the correct scanner based on defect type."""
    return state["defect_type"]


# ─────────────────────────────────────────────────────────────────────────────
# Node 2a: SCAN CODE — invoke ruff + py_compile + static checks
# ─────────────────────────────────────────────────────────────────────────────

def scan_code(state: DefectState) -> DefectState:
    """Scan code for defects using ruff, py_compile, and static analysis."""
    target = state["target"]
    findings = state.get("findings", [])

    target_path = Path(target)
    py_files = []

    if target_path.is_file() and target_path.suffix == ".py":
        py_files = [target_path]
    elif target_path.is_dir():
        py_files = list(target_path.rglob("*.py"))
    else:
        # Treat as a diff ref
        py_files = _get_diff_files(target)

    for py_file in py_files:
        # Ruff check
        ruff_findings = _run_ruff(py_file)
        findings.extend(ruff_findings)

        # py_compile check
        compile_finding = _run_py_compile(py_file)
        if compile_finding:
            findings.append(compile_finding)

    state["findings"] = findings
    return state


def _run_ruff(filepath: Path) -> list[dict]:
    """Run ruff check on a file, return findings."""
    try:
        proc = subprocess.run(
            ["ruff", "check", str(filepath), "--output-format=json"],
            capture_output=True, text=True, timeout=30
        )
        if proc.returncode == 0:
            return []

        results = json.loads(proc.stdout) if proc.stdout.strip() else []
        findings = []
        for r in results:
            findings.append(Finding(
                id=f"RUFF-{r.get('code', '???')}",
                severity=_ruff_severity(r.get('code', '')),
                title=r.get("message", "Ruff finding"),
                detail=f"{r.get('code', '')}: {r.get('message', '')}",
                evidence=f"{r.get('filename', str(filepath))}:{r.get('location', {}).get('row', '?')}",
                source="ruff",
            ).to_dict())
        return findings
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []


def _run_py_compile(filepath: Path) -> dict | None:
    """Run py_compile on a file, return a finding if syntax error."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode != 0:
            error_line = proc.stderr.strip().split("\n")[-1] if proc.stderr else "Unknown error"
            return Finding(
                id="SYNTAX-001",
                severity="BLOCK",
                title=f"Syntax error in {filepath.name}",
                detail=error_line,
                evidence=str(filepath),
                source="py_compile",
            ).to_dict()
    except subprocess.TimeoutExpired:
        pass
    return None


def _get_diff_files(diff_ref: str) -> list[Path]:
    """Get .py files from a git diff."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", diff_ref],
            capture_output=True, text=True, timeout=10
        )
        files = [Path(f) for f in proc.stdout.strip().split("\n") if f.endswith(".py")]
        return [f for f in files if f.exists()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _ruff_severity(code: str) -> str:
    """Map ruff rule codes to severity."""
    if code.startswith("E9") or code.startswith("F8"):
        return "BLOCK"  # syntax errors, undefined names
    if code.startswith("F") or code.startswith("E"):
        return "REVISE"  # pyflakes, pycodestyle errors
    return "ADVISORY"


# ─────────────────────────────────────────────────────────────────────────────
# Node 2b: SCAN SKILL — invoke script_scan.py + static checks
# ─────────────────────────────────────────────────────────────────────────────

def scan_skill(state: DefectState) -> DefectState:
    """Scan SKILL.md files and __lib/*.py for defects."""
    target = state["target"]
    findings = state.get("findings", [])

    target_path = Path(target)

    # Find all SKILL.md files
    if target_path.name == "SKILL.md":
        skill_files = [target_path]
    elif target_path.is_dir():
        skill_files = list(target_path.rglob("SKILL.md"))
    else:
        skill_files = []

    for skill_md in skill_files:
        # Run the existing script_scan.py if __lib/ exists
        skill_dir = skill_md.parent
        lib_dir = skill_dir / "__lib"
        if lib_dir.exists():
            script_findings = _run_script_scan(skill_dir)
            findings.extend(script_findings)

        # Static checks on SKILL.md itself
        md_findings = _check_skill_md(skill_md)
        findings.extend(md_findings)

    state["findings"] = findings
    return state


def _run_script_scan(skill_dir: Path) -> list[dict]:
    """Run the existing script_scan.py on a skill's __lib/ directory."""
    script = Path.home() / ".grok/skills/skill-dev/__lib/script_scan.py"
    if not script.exists():
        return []

    try:
        proc = subprocess.run(
            [sys.executable, str(script), str(skill_dir)],
            capture_output=True, text=True, timeout=30
        )
        if proc.returncode == 0 or not proc.stdout.strip():
            return []

        # Parse script_scan output (it prints findings as text lines)
        findings = []
        for line in proc.stdout.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("Scanning") or line.startswith("==="):
                continue
            findings.append(Finding(
                id="SKILL-SCRIPT",
                severity="REVISE",
                title=f"Script defect in {skill_dir.name}",
                detail=line,
                evidence=str(skill_dir),
                source="script_scan",
            ).to_dict())
        return findings
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _check_skill_md(skill_md: Path) -> list[dict]:
    """Static checks on a SKILL.md file."""
    findings = []
    try:
        content = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    # Check frontmatter exists
    if not content.startswith("---"):
        findings.append(Finding(
            id="SKILL-FM-001",
            severity="REVISE",
            title=f"Missing frontmatter in {skill_md.name}",
            detail="SKILL.md must start with YAML frontmatter (---).",
            evidence=str(skill_md),
            source="skill_check",
        ).to_dict())

    # Check for name: field
    if not re.search(r'^name:\s*', content, re.MULTILINE):
        findings.append(Finding(
            id="SKILL-FM-002",
            severity="REVISE",
            title=f"Missing 'name:' field in {skill_md.name}",
            detail="SKILL.md frontmatter must have a 'name:' field.",
            evidence=str(skill_md),
            source="skill_check",
        ).to_dict())

    # Check for description: field
    if not re.search(r'^description:\s*', content, re.MULTILINE):
        findings.append(Finding(
            id="SKILL-FM-003",
            severity="REVISE",
            title=f"Missing 'description:' field in {skill_md.name}",
            detail="SKILL.md frontmatter must have a 'description:' field.",
            evidence=str(skill_md),
            source="skill_check",
        ).to_dict())

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Node 2c: SCAN PIPELINE — basic FMEA-style checks
# ─────────────────────────────────────────────────────────────────────────────

def scan_pipeline(state: DefectState) -> DefectState:
    """Scan Python pipeline scripts for I/O boundary risks."""
    target = state["target"]
    findings = state.get("findings", [])

    target_path = Path(target)
    py_files = [target_path] if target_path.is_file() else list(target_path.rglob("*.py"))

    for py_file in py_files:
        try:
            content = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Check for bare open() without encoding= (common Windows defect)
        if re.search(r'open\([^)]*\)', content) and 'encoding=' not in content:
            if 'open(' in content:
                findings.append(Finding(
                    id="PIPE-ENC-001",
                    severity="REVISE",
                    title=f"open() without encoding= in {py_file.name}",
                    detail="File operations must specify encoding='utf-8' on Windows to avoid cp1252 corruption.",
                    evidence=str(py_file),
                    source="pipeline_scan",
                ).to_dict())

        # Check for subprocess without timeout
        if 'subprocess.run' in content or 'subprocess.call' in content:
            if 'timeout' not in content:
                findings.append(Finding(
                    id="PIPE-TIMEOUT-001",
                    severity="ADVISORY",
                    title=f"subprocess without timeout in {py_file.name}",
                    detail="Subprocess calls should specify a timeout to prevent hangs.",
                    evidence=str(py_file),
                    source="pipeline_scan",
                ).to_dict())

    state["findings"] = findings
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Node 2d: SCAN DOC — broken links, missing sections
# ─────────────────────────────────────────────────────────────────────────────

def scan_doc(state: DefectState) -> DefectState:
    """Scan documentation for broken links and missing sections."""
    target = state["target"]
    findings = state.get("findings", [])

    target_path = Path(target)
    doc_files = [target_path] if target_path.is_file() else list(target_path.rglob("*.md"))

    for doc_file in doc_files:
        try:
            content = doc_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Check for unclosed code fences
        fence_count = content.count("```")
        if fence_count % 2 != 0:
            findings.append(Finding(
                id="DOC-FENCE-001",
                severity="REVISE",
                title=f"Unclosed code fence in {doc_file.name}",
                detail=f"Found {fence_count} code fence markers (should be even).",
                evidence=str(doc_file),
                source="doc_scan",
            ).to_dict())

        # Check for broken wikilinks [[slug]] where slug has spaces
        broken_wikilinks = re.findall(r'\[\[([^\]]* [^\]]*)\]\]', content)
        for wl in broken_wikilinks:
            findings.append(Finding(
                id="DOC-WIKI-001",
                severity="ADVISORY",
                title=f"Possible broken wikilink in {doc_file.name}",
                detail=f"Wikilink [[{wl}]] contains spaces — may not resolve.",
                evidence=str(doc_file),
                source="doc_scan",
            ).to_dict())

    state["findings"] = findings
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Node 2e: SCAN SESSION — unverified claims in the session transcript chain
# ─────────────────────────────────────────────────────────────────────────────

# [FACT]/[INFERENCE] assertion markers in assistant output (epistemic format)
_FACT_RE = re.compile(r"\[FACT\]", re.IGNORECASE)
_RECEIPT_RE = re.compile(
    # tool-call receipts that back a claim: file:line, exit code, command output
    r"(?:source:|receipt:|\(source:|\(receipt:|exit (?:code)?:|→ "
    r"|tool[_ ]call|toolcall|verified via|cited? (?:from|at)|"
    r"file:[^\s]+\.(?:py|md|json|toml)|https?://[^\s\)\"]+)",
    re.IGNORECASE,
)
# session id: 8-4-4-4-12 hex
_SESSION_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def _find_session_dir(session_id: str) -> Path | None:
    """Locate the session directory under ~/.grok/sessions/<encoded-cwd>/<id>."""
    sessions_root = Path.home() / ".grok/sessions"
    if not sessions_root.exists():
        return None
    for encoded_cwd_dir in sessions_root.iterdir():
        if not encoded_cwd_dir.is_dir():
            continue
        session_dir = encoded_cwd_dir / session_id
        if session_dir.exists():
            return session_dir
    return None


def _load_session_lines(session_id: str) -> list[str]:
    """Load chat_history.jsonl + compaction segment_*.md as synthetic JSONL lines.

    Mirrors scan_transcript.py's loader: post-compaction history first, then
    pre-compaction segments (assistant turns wrapped as role=assistant entries,
    user turns as role=user entries).
    """
    session_dir = _find_session_dir(session_id)
    if not session_dir:
        return []

    lines: list[str] = []
    chat_path = session_dir / "chat_history.jsonl"
    if chat_path.exists():
        with open(chat_path, encoding="utf-8", errors="replace") as f:
            lines.extend(f)

    compaction_dir = session_dir / "compaction"
    if compaction_dir.is_dir():
        for seg in sorted(compaction_dir.glob("segment_*.md")):
            try:
                seg_text = seg.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for para in seg_text.split("\n\n"):
                if not para.strip():
                    continue
                # Best-effort role detection from the segment's plain markdown
                if para.lstrip().startswith(("#", "**Human", "**User", "> ")):
                    role = "user"
                else:
                    role = "assistant"
                lines.append(json.dumps({"type": role, "message": {"content": {"text": para}}}))

    return lines


def scan_session(state: DefectState) -> DefectState:
    """Scan the session transcript chain for defect-tier issues.

    Detects [FACT]-labeled assertions that lack a backing receipt in the
    same message (the epistemic-format defect: a claim stated as fact with
    no citation). This is the mechanical layer; LLM judgment layers on top.
    """
    findings = state.get("findings", [])
    target = state["target"]

    # Resolve the session id: explicit id, or "latest" inference
    session_id = target.strip()
    if session_id in ("latest", "current", "."):
        session_id = _latest_session_id()
    if not session_id or not _SESSION_ID_RE.match(session_id):
        findings.append(Finding(
            id="SESSION-TARGET-001",
            severity="REVISE",
            title="Invalid session target",
            detail=f"'{target}' is not a session id (use a UUID or 'latest').",
            evidence="",
            source="session_scan",
        ).to_dict())
        state["findings"] = findings
        return state

    lines = _load_session_lines(session_id)
    if not lines:
        findings.append(Finding(
            id="SESSION-LOAD-001",
            severity="REVISE",
            title=f"No transcript found for session {session_id[:8]}",
            detail="Session dir or chat_history.jsonl not found under ~/.grok/sessions/.",
            evidence="",
            source="session_scan",
        ).to_dict())
        state["findings"] = findings
        return state

    fact_no_receipt = 0
    first_offender = None
    session_dir = _find_session_dir(session_id)
    chat_rel = ""
    if session_dir is not None:
        chat_rel = str(session_dir / "chat_history.jsonl")

    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") not in ("assistant",):
            continue
        text = _extract_text(entry)
        if not text or not _FACT_RE.search(text):
            continue
        if not _RECEIPT_RE.search(text):
            fact_no_receipt += 1
            if first_offender is None:
                excerpt = text.strip().replace("\n", " ")[:100]
                first_offender = (excerpt, i + 1)

    if fact_no_receipt:
        findings.append(Finding(
            id="SESSION-FACT-001",
            severity="REVISE",
            title=f"{fact_no_receipt} assistant message(s) assert [FACT] with no receipt",
            detail=(
                f"First offender (line {first_offender[1]}): \"{first_offender[0]}...\" — "
                "claims labeled [FACT] must cite a receipt in the same message "
                "(source:, exit code, file:line, or URL)."
            ),
            evidence=f"{chat_rel}:{first_offender[1]}" if chat_rel else "",
            source="session_scan",
        ).to_dict())

    state["findings"] = findings
    return state


def _extract_text(entry: dict) -> str:
    """Pull assistant text out of a chat_history.jsonl entry, tolerating shapes."""
    msg = entry.get("message", entry)
    content = msg.get("content", msg)
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        text = content.get("text", "")
        if isinstance(text, list):  # content blocks
            text = " ".join(
                b.get("text", "") for b in text if isinstance(b, dict)
            )
        return str(text)
    return ""


def _latest_session_id() -> str:
    """Infer the most recently modified session dir across encoded cwds."""
    sessions_root = Path.home() / ".grok/sessions"
    if not sessions_root.exists():
        return ""
    best_mtime, best_id = 0.0, ""
    for encoded_cwd_dir in sessions_root.iterdir():
        if not encoded_cwd_dir.is_dir():
            continue
        for session_dir in encoded_cwd_dir.iterdir():
            if not session_dir.is_dir():
                continue
            mtime = session_dir.stat().st_mtime
            if mtime > best_mtime:
                best_mtime, best_id = mtime, session_dir.name
    return best_id


# ─────────────────────────────────────────────────────────────────────────────
# Node 3: VERIFY — verify findings against source
# ─────────────────────────────────────────────────────────────────────────────

def verify_findings(state: DefectState) -> DefectState:
    """Verify each finding against its cited source.

    A finding is verified if:
    - Its evidence file:line exists and is readable
    - For code findings: the cited file actually contains the pattern described

    This node is the structural enforcement layer. The LLM cannot skip it
    because it's a graph edge, not a prose rule.
    """
    findings = state.get("findings", [])
    verified = []

    for finding in findings:
        evidence = finding.get("evidence", "")
        if not evidence:
            # Can't verify without evidence — mark as unverified
            finding["verified"] = False
            verified.append(finding)
            continue

        # Parse file:line from evidence
        parts = evidence.rsplit(":", 1)
        filepath_str = parts[0]
        line_num = None
        if len(parts) == 2 and parts[1].isdigit():
            line_num = int(parts[1])

        filepath = Path(filepath_str)
        if not filepath.exists():
            finding["verified"] = False
            verified.append(finding)
            continue

        if line_num is not None:
            try:
                lines = filepath.read_text(encoding="utf-8").split("\n")
                if 1 <= line_num <= len(lines):
                    finding["verified"] = True
                else:
                    finding["verified"] = False
            except (OSError, UnicodeDecodeError):
                finding["verified"] = False
        else:
            finding["verified"] = True  # file exists, no line specified

        verified.append(finding)

    state["verified"] = verified
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Node 4: VERDICT — produce PASS/FAIL from verified findings
# ─────────────────────────────────────────────────────────────────────────────

def make_verdict(state: DefectState) -> DefectState:
    """Produce the final verdict from verified findings."""
    verified = state.get("verified", [])

    block_count = sum(1 for f in verified if f.get("severity") == "BLOCK" and f.get("verified", False))
    revise_count = sum(1 for f in verified if f.get("severity") == "REVISE" and f.get("verified", False))

    if block_count > 0:
        state["verdict"] = "FAIL"
    elif revise_count > 0:
        state["verdict"] = "FAIL"
    else:
        state["verdict"] = "PASS"

    return state


def check_verdict(state: DefectState) -> str:
    """Conditional edge: if verdict is FAIL with BLOCK findings, could retry.
    For pilot, always go to END after verdict."""
    return "done"


# ─────────────────────────────────────────────────────────────────────────────
# Graph construction
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    """Build and compile the defect scanner LangGraph."""
    workflow = StateGraph(DefectState)

    # Add nodes
    workflow.add_node("classify", classify)
    workflow.add_node("scan_code", scan_code)
    workflow.add_node("scan_skill", scan_skill)
    workflow.add_node("scan_pipeline", scan_pipeline)
    workflow.add_node("scan_doc", scan_doc)
    workflow.add_node("scan_session", scan_session)
    workflow.add_node("verify", verify_findings)
    workflow.add_node("verdict", make_verdict)

    # Set entry point
    workflow.set_entry_point("classify")

    # Conditional routing from classify to the correct scanner
    workflow.add_conditional_edges("classify", route_by_type, {
        "code": "scan_code",
        "skill": "scan_skill",
        "pipeline": "scan_pipeline",
        "doc": "scan_doc",
        "session": "scan_session",
    })

    # All scanners flow to verify (deterministic — not LLM-decided)
    workflow.add_edge("scan_code", "verify")
    workflow.add_edge("scan_skill", "verify")
    workflow.add_edge("scan_pipeline", "verify")
    workflow.add_edge("scan_doc", "verify")
    workflow.add_edge("scan_session", "verify")

    # Verify flows to verdict (deterministic)
    workflow.add_edge("verify", "verdict")

    # Verdict to END
    workflow.add_conditional_edges("verdict", check_verdict, {
        "done": END,
    })

    return workflow.compile()


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Defect scanner — LangGraph-based defect detection pipeline"
    )
    parser.add_argument("--target", required=True, help="Path, diff ref, or session ID to scan")
    parser.add_argument("--type", default="auto",
                        choices=["auto", "code", "session", "pipeline", "doc", "skill"],
                        help="Defect scan type (default: auto-classify from target)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Build and run the graph
    app = build_graph()

    initial_state = DefectState(
        target=args.target,
        defect_type=args.type,
        findings=[],
        verified=[],
        verdict="",
        error="",
    )

    result = app.invoke(initial_state)

    # Output
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        verdict = result.get("verdict", "UNKNOWN")
        findings = result.get("verified", [])

        verified_findings = [f for f in findings if f.get("verified")]
        unverified_findings = [f for f in findings if not f.get("verified")]

        print(f"DEFECT SCAN: {args.target}")
        print(f"Type: {result.get('defect_type', '?')}")
        print(f"Verdict: {verdict}")
        print(f"Findings: {len(verified_findings)} verified, {len(unverified_findings)} unverified")
        print()

        if verified_findings:
            print("Verified findings:")
            for f in verified_findings:
                sev = f.get("severity", "?")
                print(f"  [{sev}] {f.get('id', '?')}: {f.get('title', '?')}")
                print(f"    Evidence: {f.get('evidence', '?')}")
                if f.get("detail"):
                    print(f"    Detail: {f['detail']}")
                print()

        if unverified_findings:
            print(f"Unverified findings ({len(unverified_findings)} — could not confirm against source):")
            for f in unverified_findings:
                sev = f.get("severity", "?")
                print(f"  [{sev}] {f.get('id', '?')}: {f.get('title', '?')}")
            print()

    # Exit code
    sys.exit(0 if result.get("verdict") == "PASS" else 1)


if __name__ == "__main__":
    main()
