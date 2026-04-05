#!/usr/bin/env python3
"""Fix on_postcompact.py fresh start mode."""

from pathlib import Path

# Read original
src = Path("P:/.claude/hooks/on_postcompact.py")
lines = src.read_text().splitlines()

# Find run() method and rebuild
output = []
skip_until_next_def = False
run_fixed = False

for line in lines:
    if "def run(self) -> str:" in line and not run_fixed:
        # Start new run() method
        output.append("    def run(self) -> str:")
        output.append('        """Execute restoration and return prompt text."""')
        output.append("        # Fresh Start Mode: Check for marker file")
        output.append('        fresh_start_file = Path.cwd() / ".claude" / "fresh_start.txt"')
        output.append("")
        output.append("        if fresh_start_file.exists():")
        output.append('            print("[PostCompact] Fresh Start Mode - skipping CKS restoration")')
        output.append("            fresh_start_file.unlink()")
        output.append(r'            return "# Fresh Start Mode - No history restored.\n\nReady for new task."')
        output.append("")
        output.append('        print("[PostCompact] Starting context restoration...")')
        output.append("")
        output.append("        # Step 1: Recover task identity")
        output.append("        task_name = self.task_manager.get_current_task()")
        output.append("")
        output.append("        if not task_name:")
        output.append('            error_msg = (')
        output.append(r'                "# Context Restoration Failed\n\n"')
        output.append(r'                "I couldn\'t determine which task I\'m working on after compaction.\n\n"')
        output.append(r'                "Please tell me which task to resume:\n"')
        output.append(r'                "  python .speckit/commands/task_cli resume <TASK_NAME>\n\n"')
        output.append(r'                "Or ask: \'what were we working on?\'"')
        output.append("            )")
        output.append('            print("[PostCompact] ERROR: Could not determine task")')
        output.append("            return error_msg")
        output.append("")
        output.append('        print(f"[PostCompact] Task: {task_name}")')
        output.append("")
        output.append("        # Step 2: Ensure session file is current")
        output.append("        self.task_manager.set_current_task(task_name)")
        output.append("")
        output.append("        # Step 3: Generate restoration")
        output.append("        restoration = self.generate_restoration_prompt(task_name)")
        output.append("")
        output.append('        print("[PostCompact] ✓ Restoration complete")')
        output.append("        return restoration")
        run_fixed = True
        skip_until_next_def = True
    elif skip_until_next_def and line.strip().startswith("def ") and line.strip() != "def run(self) -> str:":
        skip_until_next_def = False
        output.append(line)
    elif not skip_until_next_def:
        output.append(line)

src.write_text("\n".join(output))
print("Fixed on_postcompact.py")
