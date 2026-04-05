#!/usr/bin/env python3
"""
Fix script to add report saving to AID command
"""
import re


def fix_aid_save_report():
    aid_file = "C:/_Python/_Projects/__csf.wip/commands/ANL/aid/aid.py"

    with open(aid_file, encoding="utf-8") as f:
        content = f.read()

    # Find the line where Claude's analysis results are printed
    search_pattern = r'(\s+print\(f"\{result\[\'analysis_results\'\]\}"\))\n(\s+# Also show DGATE delegation option)'

    replacement = r"""\1

            # Save Claude's analysis to a report file
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{target}_{analysis_type}_claude_report_{timestamp}.md"
            report_path = Path.cwd() / report_filename

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# Claude Analysis Report\\n\\n")
                f.write(f"**Target:** {target}\\n")
                f.write(f"**Analysis Type:** {analysis_type}\\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                f.write(f"**AI-Distiller Source:** {result['output_file']}\\n\\n")
                f.write(f"---\\n\\n")
                f.write(result['analysis_results'])

            print(f"\\n📄 Claude analysis saved to: {report_path}")

\2"""

    new_content = re.sub(search_pattern, replacement, content)

    if new_content != content:
        with open(aid_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ AID command fixed to save Claude analysis reports")
        return True
    else:
        print("❌ Pattern not found - file may have changed")
        return False


if __name__ == "__main__":
    fix_aid_save_report()
