#!/usr/bin/env python3
"""
Fix AID report saving to use proper project directory path
"""
import re


def fix_aid_report_path():
    aid_file = "C:/_Python/_Projects/__csf.wip/commands/ANL/aid/aid.py"

    with open(aid_file, encoding="utf-8") as f:
        content = f.read()

    # Replace the report path logic
    old_pattern = r"""            # Save Claude's analysis to a report file
            from datetime import datetime
            timestamp = datetime\.now\(\)\.strftime\("%Y%m%d_%H%M%S"\)
            report_filename = f"\{target\}_\{analysis_type\}_claude_report_\{timestamp\}\.md"
            report_path = Path\.cwd\(\) / report_filename"""

    new_replacement = """            # Save Claude's analysis to a report file in target directory
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{analysis_type}_claude_report_{timestamp}.md"

            # Save in target directory's reports folder
            target_path = Path(target)
            if target_path.is_file():
                reports_dir = target_path.parent / "reports"
            else:
                reports_dir = target_path / "reports"
            reports_dir.mkdir(exist_ok=True)
            report_path = reports_dir / report_filename"""

    new_content = re.sub(old_pattern, new_replacement, content, flags=re.MULTILINE)

    if new_content != content:
        with open(aid_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ AID report path fixed to use target directory")
        return True
    else:
        print("❌ Pattern not found - manual fix needed")
        return False


if __name__ == "__main__":
    fix_aid_report_path()
